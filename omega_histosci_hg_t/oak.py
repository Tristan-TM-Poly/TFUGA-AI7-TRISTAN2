"""OAK confidence scoring for historical claims.

Scores are prioritization aids. They are not replacements for expert
historiography, source criticism, or independent verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .models import EpistemicStatus, OAKAssessment, OAKEvidence


DEFAULT_WEIGHTS: Mapping[str, float] = {
    "source_quality": 0.28,
    "primary_source_proximity": 0.18,
    "independent_corroboration": 0.24,
    "reproducibility_or_coherence": 0.18,
    "unresolved_controversy": 0.12,
}


@dataclass(frozen=True, slots=True)
class OAKThresholds:
    established: float = 0.82
    probable: float = 0.66
    contested: float = 0.45
    uncertain: float = 0.0

    def __post_init__(self) -> None:
        if not (1.0 >= self.established > self.probable > self.contested > self.uncertain >= 0.0):
            raise ValueError("thresholds must be strictly descending")


def assess_evidence(
    evidence: OAKEvidence,
    *,
    weights: Mapping[str, float] = DEFAULT_WEIGHTS,
    thresholds: OAKThresholds = OAKThresholds(),
) -> OAKAssessment:
    required = set(DEFAULT_WEIGHTS)
    if set(weights) != required:
        raise ValueError(f"weights must contain exactly {sorted(required)}")
    if any(value < 0 for value in weights.values()):
        raise ValueError("weights cannot be negative")
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("weight total must be positive")

    positive = (
        weights["source_quality"] * evidence.source_quality
        + weights["primary_source_proximity"] * evidence.primary_source_proximity
        + weights["independent_corroboration"] * evidence.independent_corroboration
        + weights["reproducibility_or_coherence"] * evidence.reproducibility_or_coherence
    )
    penalty = weights["unresolved_controversy"] * evidence.unresolved_controversy
    score = max(0.0, min(1.0, (positive - penalty) / total))

    reasons: list[str] = []
    if evidence.source_count == 0:
        score = min(score, thresholds.contested - 0.01)
        reasons.append("no source is attached")
    elif evidence.source_count == 1:
        reasons.append("single-source assertion requires corroboration")
    if evidence.primary_source_proximity < 0.35:
        reasons.append("weak proximity to primary sources")
    if evidence.independent_corroboration < 0.35:
        reasons.append("limited independent corroboration")
    if evidence.unresolved_controversy > 0.6:
        reasons.append("substantial unresolved controversy")
    reasons.extend(evidence.notes)

    if score >= thresholds.established:
        status = EpistemicStatus.ESTABLISHED
    elif score >= thresholds.probable:
        status = EpistemicStatus.PROBABLE
    elif score >= thresholds.contested:
        status = EpistemicStatus.CONTESTED
    else:
        status = EpistemicStatus.UNCERTAIN

    return OAKAssessment(round(score, 6), status, tuple(reasons), software_validation_only=True)


def minimum_status_for_public_narrative(status: EpistemicStatus) -> bool:
    """Return whether a status is safe for unqualified narrative rendering."""
    return status in {EpistemicStatus.ESTABLISHED, EpistemicStatus.PROBABLE}
