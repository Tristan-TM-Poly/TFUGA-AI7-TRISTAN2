"""OAK gates and compatibility checks for candidate family cells."""
from __future__ import annotations

from .models import FamilyCoordinate
from .vocabularies import INCOMPATIBILITY_RULES


def contradictions_for(coordinate: FamilyCoordinate) -> tuple[str, ...]:
    values = {
        coordinate.skeleton,
        coordinate.functional_family,
        coordinate.electronic_class,
        coordinate.reaction_archetype,
        coordinate.stereo_class,
    }
    contradictions: list[str] = []
    for left, right, reason in INCOMPATIBILITY_RULES:
        if left in values and right in values:
            contradictions.append(reason)
    return tuple(sorted(set(contradictions)))


def compatibility_score(coordinate: FamilyCoordinate) -> float:
    contradictions = contradictions_for(coordinate)
    score = max(0.0, 1.0 - 0.25 * len(contradictions))
    if coordinate.functional_family == "multifunctional_mixed":
        score -= 0.05
    if coordinate.electronic_class == "radical_or_open_shell":
        score -= 0.10
    return round(max(0.0, score), 3)


def oak_gate_for_identification(*, independent_modalities: int, contradictions: int, reference_match: bool) -> str:
    if reference_match and independent_modalities >= 2 and contradictions == 0:
        return "reference_confirmed"
    if independent_modalities >= 2 and contradictions == 0:
        return "multimodal_evidence"
    if independent_modalities >= 1 and contradictions == 0:
        return "structurally_compatible"
    return "candidate_cell_unvalidated"
