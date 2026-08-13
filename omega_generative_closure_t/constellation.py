from __future__ import annotations
from collections import Counter
from itertools import combinations
from typing import Any
from .core import RepoCellDecision


def _caps(repo: dict[str, Any]) -> set[str]:
    return {str(x) for x in repo.get("capabilities", [])}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def analyze_constellation(payload: dict[str, Any], *, materialization_threshold: float = 0.72, compression_overlap_threshold: float = 0.75) -> tuple[RepoCellDecision, ...]:
    repos = list(payload.get("repositories", []))
    counts: Counter[str] = Counter()
    for repo in repos:
        counts.update(_caps(repo))
    overlap: dict[str, tuple[float, str | None]] = {str(r["name"]): (0.0, None) for r in repos}
    for left, right in combinations(repos, 2):
        score = _jaccard(_caps(left), _caps(right))
        left_name, right_name = str(left["name"]), str(right["name"])
        if score > overlap[left_name][0]:
            overlap[left_name] = (score, right_name)
        if score > overlap[right_name][0]:
            overlap[right_name] = (score, left_name)
    owner = str(payload.get("owner", ""))
    decisions = []
    for repo in repos:
        name = str(repo["name"])
        split = float(repo.get("split_score", 0.0))
        unique = tuple(sorted(c for c in _caps(repo) if counts[c] == 1))
        max_overlap, other = overlap[name]
        reasons = []
        if split < materialization_threshold:
            decision = "HOLD"
            reasons.append("split_score_below_materialization_threshold")
        elif max_overlap >= compression_overlap_threshold and not unique:
            decision = "COMPRESS"
            reasons.append("high_capability_overlap_without_unique_capability")
        else:
            decision = "KEEP"
            if unique:
                reasons.append("owns_unique_capabilities")
            reasons.append("split_score_supports_independent_cell")
            if max_overlap < compression_overlap_threshold:
                reasons.append("no_high_overlap_compression_trigger")
        decisions.append(RepoCellDecision(
            repository=f"{owner}/{name}" if owner else name,
            decision=decision,
            unique_capabilities=unique,
            max_overlap=round(max_overlap, 6),
            overlap_with=other,
            split_score=split,
            reasons=tuple(reasons),
        ))
    return tuple(decisions)


def summarize_decisions(decisions: tuple[RepoCellDecision, ...]) -> dict[str, Any]:
    counts = Counter(d.decision for d in decisions)
    return {
        "schema_version": "omega-generative-closure/constellation-court/v0.1",
        "counts": dict(sorted(counts.items())),
        "decisions": [
            {
                "repository": d.repository,
                "decision": d.decision,
                "unique_capabilities": list(d.unique_capabilities),
                "max_overlap": d.max_overlap,
                "overlap_with": d.overlap_with,
                "split_score": d.split_score,
                "reasons": list(d.reasons),
            }
            for d in decisions
        ],
    }
