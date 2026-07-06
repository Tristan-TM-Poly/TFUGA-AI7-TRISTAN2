"""Resilience scenarios for InfrastructureGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

ScenarioKind = Literal[
    "flood",
    "ice_storm",
    "heat_wave",
    "wildfire_smoke",
    "power_outage",
    "logistics_disruption",
    "cyber_incident",
    "other",
]


@dataclass(frozen=True)
class ResilienceScenario:
    scenario_id: str
    name: str
    kind: ScenarioKind = "other"
    affected_asset_ids: List[str] = field(default_factory=list)
    expected_service_impact: int = 0
    preparedness_level: int = 0
    recovery_complexity: int = 0
    evidence_quality: int = 0
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in ScenarioKind.__args__:  # type: ignore[attr-defined]
            raise ValueError(f"invalid scenario kind: {self.kind}")
        for field_name in [
            "expected_service_impact",
            "preparedness_level",
            "recovery_complexity",
            "evidence_quality",
        ]:
            value = getattr(self, field_name)
            if not 0 <= value <= 5:
                raise ValueError(f"{field_name} must be between 0 and 5")

    @property
    def resilience_pressure(self) -> int:
        return self.expected_service_impact + self.recovery_complexity + (5 - self.preparedness_level)

    @property
    def band(self) -> str:
        if self.resilience_pressure >= 11:
            return "high"
        if self.resilience_pressure >= 7:
            return "medium"
        return "low"

    @property
    def needs_review(self) -> bool:
        return self.band == "high" or self.evidence_quality < 3

    def to_dict(self, *, public_safe: bool = True) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "kind": self.kind,
            "affected_asset_count": len(self.affected_asset_ids),
            "affected_asset_ids": [] if public_safe else list(self.affected_asset_ids),
            "expected_service_impact": self.expected_service_impact,
            "preparedness_level": self.preparedness_level,
            "recovery_complexity": self.recovery_complexity,
            "evidence_quality": self.evidence_quality,
            "resilience_pressure": self.resilience_pressure,
            "band": self.band,
            "needs_review": self.needs_review,
            "notes": self.notes,
            "metadata": {} if public_safe else dict(self.metadata),
            "oak_note": "Scenario is generalized decision support, not an emergency plan.",
        }
