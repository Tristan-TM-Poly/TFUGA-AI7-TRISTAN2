from __future__ import annotations

from hashlib import sha256
import json
import math
import re
from typing import Any, Mapping

from .ast import Text
from .models import DocumentIR, NodeKind


class FigureIRError(ValueError):
    pass


_SAFE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")


def _finite(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise FigureIRError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise FigureIRError(f"{field} must be finite")
    return number


def _safe_id(value: Any, field: str) -> str:
    text = str(value)
    if not _SAFE_ID.fullmatch(text):
        raise FigureIRError(f"{field} contains unsupported identifier {text!r}")
    return text


def _label_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9:.-]+", "-", value).strip("-")
    return safe or "figure"


def validate_figure_ir(spec: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    findings: list[dict[str, Any]] = []
    kind = str(spec.get("kind", ""))
    try:
        if kind == "graph":
            nodes = list(spec.get("nodes", ())); edges = list(spec.get("edges", ())); ids: set[str] = set()
            for index, node in enumerate(nodes):
                if not isinstance(node, Mapping): raise FigureIRError(f"graph node {index} must be an object")
                node_id = _safe_id(node.get("id", ""), f"nodes[{index}].id")
                if node_id in ids: raise FigureIRError(f"duplicate graph node id {node_id!r}")
                ids.add(node_id); _finite(node.get("x", 0), f"nodes[{index}].x"); _finite(node.get("y", 0), f"nodes[{index}].y")
            for index, edge in enumerate(edges):
                if not isinstance(edge, Mapping): raise FigureIRError(f"graph edge {index} must be an object")
                source = _safe_id(edge.get("source", ""), f"edges[{index}].source"); target = _safe_id(edge.get("target", ""), f"edges[{index}].target")
                if source not in ids or target not in ids: raise FigureIRError(f"edge {index} references unknown endpoint")
        elif kind == "plot":
            series = list(spec.get("series", ()))
            if not series: raise FigureIRError("plot requires at least one series")
            for index, item in enumerate(series):
                if not isinstance(item, Mapping): raise FigureIRError(f"series[{index}] must be an object")
                xs = list(item.get("x", ())); ys = list(item.get("y", ()))
                if len(xs) != len(ys) or not xs: raise FigureIRError(f"series[{index}] x/y arrays must be non-empty and equal-length")
                for j, value in enumerate(xs): _finite(value, f"series[{index}].x[{j}]")
                for j, value in enumerate(ys): _finite(value, f"series[{index}].y[{j}]")
                mode = str(item.get("mode", "line"))
                if mode not in {"line", "scatter", "line+markers"}: raise FigureIRError(f"series[{index}] unsupported mode {mode!r}")
        else:
            raise FigureIRError(f"unsupported figure kind {kind!r}")
    except FigureIRError as exc:
        findings.append({"code": "FIGURE_IR_INVALID", "severity": "error", "message": str(exc)})
    return tuple(findings)


def render_figure_ir(spec: Mapping[str, Any], *, node_id: str = "figure", title: str = "") -> str:
    findings = validate_figure_ir(spec); errors = [item for item in findings if item["severity"] == "error"]
    if errors: raise FigureIRError(errors[0]["message"])
    caption = str(spec.get("caption", title or node_id)); label = _label_id(str(spec.get("label", node_id))); kind = str(spec["kind"])
    lines = [r"\begin{figure}[htbp]", r"\centering"]
    if kind == "graph":
        lines.append(r"\begin{tikzpicture}[>=stealth]")
        for node in spec.get("nodes", ()):
            node_id_safe = _safe_id(node["id"], "node.id"); x = _finite(node.get("x", 0), "node.x"); y = _finite(node.get("y", 0), "node.y"); label_text = Text(str(node.get("label", node_id_safe))).render()
            lines.append(rf"\node ({node_id_safe}) at ({x:g},{y:g}) {{{label_text}}};")
        for edge in spec.get("edges", ()):
            source = _safe_id(edge["source"], "edge.source"); target = _safe_id(edge["target"], "edge.target"); directed = edge.get("directed", True) is not False; command = r"\draw[->]" if directed else r"\draw"; edge_label = str(edge.get("label", "")).strip()
            if edge_label: lines.append(rf"{command} ({source}) -- node[midway,above] {{{Text(edge_label).render()}}} ({target});")
            else: lines.append(rf"{command} ({source}) -- ({target});")
        lines.append(r"\end{tikzpicture}")
    else:
        x_label = Text(str(spec.get("x_label", "x"))).render(); y_label = Text(str(spec.get("y_label", "y"))).render()
        lines += [r"\begin{tikzpicture}", rf"\begin{{axis}}[xlabel={{{x_label}}},ylabel={{{y_label}}},grid=major]"]
        for item in spec.get("series", ()):
            coords = " ".join(f"({_finite(x, 'x'):g},{_finite(y, 'y'):g})" for x, y in zip(item.get("x", ()), item.get("y", ())))
            option = {"line": "", "scatter": "only marks", "line+markers": "mark=*"}[str(item.get("mode", "line"))]; option_text = f"[{option}]" if option else ""
            lines.append(rf"\addplot{option_text} coordinates {{{coords}}};")
            if str(item.get("name", "")).strip(): lines.append(rf"\addlegendentry{{{Text(str(item['name'])).render()}}}")
        lines += [r"\end{axis}", r"\end{tikzpicture}"]
    lines += [rf"\caption{{{Text(caption).render()}}}", rf"\label{{fig:{label}}}", r"\end{figure}"]
    return "\n".join(lines)


def figure_manifest(doc: DocumentIR) -> dict[str, Any]:
    entries = []
    for node in doc.nodes:
        if node.kind != NodeKind.FIGURE: continue
        spec = node.figure_ir; findings = list(validate_figure_ir(spec)) if spec else [{"code": "FIGURE_IR_MISSING", "severity": "warning", "message": "figure node has no figure_ir"}]
        raw = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        entries.append({"node_id": node.id, "kind": str(spec.get("kind", "")) if spec else "", "figure_ir_sha256": sha256(raw).hexdigest(), "findings": findings, "renderable": bool(spec) and not any(x["severity"] == "error" for x in findings)})
    return {"semantic_hash": doc.semantic_hash(), "figures": entries, "boundary": "FigureIR validates rendering structure only; rendered figures do not validate underlying data or scientific interpretation"}
