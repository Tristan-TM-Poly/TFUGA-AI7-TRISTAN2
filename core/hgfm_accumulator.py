#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: HGFM Accumulator

Transforms accumulated JKD/OAK reports into a compact Hypergraph Fractal
Mycelial Map (HGFM):

- nodes: axes / benchmarks / verdicts / invariant signatures
- edges: similarity, shared verdict, shared failure mode
- reports: JSON + Markdown under reports/hgfm/
- memory: compact M_MINUS view for rejected or unstable axes

Design locks
------------
- stdlib + numpy only
- no network calls
- no external writes outside reports/hgfm/
- deterministic from existing reports
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import argparse
import json
import math
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OMNI_REPORT = ROOT / "reports" / "jkd" / "omni_harvester_report.json"
JKD_REPORT = ROOT / "reports" / "jkd" / "jkd_tensor_inputs_report.json"
OAK_REPORT = ROOT / "omega_max_oak_report.json"
OUT_DIR = ROOT / "reports" / "hgfm"
OUT_JSON = OUT_DIR / "hgfm_accumulator_report.json"
OUT_MD = OUT_DIR / "HGFM_ACCUMULATOR_REPORT.md"
OUT_M_MINUS = OUT_DIR / "hgfm_m_minus_compact.json"

INVARIANT_KEYS = [
    "fractal_ratio",
    "ffwt_energy_entropy",
    "ffwt_mean_adjacent_coherence",
    "ffwt_dominant_level",
    "ffwt_dominant_relative_energy",
    "null_z_score",
    "null_percentile",
]


@dataclass(frozen=True)
class HGFMNode:
    id: str
    kind: str
    label: str
    verdict: str
    source: str
    invariants: Dict[str, float]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class HGFMEdge:
    source: str
    target: str
    kind: str
    weight: float
    evidence: Dict[str, Any]


def utc_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc), "_path": str(path)}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        x = float(value)
        if math.isfinite(x):
            return x
        return default
    except Exception:
        return default


def vector_from_invariants(invariants: Dict[str, Any]) -> np.ndarray:
    return np.asarray([safe_float(invariants.get(key, 0.0)) for key in INVARIANT_KEYS], dtype=float)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.clip(np.dot(a, b) / denom, -1.0, 1.0))


def verdict_score(verdict: str) -> float:
    return {"CANON": 1.0, "FERTILE": 0.55, "M_MINUS": 0.0}.get(verdict, 0.25)


def extract_invariants(strike: Dict[str, Any]) -> Dict[str, float]:
    selected = strike.get("selected_invariants", {}) if isinstance(strike, dict) else {}
    signatures = strike.get("signatures_cvcd", {}) if isinstance(strike, dict) else {}
    control = strike.get("permutation_control", {}) if isinstance(strike, dict) else {}
    merged = {**signatures, **selected, **control}
    return {key: safe_float(merged.get(key, 0.0)) for key in INVARIANT_KEYS}


def load_omni_nodes() -> List[HGFMNode]:
    report = read_json(OMNI_REPORT)
    nodes: List[HGFMNode] = []
    if not report:
        return nodes
    runs = report.get("runs", [])
    for run_index, run in enumerate(runs[-12:]):
        timestamp = str(run.get("timestamp", f"run_{run_index}"))
        for axis, payload in run.get("axes", {}).items():
            strike = payload.get("strike", {})
            verdict = str(strike.get("verdict", "UNKNOWN"))
            nodes.append(HGFMNode(
                id=f"omni:{timestamp}:{axis}",
                kind="omni_axis",
                label=axis,
                verdict=verdict,
                source=str(payload.get("source", "unknown")),
                invariants=extract_invariants(strike),
                metadata={
                    "timestamp": timestamp,
                    "oak_score": strike.get("oak_score"),
                    "metadata": payload.get("metadata", {}),
                    "flattened_size": strike.get("flattened_size"),
                },
            ))
    return nodes


def load_jkd_tensor_nodes() -> List[HGFMNode]:
    report = read_json(JKD_REPORT)
    nodes: List[HGFMNode] = []
    if not report:
        return nodes
    for name, result in report.get("results", {}).items():
        nodes.append(HGFMNode(
            id=f"jkd_tensor:{name}",
            kind="jkd_tensor_input",
            label=name,
            verdict=str(result.get("verdict", "UNKNOWN")),
            source="reports/jkd/jkd_tensor_inputs_report.json",
            invariants=extract_invariants({"selected_invariants": result.get("selected_signatures", {}), "permutation_control": result.get("permutation_control", {})}),
            metadata={"oak_score": result.get("oak_score"), "shape": result.get("shape")},
        ))
    return nodes


def load_oak_benchmark_nodes() -> List[HGFMNode]:
    report = read_json(OAK_REPORT)
    nodes: List[HGFMNode] = []
    if not report:
        return nodes
    for item in report.get("results", []):
        errors = item.get("errors", {}) or {}
        invariants = {
            "fractal_ratio": 0.0,
            "ffwt_energy_entropy": 0.0,
            "ffwt_mean_adjacent_coherence": 0.0,
            "ffwt_dominant_level": 0.0,
            "ffwt_dominant_relative_energy": max(0.0, 1.0 - float(np.mean([safe_float(v, 1.0) for v in errors.values()])) if errors else 0.0),
            "null_z_score": safe_float(item.get("oak_score", 0.0)) / 100.0,
            "null_percentile": verdict_score(str(item.get("verdict", "UNKNOWN"))),
        }
        name = str(item.get("benchmark", "unknown"))
        nodes.append(HGFMNode(
            id=f"oak:{name}",
            kind="oak_benchmark",
            label=name,
            verdict=str(item.get("verdict", "UNKNOWN")),
            source="omega_max_oak_report.json",
            invariants=invariants,
            metadata={
                "oak_score": item.get("oak_score"),
                "relation_type": item.get("relation_type"),
                "errors": errors,
            },
        ))
    return nodes


def build_edges(nodes: List[HGFMNode], threshold: float = 0.82) -> List[HGFMEdge]:
    edges: List[HGFMEdge] = []
    vectors = {node.id: vector_from_invariants(node.invariants) for node in nodes}
    for i, left in enumerate(nodes):
        for right in nodes[i + 1:]:
            sim = cosine_similarity(vectors[left.id], vectors[right.id])
            if sim >= threshold:
                edges.append(HGFMEdge(
                    source=left.id,
                    target=right.id,
                    kind="cvcd_similarity",
                    weight=sim,
                    evidence={"threshold": threshold, "left_label": left.label, "right_label": right.label},
                ))
            if left.verdict == right.verdict and left.verdict in {"CANON", "M_MINUS"}:
                edges.append(HGFMEdge(
                    source=left.id,
                    target=right.id,
                    kind=f"shared_verdict:{left.verdict}",
                    weight=verdict_score(left.verdict),
                    evidence={"verdict": left.verdict},
                ))
    return edges


def summarize(nodes: List[HGFMNode], edges: List[HGFMEdge]) -> Dict[str, Any]:
    verdicts: Dict[str, int] = {}
    kinds: Dict[str, int] = {}
    for node in nodes:
        verdicts[node.verdict] = verdicts.get(node.verdict, 0) + 1
        kinds[node.kind] = kinds.get(node.kind, 0) + 1
    top_edges = sorted(edges, key=lambda edge: edge.weight, reverse=True)[:20]
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "verdicts": verdicts,
        "kinds": kinds,
        "top_edges": [asdict(edge) for edge in top_edges],
    }


def compact_m_minus(nodes: List[HGFMNode], edges: List[HGFMEdge]) -> Dict[str, Any]:
    m_nodes = [node for node in nodes if node.verdict == "M_MINUS"]
    incident = []
    m_ids = {node.id for node in m_nodes}
    for edge in edges:
        if edge.source in m_ids or edge.target in m_ids:
            incident.append(asdict(edge))
    return {
        "created_at": utc_stamp(),
        "count": len(m_nodes),
        "nodes": [asdict(node) for node in m_nodes],
        "incident_edges": incident[:50],
    }


def write_markdown(report: Dict[str, Any]) -> None:
    lines = ["# HGFM Accumulator Report", ""]
    lines.append(f"Generated: `{report['created_at']}`")
    lines.append("")
    summary = report["summary"]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Nodes: **{summary['node_count']}**")
    lines.append(f"- Edges: **{summary['edge_count']}**")
    lines.append(f"- Verdicts: `{json.dumps(summary['verdicts'], ensure_ascii=False, sort_keys=True)}`")
    lines.append(f"- Kinds: `{json.dumps(summary['kinds'], ensure_ascii=False, sort_keys=True)}`")
    lines.append("")
    lines.append("## Top edges")
    lines.append("")
    for edge in summary["top_edges"][:10]:
        lines.append(f"- `{edge['kind']}` `{edge['source']}` -> `{edge['target']}` weight={edge['weight']:.4f}")
    lines.append("")
    lines.append("## OAK guard")
    lines.append("")
    lines.append("This report is an internal accumulator. It does not publish, deploy, or claim scientific proof. It maps candidate invariants and failure memories for later OAK validation.")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Build HGFM map from OAK/JKD accumulation reports")
    parser.add_argument("--threshold", type=float, default=0.82, help="cosine similarity threshold for CVCD edges")
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    nodes = load_omni_nodes() + load_jkd_tensor_nodes() + load_oak_benchmark_nodes()
    edges = build_edges(nodes, threshold=float(args.threshold))
    report = {
        "system": "TTM HGFM Accumulator",
        "created_at": utc_stamp(),
        "input_reports": [str(path.relative_to(ROOT)) for path in [OMNI_REPORT, JKD_REPORT, OAK_REPORT]],
        "invariant_keys": INVARIANT_KEYS,
        "summary": summarize(nodes, edges),
        "nodes": [asdict(node) for node in nodes],
        "edges": [asdict(edge) for edge in edges],
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    OUT_M_MINUS.write_text(json.dumps(compact_m_minus(nodes, edges), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    write_markdown(report)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
