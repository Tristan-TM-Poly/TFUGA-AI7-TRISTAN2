from __future__ import annotations

from hashlib import sha256
import html
import json
import math
from typing import Any, Mapping


class FigureBackendError(ValueError):
    pass


def _finite(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number): raise FigureBackendError("non-finite figure coordinate")
    return number


def _svg_header(width: int, height: int) -> list[str]:
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">']


def render_svg(spec: Mapping[str, Any], *, width: int = 800, height: int = 500) -> str:
    if width < 100 or height < 100: raise FigureBackendError("SVG canvas must be at least 100x100")
    kind = str(spec.get("kind", "")); lines = _svg_header(width, height)
    caption = html.escape(str(spec.get("caption", "")))
    if caption: lines.append(f"<title>{caption}</title>")
    margin = 50.0
    if kind == "graph":
        nodes = list(spec.get("nodes", ())); ids = {str(n.get("id", "")): n for n in nodes if isinstance(n, Mapping)}
        coords: dict[str, tuple[float,float]] = {}
        for node_id, node in ids.items():
            x = margin + _finite(node.get("x", 0)) * 80.0; y = height - margin - _finite(node.get("y", 0)) * 80.0
            coords[node_id] = (x,y)
        for edge in spec.get("edges", ()):
            if not isinstance(edge, Mapping): continue
            source = str(edge.get("source", "")); target = str(edge.get("target", ""))
            if source not in coords or target not in coords: raise FigureBackendError("edge references unknown graph node")
            x1,y1=coords[source]; x2,y2=coords[target]
            lines.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="currentColor"/>')
        for node_id,node in ids.items():
            x,y=coords[node_id]; label=html.escape(str(node.get("label", node_id)))
            lines.append(f'<circle cx="{x:g}" cy="{y:g}" r="8" fill="none" stroke="currentColor"/>')
            lines.append(f'<text x="{x+12:g}" y="{y+4:g}" font-size="14">{label}</text>')
    elif kind == "plot":
        series = [s for s in spec.get("series", ()) if isinstance(s, Mapping)]
        points = [(float(x),float(y)) for s in series for x,y in zip(s.get("x",()),s.get("y",()))]
        if not points: raise FigureBackendError("plot has no points")
        for x,y in points: _finite(x); _finite(y)
        xs=[p[0] for p in points]; ys=[p[1] for p in points]
        xmin,xmax=min(xs),max(xs); ymin,ymax=min(ys),max(ys)
        if math.isclose(xmin,xmax): xmax=xmin+1.0
        if math.isclose(ymin,ymax): ymax=ymin+1.0
        def sx(x): return margin+(x-xmin)/(xmax-xmin)*(width-2*margin)
        def sy(y): return height-margin-(y-ymin)/(ymax-ymin)*(height-2*margin)
        lines.append(f'<line x1="{margin:g}" y1="{height-margin:g}" x2="{width-margin:g}" y2="{height-margin:g}" stroke="currentColor"/>')
        lines.append(f'<line x1="{margin:g}" y1="{margin:g}" x2="{margin:g}" y2="{height-margin:g}" stroke="currentColor"/>')
        for item in series:
            coords=[(sx(float(x)),sy(float(y))) for x,y in zip(item.get("x",()),item.get("y",()))]
            mode=str(item.get("mode","line"))
            if mode in {"line","line+markers"}:
                points_attr=" ".join(f"{x:g},{y:g}" for x,y in coords)
                lines.append(f'<polyline points="{points_attr}" fill="none" stroke="currentColor"/>')
            if mode in {"scatter","line+markers"}:
                for x,y in coords: lines.append(f'<circle cx="{x:g}" cy="{y:g}" r="3"/>')
    else:
        raise FigureBackendError(f"unsupported figure kind {kind!r}")
    lines.append("</svg>")
    return "\n".join(lines)+"\n"


def svg_receipt(spec: Mapping[str, Any], svg: str) -> dict[str, Any]:
    spec_raw=json.dumps(dict(spec),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return {"backend":"svg-stdlib","spec_sha256":sha256(spec_raw).hexdigest(),"artifact_sha256":sha256(svg.encode("utf-8")).hexdigest(),"boundary":"rendered artifact receipt validates deterministic rendering identity only; it does not validate source data or interpretation"}


def figure_backend_manifest(doc: Any) -> dict[str, Any]:
    figures=[]
    for node in getattr(doc,"nodes",()):
        spec=getattr(node,"figure_ir",{}) or {}
        if not spec: continue
        try:
            svg=render_svg(spec); receipt=svg_receipt(spec,svg); findings=[]
        except (FigureBackendError,TypeError,ValueError) as exc:
            receipt={}; findings=[{"code":"FIGURE_SVG_INVALID","severity":"error","message":str(exc)}]
        figures.append({"node_id":str(getattr(node,"id","")),"svg_receipt":receipt,"findings":findings})
    return {"semantic_hash":getattr(doc,"semantic_hash",lambda:"")(),"figures":figures,"boundary":"backend validation is rendering validation, not scientific data validation"}
