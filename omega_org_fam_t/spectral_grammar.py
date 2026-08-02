"""Provenance-aware family-level spectral grammar, not an identity oracle."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True, slots=True)
class SpectralRule:
    family: str
    modality: str
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()
    counter_signatures: tuple[str, ...] = ()
    provenance: str = "curated_family_rule_r02"
    status: str = "family_level_expectation"

RULES = (
    SpectralRule("alcohol_phenol", "ftir", ("O-H environment", "C-O mode"), ("hydrogen_bond_broadening",), ("no_oxygen_evidence",)),
    SpectralRule("aldehyde_ketone", "ftir", ("carbonyl mode",), ("aldehydic C-H",), ("carbonyl_absent",)),
    SpectralRule("carboxylic_acid", "ftir", ("carbonyl mode", "acidic O-H environment"), ("dimerization_shift",), ("acidic_O-H_absent",)),
    SpectralRule("amide_imide", "raman", ("amide carbonyl mode", "C-N coupling"), ("N-H mode",), ("nitrogen_inconsistent",)),
    SpectralRule("nitrile_isocyanate", "raman", ("cumulene_or_triple-bond region",), (), ("diagnostic_region_absent",)),
)

def evaluate_family(family: str, modality: str, observed: Iterable[str]) -> dict[str, object]:
    obs = set(observed)
    candidates = [r for r in RULES if r.family == family and r.modality == modality]
    if not candidates:
        return {"family": family, "modality": modality, "score": 0.0, "status": "no_curated_rule", "warnings": ["absence_of_rule_is_not_negative_evidence"]}
    rule = candidates[0]
    matched = sorted(obs.intersection(rule.required + rule.optional))
    missing = sorted(set(rule.required)-obs)
    counters = sorted(obs.intersection(rule.counter_signatures))
    denominator = max(1, len(rule.required))
    score = max(0.0, (len(set(rule.required)&obs)-len(counters))/denominator)
    return {"family": family, "modality": modality, "score": round(score, 3), "matched": matched, "missing_required": missing, "counter_signatures": counters, "status": "compatible_not_identified" if score > 0 else "insufficient_or_conflicting"}
