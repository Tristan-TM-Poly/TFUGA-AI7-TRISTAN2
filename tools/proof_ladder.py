"""Proof Ladder classifier for Tristan AIT Reality Forge.

Classifies evidence from P0 no evidence to P10 robust standard. The ladder is a
conservative communication tool; it does not establish truth by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ProofLevel(IntEnum):
    P0_NO_EVIDENCE = 0
    P1_INTERNAL_COHERENCE = 1
    P2_EXAMPLE = 2
    P3_TOY_TEST = 3
    P4_BENCHMARK = 4
    P5_BASELINE_COMPARISON = 5
    P6_REPRODUCTION = 6
    P7_STRESS_TEST = 7
    P8_EXTERNAL_REVIEW = 8
    P9_CONTROLLED_REAL_USE = 9
    P10_ROBUST_STANDARD = 10


@dataclass(frozen=True)
class ProofAssessment:
    level: ProofLevel
    label: str
    reasons: tuple[str, ...]
    required_next: str


def assess_proof_level(
    *,
    internally_coherent: bool = False,
    has_example: bool = False,
    has_toy_test: bool = False,
    has_benchmark: bool = False,
    compared_to_baseline: bool = False,
    reproduced: bool = False,
    stress_tested: bool = False,
    externally_reviewed: bool = False,
    controlled_real_use: bool = False,
    robust_standard: bool = False,
) -> ProofAssessment:
    reasons: list[str] = []

    if robust_standard and controlled_real_use and externally_reviewed:
        level = ProofLevel.P10_ROBUST_STANDARD
        reasons.append("robust_standard_and_reviewed")
    elif controlled_real_use:
        level = ProofLevel.P9_CONTROLLED_REAL_USE
        reasons.append("controlled_real_use")
    elif externally_reviewed:
        level = ProofLevel.P8_EXTERNAL_REVIEW
        reasons.append("external_review")
    elif stress_tested:
        level = ProofLevel.P7_STRESS_TEST
        reasons.append("stress_tested")
    elif reproduced:
        level = ProofLevel.P6_REPRODUCTION
        reasons.append("reproduced")
    elif compared_to_baseline:
        level = ProofLevel.P5_BASELINE_COMPARISON
        reasons.append("baseline_comparison")
    elif has_benchmark:
        level = ProofLevel.P4_BENCHMARK
        reasons.append("benchmark")
    elif has_toy_test:
        level = ProofLevel.P3_TOY_TEST
        reasons.append("toy_test")
    elif has_example:
        level = ProofLevel.P2_EXAMPLE
        reasons.append("example")
    elif internally_coherent:
        level = ProofLevel.P1_INTERNAL_COHERENCE
        reasons.append("internal_coherence")
    else:
        level = ProofLevel.P0_NO_EVIDENCE
        reasons.append("no_evidence")

    label = {
        ProofLevel.P0_NO_EVIDENCE: "no evidence",
        ProofLevel.P1_INTERNAL_COHERENCE: "internally coherent only",
        ProofLevel.P2_EXAMPLE: "example exists",
        ProofLevel.P3_TOY_TEST: "toy test exists",
        ProofLevel.P4_BENCHMARK: "benchmark exists",
        ProofLevel.P5_BASELINE_COMPARISON: "compared to baseline",
        ProofLevel.P6_REPRODUCTION: "reproduced",
        ProofLevel.P7_STRESS_TEST: "stress tested",
        ProofLevel.P8_EXTERNAL_REVIEW: "externally reviewed",
        ProofLevel.P9_CONTROLLED_REAL_USE: "controlled real use",
        ProofLevel.P10_ROBUST_STANDARD: "robust standard",
    }[level]

    required_next = {
        ProofLevel.P0_NO_EVIDENCE: "add coherence argument or example",
        ProofLevel.P1_INTERNAL_COHERENCE: "add concrete example",
        ProofLevel.P2_EXAMPLE: "add toy test",
        ProofLevel.P3_TOY_TEST: "add benchmark",
        ProofLevel.P4_BENCHMARK: "compare to baseline",
        ProofLevel.P5_BASELINE_COMPARISON: "seek reproduction",
        ProofLevel.P6_REPRODUCTION: "stress test",
        ProofLevel.P7_STRESS_TEST: "external review",
        ProofLevel.P8_EXTERNAL_REVIEW: "controlled real use",
        ProofLevel.P9_CONTROLLED_REAL_USE: "standardize and maintain",
        ProofLevel.P10_ROBUST_STANDARD: "maintain scope and regression tests",
    }[level]

    return ProofAssessment(level, label, tuple(reasons), required_next)


def evidence_gap(current: ProofLevel, target: ProofLevel) -> int:
    return max(0, int(target) - int(current))
