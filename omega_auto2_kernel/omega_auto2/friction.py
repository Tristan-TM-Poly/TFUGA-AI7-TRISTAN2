from __future__ import annotations

from .models import FrictionTensor


def compute_priority_score(tensor: FrictionTensor) -> float:
    """Calcule la priorité d'automatisation.

    Score élevé = candidat fort à AUTO²-FORGE.
    Le risque et le coût réduisent le score mais ne l'annulent pas si la valeur est forte.
    """

    t = tensor.clamp()
    positive = (
        0.20 * t.time_cost
        + 0.20 * t.repetition
        + 0.15 * t.cognitive_load
        + 0.10 * t.error_risk
        + 0.15 * t.value_loss
        + 0.10 * t.urgency
        + 0.10 * t.human_dependency
    )
    penalty = 0.12 * t.safety_risk + 0.08 * t.build_cost + 0.05 * t.complexity
    return round(max(0.0, min(1.0, positive - penalty)), 4)


def classify_priority(score: float) -> str:
    if score >= 0.85:
        return "automate_now"
    if score >= 0.65:
        return "forge_draft_workflow"
    if score >= 0.45:
        return "watch_and_collect_more_data"
    return "do_not_automate_yet"
