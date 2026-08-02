"""Typed reaction-family rules with explicit balance and domain gates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True, slots=True)
class ReactionRule:
    name: str
    reactant_families: tuple[str, ...]
    product_families: tuple[str, ...]
    required_conditions: tuple[str, ...]
    forbidden_conditions: tuple[str, ...] = ()
    status: str = "mechanism_family_template"

RULES = (
    ReactionRule("alcohol_oxidation", ("alcohol_phenol",), ("aldehyde_ketone", "carboxylic_acid"), ("oxidizing_context",), ("strongly_reducing_context",)),
    ReactionRule("ester_hydrolysis", ("ester_anhydride",), ("carboxylic_acid", "alcohol_phenol"), ("water_or_nucleophile",), ("strictly_anhydrous_context",)),
    ReactionRule("amide_hydrolysis", ("amide_imide",), ("carboxylic_acid", "amine_imine"), ("water", "activation"), ("strictly_anhydrous_context",)),
)

def evaluate_reaction(name: str, *, reactants: tuple[str, ...], conditions: tuple[str, ...], atom_balance: Mapping[str, int] | None = None, charge_balance: int = 0) -> dict[str, object]:
    rule = next((r for r in RULES if r.name == name), None)
    if rule is None:
        return {"name": name, "status": "unknown_rule", "promotable": False}
    condition_set = set(conditions)
    missing = sorted(set(rule.required_conditions)-condition_set)
    forbidden = sorted(set(rule.forbidden_conditions)&condition_set)
    wrong_reactants = sorted(set(rule.reactant_families)-set(reactants))
    balanced = atom_balance is not None and all(value == 0 for value in atom_balance.values()) and charge_balance == 0
    promotable = not missing and not forbidden and not wrong_reactants and balanced
    return {"name": name, "missing_conditions": missing, "forbidden_conditions": forbidden, "missing_reactant_families": wrong_reactants, "balanced": balanced, "promotable": promotable, "status": "template_pass" if promotable else "requires_review"}
