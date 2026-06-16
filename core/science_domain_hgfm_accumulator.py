#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Science Domain HGFM Accumulator

Builds an HGFM map specifically from reports/jkd/science_domain_omni_report.json.

Outputs
-------
- reports/hgfm/science_domain_hgfm_report.json
- reports/hgfm/SCIENCE_DOMAIN_HGFM_REPORT.md
- reports/hgfm/science_domain_m_minus_compact.json

This is an internal map of synthetic domain tensors, not empirical validation of
any scientific field.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import json
import math
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCIENCE_REPORT = ROOT / "reports" / "jkd" / "science_domain_omni_report.json"
OUT_DIR = ROOT / "reports" / "hgfm"
OUT_JSON = OUT_DIR / "science_domain_hgfm_report.json"
OUT_MD = OUT_DIR / "SCIENCE_DOMAIN_HGFM_REPORT.md"
OUT_M_MINUS = OUT_DIR / "science_domain_m_minus_compact.json"

KEYS = [
    "fractal_ratio",
    "ffwt_energy_entropy",
    "ffwt_mean_adjacent_coherence",
    "ffwt_dominant_level",
    "ffwt_dominant_relative_energy",
    "null_z_score",
    "null_percentile",
]


@dataclass(frozen=True)
class ScienceNode:
    id: str
    family: str
    domain: str
    verdict: str
    oak_score: float
    invariants: Dict[str, float]


@dataclass(frozen=True)
class ScienceEdge:
    source: str
    target: str
    kind: str
    weight: float
    evidence: Dict[str, Any]


def stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc)}


def sf(x: Any) -> float:
    try:
        y = float(x)
        return y if math.isfinite(y) else 0.0
    except Exception:
        return 0.0


def vec(inv: Dict[str, float]) -> np.ndarray:
    return np.asarray([sf(inv.get(k, 0.0)) for k in KEYS], dtype=float)


def sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.clip(np.dot(a, b) / denom, -1.0, 1.0))


def load_nodes(report: Optional[Dict[str, Any]]) -> List[ScienceNode]:
    if not report:
        return []
    runs = report.get("runs", [])
    if not runs and "last_run" in report:
        runs = [report["last_run"]]
    if not runs:
        return []
    latest = runs[-1]
    nodes: List[ScienceNode] = []
    for name, payload in latest.get("domains", {}).items():
        strike = payload.get("strike", {})
        selected = strike.get("selected_invariants", {})
        nodes.append(ScienceNode(
            id=f"science:{name}",
            family=str(payload.get("family", "unknown")),
            domain=name,
            verdict=str(strike.get("verdict", "UNKNOWN")),
            oak_score=sf(strike.get("oak_score", 0.0)),
            invariants={k: sf(selected.get(k, 0.0)) for k in KEYS},
        ))
    return nodes


def build_edges(nodes: List[ScienceNode], threshold: float) -> List[ScienceEdge]:
    vectors = {node.id: vec(node.invariants) for node in nodes}
    edges: List[ScienceEdge] = []
    for i, left in enumerate(nodes):
        for right in nodes[i + 1:]:
            c = sim(vectors[left.id], vectors[right.id])
            if c >= threshold:
                edges.append(ScienceEdge(left.id, right.id, "science_cvcd_similarity", c, {"left": left.domain, "right": right.domain}))
            if left.family == right.family:
                edges.append(ScienceEdge(left.id, right.id, "same_science_family", 0.5, {"family": left.family}))
            if left.verdict == right.verdict and left.verdict in {"CANON", "M_MINUS"}:
                edges.append(ScienceEdge(left.id, right.id, f"shared_verdict:{left.verdict}", 1.0 if left.verdict == "CANON" else 0.0, {"verdict": left.verdict}))
    return edges


def summarize(nodes: List[ScienceNode], edges: List[ScienceEdge]) -> Dict[str, Any]:
    families: Dict[str, int] = {}
    verdicts: Dict[str, int] = {}
    for node in nodes:
        families[node.family] = families.get(node.family, 0) + 1
        verdicts[node.verdict] = verdicts.get(node.verdict, 0) + 1
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "families": families,
        "verdicts": verdicts,
        "top_edges": [asdict(e) for e in sorted(edges, key=lambda x: x.weight, reverse=True)[:20]],
    }


def write_markdown(report: Dict[str, Any]) -> None:
    lines = ["# Science Domain HGFM Report", ""]
    lines.append(f"Generated: `{report['created_at']}`")
    lines.append("")
    summary = report["summary"]
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- Domains: **{summary['node_count']}**")
    lines.append(f"- Edges: **{summary['edge_count']}**")
    lines.append(f"- Families: `{json.dumps(summary['families'], ensure_ascii=False, sort_keys=True)}`")
    lines.append(f"- Verdicts: `{json.dumps(summary['verdicts'], ensure_ascii=False, sort_keys=True)}`")
    lines.append("")
    lines.append("## Guard")
    lines.append("")
    lines.append("All tensors are offline synthetic proxies. This report maps candidate cross-domain invariants only; it does not validate claims in those sciences.")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Build science-domain HGFM from science-domain omni report")
    parser.add_argument("--threshold", type=float, default=0.82)
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    nodes = load_nodes(read_json(SCIENCE_REPORT))
    edges = build_edges(nodes, float(args.threshold))
    report = {
        "system": "TTM Science Domain HGFM",
        "created_at": stamp(),
        "input_report": str(SCIENCE_REPORT.relative_to(ROOT)),
        "invariant_keys": KEYS,
        "summary": summarize(nodes, edges),
        "nodes": [asdict(n) for n in nodes],
        "edges": [asdict(e) for e in edges],
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    m_nodes = [n for n in nodes if n.verdict == "M_MINUS"]
    OUT_M_MINUS.write_text(json.dumps({"created_at": stamp(), "count": len(m_nodes), "nodes": [asdict(n) for n in m_nodes]}, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    write_markdown(report)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
