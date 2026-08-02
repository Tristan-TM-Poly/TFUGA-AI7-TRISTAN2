"""OAK-safe validation and compact contradiction bitsets for R0.2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

RULES = (
    ("saturated_sigma", "alkene_alkyne", "saturation_conflicts_with_explicit_pi_family"),
    ("saturated_sigma", "conjugated_backbone", "saturation_conflicts_with_conjugated_skeleton"),
    ("aromatic_delocalized", "acyclic_linear", "aromaticity_requires_cyclic_or_extended_context"),
    ("aromatic_delocalized", "acyclic_branched", "aromaticity_requires_cyclic_or_extended_context"),
    ("geometric_e_z", "monocyclic_aromatic", "e_z_needs_non_aromatic_double_bond_context"),
    ("gas_phase", "aqueous", "gas_phase_conflicts_with_aqueous_solvent"),
    ("solid_or_crystalline", "vacuum_or_gas", "solid_phase_conflicts_with_gas_solvent_class"),
    ("cryogenic", "supercritical", "cryogenic_conflicts_with_supercritical_context"),
)
RULE_INDEX = {reason: index for index, (_, _, reason) in enumerate(RULES)}

@dataclass(frozen=True, slots=True)
class OakAssessment:
    compatibility_score: float
    contradiction_bits: int
    contradiction_count: int
    warnings: tuple[str, ...]
    status: str


def assess_coordinate(c: Mapping[str, str]) -> OakAssessment:
    values = set(c.values())
    warnings = []
    bits = 0
    for left, right, reason in RULES:
        if left in values and right in values:
            bits |= 1 << RULE_INDEX[reason]
            warnings.append(reason)
    if c.get("electronic_class") == "radical_or_open_shell":
        warnings.append("open_shell_requires_specialized_validation")
    if c.get("protonation_state") in {"multiply_charged", "unspecified_charge_state"}:
        warnings.append("charge_state_uncertainty")
    contradictions = bits.bit_count()
    score = max(0.0, 1.0 - 0.20 * contradictions - 0.03 * (len(warnings)-contradictions))
    status = "candidate_cell_unvalidated" if warnings else "structurally_compatible_template"
    return OakAssessment(round(score, 3), bits, contradictions, tuple(warnings), status)
