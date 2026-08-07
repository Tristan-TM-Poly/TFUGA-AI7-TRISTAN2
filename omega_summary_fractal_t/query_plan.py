from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

from .query import query_payload

SUPPORTED_OPS = {"eq", "ne", "gt", "gte", "lt", "lte", "contains", "in", "exists"}
SUPPORTED_AGGREGATES = {"count", "sum", "mean", "min", "max"}


def _load(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _field(row: Mapping[str, Any], path: str) -> Any:
    current: Any = row
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _match_condition(row: Mapping[str, Any], condition: Mapping[str, Any]) -> bool:
    field = str(condition.get("field", ""))
    op = str(condition.get("op", "eq")).casefold()
    if op not in SUPPORTED_OPS:
        raise ValueError(f"unsupported query-plan operator: {op}")
    actual = _field(row, field)
    expected = condition.get("value")
    if op == "exists":
        return (actual is not None) is bool(expected if expected is not None else True)
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "contains":
        if actual is None:
            return False
        if isinstance(actual, (list, tuple, set)):
            return expected in actual
        return str(expected).casefold() in str(actual).casefold()
    if op == "in":
        if not isinstance(expected, (list, tuple, set)):
            raise ValueError("'in' expects a list/tuple/set value")
        return actual in expected
    if actual is None:
        return False
    try:
        left = float(actual)
        right = float(expected)
    except (TypeError, ValueError):
        left = str(actual)
        right = str(expected)
    if op == "gt":
        return left > right
    if op == "gte":
        return left >= right
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    return False


def _matches(row: Mapping[str, Any], plan: Mapping[str, Any]) -> bool:
    where = plan.get("where", []) or []
    any_of = plan.get("any", []) or []
    none_of = plan.get("not", []) or []
    if not all(_match_condition(row, condition) for condition in where):
        return False
    if any_of and not any(_match_condition(row, condition) for condition in any_of):
        return False
    if any(_match_condition(row, condition) for condition in none_of):
        return False
    return True


def _aggregate(rows: list[Mapping[str, Any]], spec: Mapping[str, Any]) -> Any:
    op = str(spec.get("op", "count")).casefold()
    if op not in SUPPORTED_AGGREGATES:
        raise ValueError(f"unsupported aggregate: {op}")
    if op == "count":
        return len(rows)
    field = str(spec.get("field", ""))
    values = [_field(row, field) for row in rows]
    values = [value for value in values if value is not None]
    if not values:
        return None
    numeric: list[float] = []
    for value in values:
        try:
            numeric.append(float(value))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"aggregate {op} requires numeric field: {field}") from exc
    if op == "sum":
        return round(sum(numeric), 6)
    if op == "mean":
        return round(mean(numeric), 6)
    if op == "min":
        return min(numeric)
    if op == "max":
        return max(numeric)
    raise AssertionError(op)


def _sort_rows(rows: list[dict[str, Any]], sort_spec: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = list(rows)
    for spec in reversed(sort_spec):
        field = str(spec.get("field", ""))
        reverse = str(spec.get("direction", "asc")).casefold() == "desc"
        result.sort(
            key=lambda row: (
                _field(row, field) is None,
                _field(row, field),
            ),
            reverse=reverse,
        )
    return result


def execute_query_plan(
    source: str | Path | Mapping[str, Any],
    plan: str | Path | Mapping[str, Any],
) -> dict[str, Any]:
    """Execute a bounded declarative query plan over structural summary rows."""

    plan_payload = _load(plan)
    seed = dict(plan_payload.get("seed", {}))
    allowed_seed = {
        "text",
        "kind",
        "status",
        "relation",
        "repository",
        "min_crystallization",
        "max_crystallization",
    }
    unknown_seed = set(seed) - allowed_seed
    if unknown_seed:
        raise ValueError(f"unsupported seed fields: {sorted(unknown_seed)}")
    base = query_payload(source, limit=1_000_000, **seed)
    rows = [dict(row) for row in base.get("results", []) if _matches(row, plan_payload)]

    group_by = plan_payload.get("group_by", []) or []
    if isinstance(group_by, str):
        group_by = [group_by]
    aggregates = plan_payload.get("aggregates", []) or []
    if not aggregates:
        aggregates = [
            {"name": "count", "op": "count"},
            {"name": "mean_crystallization", "op": "mean", "field": "structural_crystallization"},
        ]

    groups: list[dict[str, Any]] = []
    if group_by:
        buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            buckets[tuple(_field(row, field) for field in group_by)].append(row)
        for key, bucket in buckets.items():
            record = {field: value for field, value in zip(group_by, key)}
            for spec in aggregates:
                name = str(spec.get("name") or f"{spec.get('op','count')}_{spec.get('field','rows')}")
                record[name] = _aggregate(bucket, spec)
            groups.append(record)
        groups = _sort_rows(groups, list(plan_payload.get("sort", []) or []))
    else:
        rows = _sort_rows(rows, list(plan_payload.get("sort", []) or []))

    limit = max(0, int(plan_payload.get("limit", 100)))
    total_matches = len(rows)
    if group_by:
        total_groups = len(groups)
        groups = groups[:limit]
    else:
        total_groups = 0
        rows = rows[:limit]

    return {
        "schema_version": "1.0.0",
        "source_kind": base.get("source_kind", "unknown"),
        "plan": plan_payload,
        "total_matches": total_matches,
        "total_groups": total_groups,
        "rows": [] if group_by else rows,
        "groups": groups if group_by else [],
        "boundary": "query-plan filters and aggregates operate only on observed structural metadata; compositions do not create scientific, causal, legal, IP or commercial authority",
    }


def render_query_plan_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Ω-SUMMARY QUERY PLAN",
        "",
        f"- source : `{report.get('source_kind', '')}`",
        f"- lignes correspondantes : **{report.get('total_matches', 0)}**",
        f"- groupes : **{report.get('total_groups', 0)}**",
        "",
    ]
    groups = list(report.get("groups", []))
    rows = list(report.get("rows", []))
    if groups:
        keys = sorted({key for item in groups for key in item})
        lines += ["| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
        for item in groups:
            lines.append("| " + " | ".join(str(item.get(key, "")) for key in keys) + " |")
    elif rows:
        lines += [
            "| Repository | Objet | Type | Statut | C_struct |",
            "|---|---|---|---|---:|",
        ]
        for item in rows:
            c = item.get("structural_crystallization")
            c_text = "—" if c is None else f"{float(c):.3f}"
            lines.append(
                f"| `{item.get('repository','')}` | `{item.get('path','')}` | {item.get('kind','')} | {item.get('status','')} | {c_text} |"
            )
    else:
        lines.append("_Aucun résultat._")
    lines += ["", "## OAK boundary", "", str(report.get("boundary", "")), ""]
    return "\n".join(lines)


def write_query_plan(report: Mapping[str, Any], output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "QUERY_PLAN_RESULTS.json"
    markdown_path = out / "QUERY_PLAN_RESULTS.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_query_plan_markdown(report), encoding="utf-8")
    return {"query_plan_json": json_path, "query_plan_markdown": markdown_path}
