from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _load_payload(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _crystallization(metrics: Mapping[str, Any]) -> float:
    components = (
        bool(metrics.get("documented") or int(metrics.get("documents", 0) or 0)),
        bool(metrics.get("implemented") or int(metrics.get("code_files", 0) or 0)),
        bool(metrics.get("tested") or int(metrics.get("tests", 0) or 0)),
        bool(int(metrics.get("workflows", 0) or 0)),
        bool(metrics.get("schema_backed") or int(metrics.get("schemas", 0) or 0)),
    )
    return round(sum(int(value) for value in components) / len(components), 4)


def _rows_from_repository(payload: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    id_to_path = {
        str(node.get("id")): str(node.get("path", node.get("id", "")))
        for node in payload.get("nodes", [])
    }
    relations = []
    for edge in payload.get("edges", []):
        relation = str(edge.get("relation", ""))
        if not relation:
            continue
        relations.append(
            {
                "source": id_to_path.get(str(edge.get("source")), str(edge.get("source", ""))),
                "relation": relation,
                "target": id_to_path.get(str(edge.get("target")), str(edge.get("target", ""))),
            }
        )
    rows = []
    for node in payload.get("nodes", []):
        metrics = dict(node.get("metrics", {}))
        rows.append(
            {
                "repository": str(payload.get("root", "")),
                "path": str(node.get("path", "")),
                "kind": str(node.get("kind", "")),
                "title": str(node.get("title", "")),
                "one_line": str(node.get("one_line", "")),
                "status": str(node.get("status", "observed")),
                "metrics": metrics,
                "structural_crystallization": _crystallization(metrics) if node.get("kind") == "system" else None,
            }
        )
    return rows, relations


def _rows_from_corpus(payload: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = []
    for repository in payload.get("repositories", []):
        if not repository.get("available"):
            continue
        repo_name = str(repository.get("name", ""))
        for system in repository.get("systems", []):
            metrics = dict(system.get("metrics", {}))
            rows.append(
                {
                    "repository": repo_name,
                    "path": str(system.get("path", "")),
                    "kind": "system",
                    "title": str(system.get("title", "")),
                    "one_line": str(system.get("one_line", "")),
                    "status": str(system.get("status", "observed")),
                    "metrics": metrics,
                    "structural_crystallization": _crystallization(metrics),
                }
            )
    relations = [
        {
            "source": str(item.get("source", "")),
            "relation": str(item.get("relation", "")),
            "target": str(item.get("target", "")),
        }
        for item in payload.get("cross_repo_links", [])
    ]
    return rows, relations


def _rows_from_index(payload: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    runs = payload.get("runs", [])
    if not runs:
        return [], []
    snapshot = runs[-1].get("snapshot", {})
    rows = []
    for entity, profile in snapshot.get("entities", {}).items():
        repository, separator, path = str(entity).partition("::")
        rows.append(
            {
                "repository": repository if separator else str(snapshot.get("root", "")),
                "path": path if separator else str(entity),
                "kind": "system",
                "title": path if separator else str(entity),
                "one_line": "",
                "status": str(profile.get("status", "observed")),
                "metrics": dict(profile),
                "structural_crystallization": float(profile.get("structural_crystallization", 0.0)),
            }
        )
    relations = [dict(item) for item in snapshot.get("relations", [])]
    return rows, relations


def query_payload(
    source: str | Path | Mapping[str, Any],
    *,
    text: str | None = None,
    kind: str | None = None,
    status: str | None = None,
    relation: str | None = None,
    repository: str | None = None,
    min_crystallization: float | None = None,
    max_crystallization: float | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    payload = _load_payload(source)
    if isinstance(payload.get("repositories"), list):
        rows, relations = _rows_from_corpus(payload)
        source_kind = "corpus"
    elif isinstance(payload.get("runs"), list):
        rows, relations = _rows_from_index(payload)
        source_kind = "index"
    else:
        rows, relations = _rows_from_repository(payload)
        source_kind = "repository"

    relation_paths: set[str] | None = None
    if relation:
        wanted = relation.casefold()
        relation_paths = set()
        for item in relations:
            if str(item.get("relation", "")).casefold() == wanted:
                relation_paths.add(str(item.get("source", "")))
                relation_paths.add(str(item.get("target", "")))

    needle = text.casefold() if text else None
    repo_needle = repository.casefold() if repository else None
    results = []
    for row in rows:
        if kind and row["kind"].casefold() != kind.casefold():
            continue
        if status and row["status"].casefold() != status.casefold():
            continue
        if repo_needle and repo_needle not in row["repository"].casefold():
            continue
        if needle:
            haystack = " ".join((row["path"], row["title"], row["one_line"], row["repository"])).casefold()
            if needle not in haystack:
                continue
        if relation_paths is not None and row["path"] not in relation_paths and f"{row['repository']}::{row['path']}" not in relation_paths:
            continue
        crystallization = row.get("structural_crystallization")
        if min_crystallization is not None and (crystallization is None or float(crystallization) < min_crystallization):
            continue
        if max_crystallization is not None and (crystallization is None or float(crystallization) > max_crystallization):
            continue
        results.append(row)

    results.sort(
        key=lambda item: (
            -float(item.get("structural_crystallization") or 0.0),
            item["repository"].casefold(),
            item["path"].casefold(),
        )
    )
    total = len(results)
    results = results[: max(0, limit)]
    return {
        "schema_version": "1.0.0",
        "source_kind": source_kind,
        "query": {
            "text": text,
            "kind": kind,
            "status": status,
            "relation": relation,
            "repository": repository,
            "min_crystallization": min_crystallization,
            "max_crystallization": max_crystallization,
            "limit": limit,
        },
        "total_matches": total,
        "returned": len(results),
        "results": results,
        "boundary": "query results are structural repository observations; ranking by crystallization is not ranking by scientific truth, novelty, safety, market value or IP quality",
    }


def render_query_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Ω-SUMMARY QUERY",
        "",
        f"- source : `{report.get('source_kind', '')}`",
        f"- correspondances : **{report.get('total_matches', 0)}**",
        f"- retournées : **{report.get('returned', 0)}**",
        "",
        "| Repository | Objet | Type | Statut | C_struct | Résumé |",
        "|---|---|---|---|---:|---|",
    ]
    for item in report.get("results", []):
        crystallization = item.get("structural_crystallization")
        c_text = "—" if crystallization is None else f"{float(crystallization):.2f}"
        summary = str(item.get("one_line", "")).replace("|", "\\|")
        lines.append(
            f"| `{item.get('repository', '')}` | `{item.get('path', '')}` | {item.get('kind', '')} | "
            f"{item.get('status', '')} | {c_text} | {summary} |"
        )
    if not report.get("results"):
        lines.append("| — | — | — | — | — | aucune correspondance |")
    lines += ["", "## OAK boundary", "", str(report.get("boundary", "")), ""]
    return "\n".join(lines)


def write_query(report: Mapping[str, Any], output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "QUERY_RESULTS.json"
    markdown_path = out / "QUERY_RESULTS.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_query_markdown(report), encoding="utf-8")
    return {"query_json": json_path, "query_markdown": markdown_path}
