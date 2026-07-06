"""Maintenance prioritization for InfrastructureGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal

MaintenanceBand = Literal["monitor", "planned", "priority", "urgent"]


@dataclass(frozen=True)
class MaintenanceSignal:
    signal_id: str
    asset_id: str
    condition_score: int = 0
    service_criticality: int = 0
    maintenance_debt: int = 0
    climate_exposure: int = 0
    cost_of_delay: int = 0
    reversibility: int = 5
    evidence_quality: int = 0
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in [
            "condition_score",
            "service_criticality",
            "maintenance_debt",
            "climate_exposure",
            "cost_of_delay",
            "reversibility",
            "evidence_quality",
        ]:
            value = getattr(self, field_name)
            if not 0 <= value <= 5:
                raise ValueError(f"{field_name} must be between 0 and 5")

    @property
    def priority_score(self) -> float:
        return round(
            0.25 * self.condition_score
            + 0.20 * self.service_criticality
            + 0.20 * self.maintenance_debt
            + 0.15 * self.climate_exposure
            + 0.15 * self.cost_of_delay
            + 0.05 * (5 - self.reversibility),
            3,
        )

    @property
    def band(self) -> MaintenanceBand:
        if self.priority_score >= 4.0:
            return "urgent"
        if self.priority_score >= 3.0:
            return "priority"
        if self.priority_score >= 1.5:
            return "planned"
        return "monitor"

    @property
    def needs_more_evidence(self) -> bool:
        return self.evidence_quality < 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "asset_id": self.asset_id,
            "condition_score": self.condition_score,
            "service_criticality": self.service_criticality,
            "maintenance_debt": self.maintenance_debt,
            "climate_exposure": self.climate_exposure,
            "cost_of_delay": self.cost_of_delay,
            "reversibility": self.reversibility,
            "evidence_quality": self.evidence_quality,
            "priority_score": self.priority_score,
            "band": self.band,
            "needs_more_evidence": self.needs_more_evidence,
            "notes": self.notes,
            "metadata": dict(self.metadata),
            "oak_note": "Maintenance signal is prioritization support, not an engineering order.",
        }
