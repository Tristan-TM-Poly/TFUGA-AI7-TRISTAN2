from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Mapping

from .bayes_mastery import confidence_penalty
from .core import Evidence, MasteryAxis, clamp01, mean
from .m_minus_registry import MMinusRegistry


@dataclass(frozen=True)
class OAKBenchResult:
    retention: float
    transfer: float
    robustness: float
    explanation: float
    calibration: float
    residue: float
    cost: float
    negentropy_index: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def oakbench(
    mastery: Mapping[MasteryAxis, float],
    evidence: Iterable[Evidence],
    registry: MMinusRegistry,
    cost: float = 1.0,
) -> OAKBenchResult:
    """Compute an auditable, non-magical learning score.

    The score rewards mastery in core axes and penalizes open errors, uncertainty, and cost.
    """

    cost = max(0.1, float(cost))
    retention = mastery.get(MasteryAxis.RECALL, 0.5)
    transfer = mastery.get(MasteryAxis.TRANSFER, 0.5)
    robustness = mean([
        mastery.get(MasteryAxis.GENERALIZATION, 0.5),
        mastery.get(MasteryAxis.SAFETY, 0.5),
        mastery.get(MasteryAxis.AUTONOMY, 0.5),
    ])
    explanation = mastery.get(MasteryAxis.UNDERSTANDING, 0.5)
    calibration = 1.0 - confidence_penalty(evidence)
    residue = clamp01(registry.oak_residue())
    numerator = retention * transfer * robustness * explanation * calibration
    negentropy_index = clamp01(numerator / (cost * (1.0 + residue)))
    status = "canon_candidate" if negentropy_index >= 0.45 and residue < 0.25 else "practice_required"
    return OAKBenchResult(
        retention=clamp01(retention),
        transfer=clamp01(transfer),
        robustness=clamp01(robustness),
        explanation=clamp01(explanation),
        calibration=clamp01(calibration),
        residue=residue,
        cost=cost,
        negentropy_index=negentropy_index,
        status=status,
    )


def oak_questions() -> list[str]:
    return [
        "Puis-je résoudre sans regarder mes notes?",
        "Puis-je résoudre une variante nouvelle?",
        "Puis-je expliquer en langage simple et en équations?",
        "Puis-je identifier une mauvaise solution et dire pourquoi elle est mauvaise?",
        "Puis-je appliquer l'idée dans un autre domaine?",
        "Ai-je capturé mes erreurs en M⁻ avec un futur test?",
    ]
