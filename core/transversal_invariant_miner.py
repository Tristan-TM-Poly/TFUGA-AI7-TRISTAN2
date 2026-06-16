#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Transversal Invariant Miner (TIM)

TIM mines candidate cross-domain invariants from accumulated HGFM/OAK reports.

Inputs
------
- reports/hgfm/science_domain_hgfm_report.json
- reports/science_oak/science_oak_benchmark_report.json
- reports/hgfm/hgfm_m_minus_compact.json

Outputs
-------
- reports/transversal/transversal_invariants.json
- reports/transversal/TRANSVERSAL_INVARIANTS.md
- reports/transversal/transversal_m_minus.json

OAK guard
---------
TIM does not claim that domains share a real law. It emits candidates, risks, and
next OAK tests. A candidate becomes CANON only after a micro-oracle or later real
benchmark validates the proposed invariant.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import argparse
import json
import math
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCIENCE_HGFM = ROOT / "reports" / "hgfm" / "science_domain_hgfm_report.json"
SCIENCE_OAK = ROOT / "reports" / "science_oak" / "science_oak_benchmark_report.json"
GENERAL_M_MINUS = ROOT / "reports" / "hgfm" / "hgfm_m_minus_compact.json"
OUT_DIR = ROOT / "reports" / "transversal"
OUT_JSON = OUT_DIR / "transversal_invariants.json"
OUT_MD = OUT_DIR / "TRANSVERSAL_INVARIANTS.md"
OUT_M_MINUS = OUT_DIR / "transversal_m_minus.json"

FEATURE_KEYS = [
    "fractal_ratio",
    "ffwt_energy_entropy",
    "ffwt_mean_adjacent_coherence",
    "ffwt_dominant_level",
    "ffwt_dominant_relative_energy",
    "null_z_score",
    "null_percentile",
]


@dataclass(frozen=True)
class CandidateInvariant:
    id: str
    status: str
    score: float
    domains: List[str]
    families: List[str]
    shared_features: List[str]
    evidence: Dict[str, Any]
    risks: List[str]
    oak_next_test: str


def stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc), "_path": str(path)}


def sf(x: Any, default: float = 0.0) -> float:
    try:
        y = float(x)
        if math.isfinite(y):
            return y
        return default
    except Exception:
        return default


def verdict_score(verdict: str) -> float:
    return {"CANON": 1.0, "FERTILE": 0.60, "M_MINUS": 0.0}.get(verdict, 0.25)


def feature_vector(node: Dict[str, Any]) -> np.ndarray:
    inv = node.get("invariants", {}) or {}
    return np.asarray([sf(inv.get(k, 0.0)) for k in FEATURE_KEYS], dtype=float)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.clip(float(np.dot(a, b)) / denom, -1.0, 1.0))


def top_shared_features(left: Dict[str, Any], right: Dict[str, Any], k: int = 4) -> List[str]:
    a = left.get("invariants", {}) or {}
    b = right.get("invariants", {}) or {}
    scored: List[Tuple[float, str]] = []
    for key in FEATURE_KEYS:
        av = sf(a.get(key, 0.0))
        bv = sf(b.get(key, 0.0))
        magnitude = min(abs(av), abs(bv))
        closeness = 1.0 / (1.0 + abs(av - bv))
        scored.append((magnitude * closeness, key))
    return [key for _, key in sorted(scored, reverse=True)[:k]]


def oak_benchmark_index(report: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    if not report:
        return index
    for item in report.get("results", []):
        family = str(item.get("family", "unknown"))
        bucket = index.setdefault(family, {"count": 0, "canon": 0, "fertile": 0, "m_minus": 0, "scores": []})
        bucket["count"] += 1
        verdict = str(item.get("verdict", "UNKNOWN"))
        if verdict == "CANON":
            bucket["canon"] += 1
        elif verdict == "FERTILE":
            bucket["fertile"] += 1
        elif verdict == "M_MINUS":
            bucket["m_minus"] += 1
        bucket["scores"].append(sf(item.get("oak_score", 0.0)))
    for bucket in index.values():
        bucket["mean_score"] = float(np.mean(bucket["scores"])) if bucket["scores"] else 0.0
    return index


def support_score(families: List[str], oak_index: Dict[str, Dict[str, Any]]) -> float:
    if not families:
        return 0.0
    vals = []
    for family in families:
        bucket = oak_index.get(family)
        if not bucket:
            vals.append(0.35)
        else:
            vals.append(sf(bucket.get("mean_score", 0.0)) / 100.0)
    return float(np.mean(vals))


def status_from_score(score: float, has_m_minus: bool) -> str:
    if has_m_minus:
        return "M_MINUS"
    if score >= 0.84:
        return "CANON_CANDIDATE"
    if score >= 0.62:
        return "FERTILE"
    return "M_MINUS"


def next_test_for(features: List[str], domains: List[str]) -> str:
    feature_text = ", ".join(features[:3]) if features else "selected CVCD features"
    domain_text = " vs ".join(domains[:3])
    return (
        f"Generate paired perturbation benchmarks for {domain_text}; preserve the proposed shared features ({feature_text}) while varying noise, scale, and phase. "
        "Accept only if similarity remains stable and parameter micro-oracles stay CANON/FERTILE."
    )


def mine_pair_candidates(science_hgfm: Optional[Dict[str, Any]], oak_index: Dict[str, Dict[str, Any]], threshold: float) -> List[CandidateInvariant]:
    if not science_hgfm:
        return []
    nodes = science_hgfm.get("nodes", [])
    candidates: List[CandidateInvariant] = []
    for i, left in enumerate(nodes):
        for right in nodes[i + 1:]:
            if left.get("family") == right.get("family"):
                continue
            sim = cosine(feature_vector(left), feature_vector(right))
            if sim < threshold:
                continue
            domains = [str(left.get("domain", left.get("id", "left"))), str(right.get("domain", right.get("id", "right")))]
            families = sorted({str(left.get("family", "unknown")), str(right.get("family", "unknown"))})
            features = top_shared_features(left, right)
            oak_support = support_score(families, oak_index)
            verdicts = [str(left.get("verdict", "UNKNOWN")), str(right.get("verdict", "UNKNOWN"))]
            has_m_minus = "M_MINUS" in verdicts
            score = float(np.clip(0.65 * sim + 0.35 * oak_support, 0.0, 1.0))
            status = status_from_score(score, has_m_minus)
            risks = [
                "synthetic tensors are proxies, not empirical data",
                "flattening may create artificial similarity",
            ]
            if not all(f in oak_index for f in families):
                risks.append("one or more families lack micro-oracle support")
            if has_m_minus:
                risks.append("one paired domain is already M_MINUS in science HGFM")
            candidate_id = "tim:" + "+".join(domains)
            candidates.append(CandidateInvariant(
                id=candidate_id,
                status=status,
                score=score,
                domains=domains,
                families=families,
                shared_features=features,
                evidence={
                    "cvcd_similarity": sim,
                    "oak_support": oak_support,
                    "left_verdict": verdicts[0],
                    "right_verdict": verdicts[1],
                },
                risks=risks,
                oak_next_test=next_test_for(features, domains),
            ))
    return sorted(candidates, key=lambda x: x.score, reverse=True)


def cluster_by_feature(candidates: List[CandidateInvariant], limit: int = 12) -> List[Dict[str, Any]]:
    buckets: Dict[str, Dict[str, Any]] = {}
    for cand in candidates:
        for feature in cand.shared_features[:2]:
            b = buckets.setdefault(feature, {"feature": feature, "domains": set(), "candidate_ids": [], "max_score": 0.0})
            b["domains"].update(cand.domains)
            b["candidate_ids"].append(cand.id)
            b["max_score"] = max(float(b["max_score"]), cand.score)
    rows = []
    for item in buckets.values():
        rows.append({
            "feature": item["feature"],
            "domains": sorted(item["domains"]),
            "candidate_ids": item["candidate_ids"][:20],
            "max_score": item["max_score"],
            "status": "FERTILE" if len(item["domains"]) >= 3 else "LOCAL",
        })
    return sorted(rows, key=lambda x: (len(x["domains"]), x["max_score"]), reverse=True)[:limit]


def compact_m_minus(candidates: List[CandidateInvariant], general_m_minus: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    failed = [cand for cand in candidates if cand.status == "M_MINUS"]
    return {
        "created_at": stamp(),
        "candidate_count": len(failed),
        "candidates": [asdict(cand) for cand in failed[:50]],
        "general_m_minus_count": int((general_m_minus or {}).get("count", 0)) if isinstance(general_m_minus, dict) else 0,
    }


def write_markdown(report: Dict[str, Any]) -> None:
    lines = ["# Transversal Invariant Miner Report", ""]
    lines.append(f"Generated: `{report['created_at']}`")
    lines.append("")
    summary = report["summary"]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Candidates: **{summary['candidate_count']}**")
    lines.append(f"- Clusters: **{summary['cluster_count']}**")
    lines.append(f"- Status counts: `{json.dumps(summary['status_counts'], ensure_ascii=False, sort_keys=True)}`")
    lines.append("")
    lines.append("## Top candidates")
    lines.append("")
    for cand in report["candidates"][:10]:
        lines.append(f"- **{cand['status']}** `{cand['id']}` score={cand['score']:.4f}; domains={', '.join(cand['domains'])}; features={', '.join(cand['shared_features'])}")
    lines.append("")
    lines.append("## Guard")
    lines.append("")
    lines.append("TIM emits hypotheses and proposed OAK tests only. A transversal invariant is not a proven scientific law until micro-oracles or empirical benchmarks validate it.")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def summarize(candidates: List[CandidateInvariant], clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for cand in candidates:
        counts[cand.status] = counts.get(cand.status, 0) + 1
    return {
        "candidate_count": len(candidates),
        "cluster_count": len(clusters),
        "status_counts": counts,
        "top_score": max([cand.score for cand in candidates], default=0.0),
    }


def main(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Mine transversal invariant candidates from science HGFM/OAK reports")
    parser.add_argument("--threshold", type=float, default=0.88)
    parser.add_argument("--max-candidates", type=int, default=80)
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    science_hgfm = read_json(SCIENCE_HGFM)
    science_oak = read_json(SCIENCE_OAK)
    general_m_minus = read_json(GENERAL_M_MINUS)
    oak_index = oak_benchmark_index(science_oak)
    candidates = mine_pair_candidates(science_hgfm, oak_index, threshold=float(args.threshold))[: int(args.max_candidates)]
    clusters = cluster_by_feature(candidates)
    report = {
        "system": "TTM Transversal Invariant Miner",
        "created_at": stamp(),
        "input_reports": [str(p.relative_to(ROOT)) for p in [SCIENCE_HGFM, SCIENCE_OAK, GENERAL_M_MINUS]],
        "threshold": float(args.threshold),
        "summary": summarize(candidates, clusters),
        "clusters": clusters,
        "candidates": [asdict(cand) for cand in candidates],
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    OUT_M_MINUS.write_text(json.dumps(compact_m_minus(candidates, general_m_minus), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    write_markdown(report)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
