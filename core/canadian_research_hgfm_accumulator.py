#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Canadian Research HGFM Accumulator

Builds an internal HGFM map from the Canadian University Research Harvester.

Input
-----
- reports/canada_research/canadian_university_research_report.json

Outputs
-------
- reports/hgfm/canadian_research_hgfm_report.json
- reports/hgfm/CANADIAN_RESEARCH_HGFM_REPORT.md
- reports/hgfm/canadian_research_m_minus_compact.json

Guard
-----
This is metadata-level triage only. It is not a university ranking, not a claim of
best-in-world research, and not an evaluation of individual researchers.
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
CANADA_REPORT = ROOT / "reports" / "canada_research" / "canadian_university_research_report.json"
OUT_DIR = ROOT / "reports" / "hgfm"
OUT_JSON = OUT_DIR / "canadian_research_hgfm_report.json"
OUT_MD = OUT_DIR / "CANADIAN_RESEARCH_HGFM_REPORT.md"
OUT_M_MINUS = OUT_DIR / "canadian_research_m_minus_compact.json"

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
class CanadaResearchNode:
    id: str
    name: str
    province: str
    region: str
    priority: str
    source: str
    verdict: str
    oak_score: float
    invariants: Dict[str, float]
    topics: List[str]
    works: List[Dict[str, Any]]


@dataclass(frozen=True)
class CanadaResearchEdge:
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


def sf(x: Any, default: float = 0.0) -> float:
    try:
        y = float(x)
        return y if math.isfinite(y) else default
    except Exception:
        return default


def vector(node: CanadaResearchNode) -> np.ndarray:
    return np.asarray([sf(node.invariants.get(key, 0.0)) for key in KEYS], dtype=float)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.clip(np.dot(a, b) / denom, -1.0, 1.0))


def extract_topics(works: List[Dict[str, Any]]) -> List[str]:
    topics = []
    for work in works:
        topic = work.get("topic")
        if topic:
            topics.append(str(topic))
    return sorted(set(topics))


def load_nodes(report: Optional[Dict[str, Any]]) -> List[CanadaResearchNode]:
    if not report:
        return []
    runs = report.get("runs", [])
    if not runs and "last_run" in report:
        runs = [report["last_run"]]
    if not runs:
        return []
    latest = runs[-1]
    nodes: List[CanadaResearchNode] = []
    for name, payload in latest.get("institutions", {}).items():
        seed = payload.get("seed", {})
        strike = payload.get("strike", {})
        inv = strike.get("selected_invariants", {}) or {}
        works = payload.get("works", []) or []
        safe_name = name.replace(" ", "_").replace("'", "").replace("é", "e")
        nodes.append(CanadaResearchNode(
            id=f"canada_research:{safe_name}",
            name=str(name),
            province=str(seed.get("province", "unknown")),
            region=str(seed.get("region", "unknown")),
            priority=str(seed.get("priority", "unknown")),
            source=str(payload.get("source", "unknown")),
            verdict=str(strike.get("verdict", "UNKNOWN")),
            oak_score=sf(strike.get("oak_score", 0.0)),
            invariants={k: sf(inv.get(k, 0.0)) for k in KEYS},
            topics=extract_topics(works),
            works=works[:10],
        ))
    return nodes


def topic_overlap(left: CanadaResearchNode, right: CanadaResearchNode) -> float:
    a = set(left.topics)
    b = set(right.topics)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def build_edges(nodes: List[CanadaResearchNode], threshold: float) -> List[CanadaResearchEdge]:
    edges: List[CanadaResearchEdge] = []
    vectors = {node.id: vector(node) for node in nodes}
    for i, left in enumerate(nodes):
        for right in nodes[i + 1:]:
            sim = cosine(vectors[left.id], vectors[right.id])
            if sim >= threshold:
                edges.append(CanadaResearchEdge(left.id, right.id, "canada_cvcd_similarity", sim, {"left": left.name, "right": right.name}))
            if left.province == right.province:
                edges.append(CanadaResearchEdge(left.id, right.id, "same_province", 0.5, {"province": left.province}))
            overlap = topic_overlap(left, right)
            if overlap > 0.0:
                edges.append(CanadaResearchEdge(left.id, right.id, "topic_overlap", overlap, {"shared_topics": sorted(set(left.topics) & set(right.topics))[:10]}))
            if left.verdict == right.verdict and left.verdict in {"CANON", "M_MINUS"}:
                edges.append(CanadaResearchEdge(left.id, right.id, f"shared_verdict:{left.verdict}", 1.0 if left.verdict == "CANON" else 0.0, {"verdict": left.verdict}))
    return edges


def summarize(nodes: List[CanadaResearchNode], edges: List[CanadaResearchEdge]) -> Dict[str, Any]:
    provinces: Dict[str, int] = {}
    verdicts: Dict[str, int] = {}
    sources: Dict[str, int] = {}
    for node in nodes:
        provinces[node.province] = provinces.get(node.province, 0) + 1
        verdicts[node.verdict] = verdicts.get(node.verdict, 0) + 1
        sources[node.source] = sources.get(node.source, 0) + 1
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "provinces": provinces,
        "verdicts": verdicts,
        "sources": sources,
        "top_edges": [asdict(edge) for edge in sorted(edges, key=lambda edge: edge.weight, reverse=True)[:20]],
    }


def write_markdown(report: Dict[str, Any]) -> None:
    summary = report["summary"]
    lines = ["# Canadian Research HGFM Report", ""]
    lines.append(f"Generated: `{report['created_at']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Institutions: **{summary['node_count']}**")
    lines.append(f"- Edges: **{summary['edge_count']}**")
    lines.append(f"- Provinces: `{json.dumps(summary['provinces'], ensure_ascii=False, sort_keys=True)}`")
    lines.append(f"- Verdicts: `{json.dumps(summary['verdicts'], ensure_ascii=False, sort_keys=True)}`")
    lines.append(f"- Sources: `{json.dumps(summary['sources'], ensure_ascii=False, sort_keys=True)}`")
    lines.append("")
    lines.append("## Guard")
    lines.append("")
    lines.append("This is metadata-level research triage. It is not a university ranking, not a complete capture of Canadian research, and not an evaluation of individual researchers.")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Build Canadian/Quebec research HGFM from harvested metadata")
    parser.add_argument("--threshold", type=float, default=0.84)
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    nodes = load_nodes(read_json(CANADA_REPORT))
    edges = build_edges(nodes, float(args.threshold))
    report = {
        "system": "TTM Canadian Research HGFM",
        "created_at": stamp(),
        "input_report": str(CANADA_REPORT.relative_to(ROOT)),
        "invariant_keys": KEYS,
        "summary": summarize(nodes, edges),
        "nodes": [asdict(node) for node in nodes],
        "edges": [asdict(edge) for edge in edges],
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    m_nodes = [node for node in nodes if node.verdict == "M_MINUS"]
    OUT_M_MINUS.write_text(json.dumps({"created_at": stamp(), "count": len(m_nodes), "nodes": [asdict(node) for node in m_nodes]}, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    write_markdown(report)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
