from __future__ import annotations

from typing import Iterable, List, Mapping

from .bayes_mastery import weakest_axes
from .core import MasteryAxis, axis_label
from .cvcd import invariant_prompt

_ACTIONS = {
    MasteryAxis.UNDERSTANDING: "Écrire une explication Feynman en 12 lignes, puis identifier 2 zones floues.",
    MasteryAxis.RECALL: "Faire un rappel actif sans notes, puis corriger en rouge les oublis.",
    MasteryAxis.TRANSFER: "Résoudre une variante jamais vue et expliquer ce qui change/invariant.",
    MasteryAxis.SPEED: "Faire 5 problèmes chronométrés avec post-mortem de friction.",
    MasteryAxis.GENERALIZATION: "Construire une carte reliant ce concept à 3 domaines différents.",
    MasteryAxis.CREATIVITY: "Générer un mini-prototype ou une analogie nouvelle testable.",
    MasteryAxis.SAFETY: "Lister les hypothèses, limites, risques de surconfiance et contre-exemples.",
    MasteryAxis.AUTONOMY: "Créer un exercice original puis le résoudre sans aide externe.",
}


def generate_curriculum(
    mastery: Mapping[MasteryAxis, float],
    invariants: Iterable[str],
    goal: str,
    horizon_days: int = 7,
) -> List[str]:
    """Generate a compact micro-curriculum from weak axes and invariants."""

    weak = weakest_axes(mastery, limit=3)
    plan = [f"Objectif OAK {horizon_days} jours: {goal}"]
    plan.append(invariant_prompt(invariants))
    for day, axis in enumerate(weak, start=1):
        plan.append(f"Jour {day} — axe {axis_label(axis)}: {_ACTIONS[axis]}")
    plan.append("Jour final — OAK: test différé, variante nouvelle, explication courte, capture M⁻.")
    return plan
