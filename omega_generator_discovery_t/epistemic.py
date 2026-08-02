"""Epistemic dynamics over theory/evidence counts."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class EpistemicTransition:
    concept_delta: float
    evidence_delta: float
    proof_growth_ratio: float | None
    classification: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evidence_growth_transition(
    *,
    concepts_before: float,
    concepts_after: float,
    evidence_before: float,
    evidence_after: float,
) -> EpistemicTransition:
    values = (concepts_before, concepts_after, evidence_before, evidence_after)
    if any(value < 0 for value in values):
        raise ValueError("Counts must be non-negative")
    concept_delta = concepts_after-concepts_before
    evidence_delta = evidence_after-evidence_before
    if concept_delta > 0:
        ratio = evidence_delta/concept_delta
    elif evidence_delta > 0:
        ratio = float("inf")
    else:
        ratio = None
    if evidence_delta < 0:
        classification = "evidence_regression"
    elif concept_delta > 0 and evidence_delta <= 0:
        classification = "concept_expansion_without_new_evidence"
    elif ratio is not None and ratio < 0.5:
        classification = "evidence_lag"
    elif ratio is not None and ratio >= 1.0:
        classification = "crystallizing"
    else:
        classification = "balanced_or_stable"
    return EpistemicTransition(concept_delta, evidence_delta, ratio, classification)
