from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

TRACKED_METRICS = ("code_files", "tests", "workflows", "documents", "schemas")


def _load_payload(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    path = Path(value)
    return json.loads(path.read_text(encoding="utf-8"))


def _system_index(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(node["path"]): dict(node)
        for node in payload.get("nodes", [])
        if node.get("kind") == "system" and node.get("path")
    }


def _relations(payload: Mapping[str, Any]) -> set[tuple[str, str, str]]:
    id_to_path = {
        str(node.get("id")): str(node.get("path", node.get("id")))
        for node in payload.get("nodes", [])
    }
    out: set[tuple[str, str, str]] = set()
    for edge in payload.get("edges", []):
        relation = str(edge.get("relation", ""))
        if relation == "CONTAINS" or not relation:
            continue
        source = id_to_path.get(str(edge.get("source")), str(edge.get("source")))
        target = id_to_path.get(str(edge.get("target")), str(edge.get("target")))
        out.add((source, relation, target))
    return out


def delta_summaries(
    previous: str | Path | Mapping[str, Any],
    current: str | Path | Mapping[str, Any],
) -> dict[str, Any]:
    """Compare two summary snapshots without promoting semantic claims.

    The delta is repository-state evidence only. It does not infer scientific
    progress, novelty, causal improvement, market traction or IP priority.
    """

    before = _load_payload(previous)
    after = _load_payload(current)
    before_systems = _system_index(before)
    after_systems = _system_index(after)

    before_names = set(before_systems)
    after_names = set(after_systems)
    added = sorted(after_names - before_names)
    removed = sorted(before_names - after_names)

    status_changes = []
    metric_changes = []
    for system in sorted(before_names & after_names):
        left = before_systems[system]
        right = after_systems[system]
        if left.get("status") != right.get("status"):
            status_changes.append(
                {
                    "system": system,
                    "from": left.get("status"),
                    "to": right.get("status"),
                }
            )
        left_metrics = left.get("metrics", {})
        right_metrics = right.get("metrics", {})
        changes = {}
        for metric in TRACKED_METRICS:
            old = int(left_metrics.get(metric, 0) or 0)
            new = int(right_metrics.get(metric, 0) or 0)
            if old != new:
                changes[metric] = {"from": old, "to": new, "delta": new - old}
        if changes:
            metric_changes.append({"system": system, "changes": changes})

    before_relations = _relations(before)
    after_relations = _relations(after)
    relation_added = [
        {"source": source, "relation": relation, "target": target}
        for source, relation, target in sorted(after_relations - before_relations)
    ]
    relation_removed = [
        {"source": source, "relation": relation, "target": target}
        for source, relation, target in sorted(before_relations - after_relations)
    ]

    return {
        "schema_version": "1.0.0",
        "previous_fingerprint": before.get("cache_fingerprint", ""),
        "current_fingerprint": after.get("cache_fingerprint", ""),
        "root": after.get("root") or before.get("root"),
        "added_systems": added,
        "removed_systems": removed,
        "status_changes": status_changes,
        "metric_changes": metric_changes,
        "relations_added": relation_added,
        "relations_removed": relation_removed,
        "changed": bool(
            added
            or removed
            or status_changes
            or metric_changes
            or relation_added
            or relation_removed
        ),
        "boundary": "repository-state delta only; not scientific progress, novelty, causal improvement, market traction or IP priority",
    }


def render_delta_markdown(delta: Mapping[str, Any]) -> str:
    lines = [
        f"# ΔSUMMARY — {delta.get('root', '')}",
        "",
        f"- précédent : `{delta.get('previous_fingerprint', '')}`",
        f"- courant : `{delta.get('current_fingerprint', '')}`",
        f"- changement structurel détecté : **{bool(delta.get('changed'))}**",
        "",
        "## Systèmes ajoutés",
        "",
    ]
    lines += [f"- `+ {system}`" for system in delta.get("added_systems", [])] or ["_Aucun._"]
    lines += ["", "## Systèmes retirés", ""]
    lines += [f"- `- {system}`" for system in delta.get("removed_systems", [])] or ["_Aucun._"]
    lines += ["", "## Changements de statut", ""]
    lines += [
        f"- `{item['system']}` : {item['from']} → **{item['to']}**"
        for item in delta.get("status_changes", [])
    ] or ["_Aucun._"]
    lines += ["", "## Changements métriques", ""]
    if delta.get("metric_changes"):
        for item in delta["metric_changes"]:
            details = ", ".join(
                f"{metric} {change['from']}→{change['to']} ({change['delta']:+d})"
                for metric, change in sorted(item["changes"].items())
            )
            lines.append(f"- `{item['system']}` — {details}")
    else:
        lines.append("_Aucun._")
    lines += ["", "## Relations ajoutées", ""]
    lines += [
        f"- `{item['source']}` —`{item['relation']}`→ `{item['target']}`"
        for item in delta.get("relations_added", [])
    ] or ["_Aucune._"]
    lines += ["", "## Relations retirées", ""]
    lines += [
        f"- `{item['source']}` —`{item['relation']}`→ `{item['target']}`"
        for item in delta.get("relations_removed", [])
    ] or ["_Aucune._"]
    lines += [
        "",
        "## OAK boundary",
        "",
        str(delta.get("boundary", "")),
        "",
    ]
    return "\n".join(lines)


def write_delta(
    previous: str | Path | Mapping[str, Any],
    current: str | Path | Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    delta = delta_summaries(previous, current)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "DELTA_SUMMARY.json"
    markdown_path = out / "DELTA_SUMMARY.md"
    json_path.write_text(
        json.dumps(delta, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_delta_markdown(delta), encoding="utf-8")
    return {"delta_json": json_path, "delta_markdown": markdown_path}
