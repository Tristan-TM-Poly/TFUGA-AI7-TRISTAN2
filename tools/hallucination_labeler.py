"""Hallucination labeler for Tristan AIT systems.

Labels generated content as vision, metaphor, hypothesis, prototype, measured
result, proof, or quarantined. This is an OAK-safe classification helper, not a
truth oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ClaimStatus(StrEnum):
    VISION = "vision"
    METAPHOR = "metaphor"
    HYPOTHESIS = "hypothesis"
    PROTOTYPE = "prototype"
    MEASURED = "measured_result"
    PROOF = "proof"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class ClaimLabel:
    status: ClaimStatus
    confidence: float
    reasons: tuple[str, ...]
    oak_required_next: tuple[str, ...]


UNSAFE_BOUNDARY_TERMS = {
    "dose",
    "extraction",
    "potentiate",
    "mixing protocol",
    "bypass safety",
    "hide evidence",
    "delete logs",
    "steal",
}

PROOFY_TERMS = {
    "proves",
    "guaranteed",
    "certain",
    "absolute truth",
    "undeniable",
    "zero risk",
}

METAPHOR_TERMS = {
    "like",
    "as if",
    "metaphor",
    "analogy",
    "symbolic",
}


def _hits(text: str, terms: set[str]) -> tuple[str, ...]:
    normalized = text.lower()
    return tuple(term for term in terms if term in normalized)


def label_claim(
    text: str,
    *,
    has_reality_anchor: bool = False,
    has_test: bool = False,
    has_implementation: bool = False,
    has_measurement: bool = False,
    independently_reproduced: bool = False,
) -> ClaimLabel:
    """Classify a generated claim with conservative OAK semantics."""

    boundary_hits = _hits(text, UNSAFE_BOUNDARY_TERMS)
    proofy_hits = _hits(text, PROOFY_TERMS)
    metaphor_hits = _hits(text, METAPHOR_TERMS)
    reasons: list[str] = []
    next_steps: list[str] = []

    if boundary_hits:
        return ClaimLabel(
            status=ClaimStatus.QUARANTINED,
            confidence=0.95,
            reasons=("unsafe_boundary_terms", *boundary_hits),
            oak_required_next=("quarantine", "remove_or_refuse_unsafe_content", "no_external_execution"),
        )

    if proofy_hits and not independently_reproduced:
        reasons.append("overclaim_language_detected")
        next_steps.append("downgrade_claim_strength")

    if independently_reproduced and has_measurement and has_test:
        return ClaimLabel(
            status=ClaimStatus.PROOF,
            confidence=0.85,
            reasons=tuple(reasons + ["reproduced_measured_tested"]),
            oak_required_next=tuple(next_steps + ["document_scope_and_limits"]),
        )

    if has_measurement and has_test:
        return ClaimLabel(
            status=ClaimStatus.MEASURED,
            confidence=0.75,
            reasons=tuple(reasons + ["measured_and_tested"]),
            oak_required_next=tuple(next_steps + ["seek_reproduction", "document_uncertainty"]),
        )

    if has_implementation and has_test:
        return ClaimLabel(
            status=ClaimStatus.PROTOTYPE,
            confidence=0.70,
            reasons=tuple(reasons + ["implemented_and_tested"]),
            oak_required_next=tuple(next_steps + ["benchmark", "measure", "add_m_minus"]),
        )

    if has_reality_anchor and has_test:
        return ClaimLabel(
            status=ClaimStatus.HYPOTHESIS,
            confidence=0.65,
            reasons=tuple(reasons + ["anchored_and_testable"]),
            oak_required_next=tuple(next_steps + ["implement_minimal_test", "falsify"]),
        )

    if metaphor_hits or has_reality_anchor:
        return ClaimLabel(
            status=ClaimStatus.METAPHOR,
            confidence=0.60,
            reasons=tuple(reasons + ["metaphor_or_partial_anchor"]),
            oak_required_next=tuple(next_steps + ["add_test", "separate_metaphor_from_mechanism"]),
        )

    return ClaimLabel(
        status=ClaimStatus.VISION,
        confidence=0.55,
        reasons=tuple(reasons + ["unanchored_generation"]),
        oak_required_next=tuple(next_steps + ["add_reality_anchor", "classify_risk", "no_execution"]),
    )
