"""Resource flow primitive for GameEngineOS-T."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class ResourceFlow:
    """Track changes in energy, matter, value, and knowledge."""

    energy: float = 0.0
    matter: float = 0.0
    value: float = 0.0
    knowledge: float = 0.0

    def total_positive(self) -> float:
        return sum(max(0.0, value) for value in (self.energy, self.matter, self.value, self.knowledge))

    def total_negative(self) -> float:
        return sum(abs(min(0.0, value)) for value in (self.energy, self.matter, self.value, self.knowledge))

    def normalized_score(self) -> float:
        positive = self.total_positive()
        negative = self.total_negative()
        if positive + negative == 0:
            return 0.5
        return max(0.0, min(1.0, positive / (positive + negative)))

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


__all__ = ["ResourceFlow"]
