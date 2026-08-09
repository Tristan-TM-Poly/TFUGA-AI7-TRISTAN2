from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, List


@dataclass(frozen=True)
class ModelScore:
    name: str
    predictive_loss: float
    complexity: float
    uncertainty: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be non-empty")
        for field_name in ("predictive_loss", "complexity", "uncertainty"):
            value = getattr(self, field_name)
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{field_name} must be finite and >= 0")


@dataclass(frozen=True)
class OAKBench:
    """Evidence-aware model-selection gate; lower score is better.

    OAKBench is not proof. It makes the trade-off between predictive error,
    complexity and uncertainty explicit and reproducible.
    """

    complexity_penalty: float = 0.01
    uncertainty_penalty: float = 0.10

    def score(self, model: ModelScore) -> float:
        return (
            model.predictive_loss
            + self.complexity_penalty * model.complexity
            + self.uncertainty_penalty * model.uncertainty
        )

    def rank(self, models: Iterable[ModelScore]) -> List[ModelScore]:
        return sorted(models, key=lambda model: (self.score(model), model.complexity, model.name))

    def improvement_required(self, simple: ModelScore, complex_model: ModelScore) -> float:
        """Predictive-loss improvement needed for complexity/uncertainty to pay for itself."""

        extra_penalty = (
            self.complexity_penalty * (complex_model.complexity - simple.complexity)
            + self.uncertainty_penalty * (complex_model.uncertainty - simple.uncertainty)
        )
        return max(0.0, extra_penalty)

    def justified(self, baseline: ModelScore, candidate: ModelScore) -> bool:
        return self.score(candidate) < self.score(baseline)
