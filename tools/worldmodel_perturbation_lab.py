"""World-model perturbation lab for Tristan AIT systems.

This module is a computational abstraction inspired by altered-state/world-model
research. It is not substance-use guidance, not medical advice, not dosing
advice, and not a protocol for psychoactive substances.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EntropyBand(StrEnum):
    LOW = "low_rigidity"
    MEDIUM = "medium_fertile"
    HIGH = "high_hallucination_risk"
    QUARANTINE = "quarantine_no_execution"


class InsightStatus(StrEnum):
    VISION = "vision"
    METAPHOR = "metaphor"
    HYPOTHESIS = "hypothesis"
    PROTOTYPE = "prototype"
    MEASURED = "measured_result"
    PROOF = "proof"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class RealityAnchor:
    definition: str
    example: str
    test: str
    limitation: str
    risk: str
    residue: str
    source_status: str = "unsourced_or_internal"

    @property
    def is_testable(self) -> bool:
        return bool(self.definition and self.example and self.test and self.limitation)


@dataclass(frozen=True)
class WorldModelPerturbation:
    seed: str
    entropy_band: EntropyBand
    personas: tuple[str, ...]
    candidate_insight: str
    status: InsightStatus
    anchor: RealityAnchor | None
    oak_warnings: tuple[str, ...]
    safe_next_action: str


RUNAWAY_TERMS = {
    "guaranteed",
    "absolute truth",
    "zero risk",
    "unlimited",
    "proof of everything",
    "no need to test",
}

AUTHORITY_CONFUSION_TERMS = {
    "entity told me",
    "the persona proved",
    "vision proves",
    "felt real therefore true",
}


def choose_entropy_band(divergence: float, *, has_anchor: bool, high_stakes: bool = False) -> EntropyBand:
    """Choose an entropy band from a 0..1 divergence value."""

    if high_stakes:
        return EntropyBand.QUARANTINE
    if divergence < 0.25:
        return EntropyBand.LOW
    if divergence < 0.70 and has_anchor:
        return EntropyBand.MEDIUM
    if divergence < 0.90:
        return EntropyBand.HIGH
    return EntropyBand.QUARANTINE


def detect_oak_warnings(text: str) -> tuple[str, ...]:
    normalized = text.lower()
    warnings: list[str] = []
    if any(term in normalized for term in RUNAWAY_TERMS):
        warnings.append("runaway_or_overconfidence_language")
    if any(term in normalized for term in AUTHORITY_CONFUSION_TERMS):
        warnings.append("persona_or_vision_confused_with_evidence")
    if "dose" in normalized or "extraction" in normalized or "mix" in normalized:
        warnings.append("substance_use_boundary_violation")
    return tuple(warnings)


def classify_insight(*, anchor: RealityAnchor | None, warnings: tuple[str, ...], entropy_band: EntropyBand) -> InsightStatus:
    if "substance_use_boundary_violation" in warnings or entropy_band == EntropyBand.QUARANTINE:
        return InsightStatus.QUARANTINED
    if not anchor:
        return InsightStatus.VISION
    if not anchor.is_testable:
        return InsightStatus.METAPHOR
    if entropy_band == EntropyBand.HIGH:
        return InsightStatus.HYPOTHESIS
    return InsightStatus.PROTOTYPE


def perturb_worldmodel(
    *,
    seed: str,
    candidate_insight: str,
    divergence: float,
    personas: tuple[str, ...] = ("OAK-Falsifier", "Builder", "RealityAnchor"),
    anchor: RealityAnchor | None = None,
    high_stakes: bool = False,
) -> WorldModelPerturbation:
    """Create an OAK-safe world-model perturbation packet."""

    warnings = detect_oak_warnings(seed + " " + candidate_insight)
    entropy = choose_entropy_band(divergence, has_anchor=anchor is not None, high_stakes=high_stakes)
    status = classify_insight(anchor=anchor, warnings=warnings, entropy_band=entropy)

    if status == InsightStatus.QUARANTINED:
        safe_next = "Keep in QuarantineGraph; analyze only; no external execution."
    elif status in {InsightStatus.VISION, InsightStatus.METAPHOR}:
        safe_next = "Add RealityAnchor before prototype or external action."
    elif status == InsightStatus.HYPOTHESIS:
        safe_next = "Run OAK falsification and add tests before implementation."
    else:
        safe_next = "Create reversible branch/draft PR with tests and M- notes."

    return WorldModelPerturbation(
        seed=seed,
        entropy_band=entropy,
        personas=personas,
        candidate_insight=candidate_insight,
        status=status,
        anchor=anchor,
        oak_warnings=warnings,
        safe_next_action=safe_next,
    )
