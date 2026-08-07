from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from xml.sax.saxutils import escape, quoteattr


def _load_payload(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return json.loads(Path(value).read_text(encoding="utf-8"))


def write_jsonl(payload: Mapping[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for node in payload.get("nodes", []):
        lines.append(json.dumps({"record_type": "node", **dict(node)}, sort_keys=True, ensure_ascii=False))
    for edge in payload.get("edges", []):
        lines.append(json.dumps({"record_type": "edge", **dict(edge)}, sort_keys=True, ensure_ascii=False))
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return target


def _data(key: str, value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        rendered = json.dumps(value, sort_keys=True, ensure_ascii=False)
    elif value is None:
        rendered = ""
    else:
        rendered = str(value)
    return f"<data key={quoteattr(key)}>{escape(rendered)}</data>"


def write_graphml(payload: Mapping[str, Any], path: str | Path) -> Path:
    """Write a dependency-free GraphML projection of a SummaryBundle payload."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '<key id="path" for="node" attr.name="path" attr.type="string"/>',
        '<key id="title" for="node" attr.name="title" attr.type="string"/>',
        '<key id="status" for="node" attr.name="status" attr.type="string"/>',
        '<key id="metrics" for="node" attr.name="metrics" attr.type="string"/>',
        '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '<graph id="summary" edgedefault="directed">',
    ]
    for node in payload.get("nodes", []):
        node_id = str(node.get("id", ""))
        lines.append(f"<node id={quoteattr(node_id)}>")
        lines.append(_data("kind", node.get("kind", "")))
        lines.append(_data("path", node.get("path", "")))
        lines.append(_data("title", node.get("title", "")))
        lines.append(_data("status", node.get("status", "")))
        lines.append(_data("metrics", node.get("metrics", {})))
        lines.append("</node>")
    for ordinal, edge in enumerate(payload.get("edges", []), start=1):
        source = str(edge.get("source", ""))
        target_id = str(edge.get("target", ""))
        lines.append(
            f"<edge id={quoteattr('e' + str(ordinal))} source={quoteattr(source)} target={quoteattr(target_id)}>"
        )
        lines.append(_data("relation", edge.get("relation", "")))
        lines.append("</edge>")
    lines += ["</graph>", "</graphml>"]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def write_graph_exports(
    summary: str | Path | Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    payload = _load_payload(summary)
    if "nodes" not in payload or "edges" not in payload:
        raise ValueError("graph export requires a repository SummaryBundle payload")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    jsonl = write_jsonl(payload, out / "SUMMARY_GRAPH.jsonl")
    graphml = write_graphml(payload, out / "SUMMARY_GRAPH.graphml")
    manifest = out / "SUMMARY_GRAPH_EXPORT.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "root": payload.get("root", ""),
                "fingerprint": payload.get("cache_fingerprint", ""),
                "node_count": len(payload.get("nodes", [])),
                "edge_count": len(payload.get("edges", [])),
                "artifacts": [jsonl.name, graphml.name],
                "boundary": "structural graph export only; relation presence does not establish scientific causality, novelty, ownership or validity",
            },
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"jsonl": jsonl, "graphml": graphml, "manifest": manifest}
