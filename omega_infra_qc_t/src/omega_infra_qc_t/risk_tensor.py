"""Risk tensor for InfrastructureGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal

RiskBand = Literal["low", "medium", "high", "critical"]


def _score(value: int) -> int:
    if not 0 <= value <= 5:
        raise ValueError("risk values must be between 0 and 5")
    return value


@dataclass(frozen=True)
class InfraRiskTensor:
    risk_id: str
    asset_id: str
    physical_condition: int = 0
    service_criticality: int = 0
    public_dependency: int = 0
    climate_exposure: int = 0
    cyber_dependency: int = 0
    supply_chain_dependency: int = 0
    maintenance_debt: int = 0
    financial_pressure: int = 0
    legal_regulatory_risk: int = 0
    equity_access_risk: int = 0
    privacy_security_sensitivity: int = 0
    reversibility: int = 5
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in [
            "physical_condition",
            "service_criticality",
            "public_dependency",
            "climate_exposure",
            "cyber_dependency",
            "supply_chain_dependency",
            "maintenance_debt",
            "financial_pressure",
            "legal_regulatory_risk",
            "equity_access_risk",
            "privacy_security_sensitivity",
            "reversibility",
        ]:
            _score(getattr(self, field_name))

    @property
    def pressure(self) -> int:
        return (
            self.physical_condition
            + self.service_criticality
            + self.public_dependency
            + self.climate_exposure
            + self.cyber_dependency
            + self.supply_chain_dependency
            + self.maintenance_debt
            + self.financial_pressure
            + self.legal_regulatory_risk
            + self.equity_access_risk
            + self.privacy_security_sensitivity
            + (5 - self.reversibility)
        )

    @property
    def band(self) -> RiskBand:
        if self.privacy_security_sensitivity >= 5 or self.service_criticality >= 5:
            return "critical"
        if self.pressure >= 38:
            return "critical"
        if self.pressure >= 27:
            return "high"
        if self.pressure >= 14:
            return "medium"
        return "low"

    @property
    def blocks_publication(self) -> bool:
        return self.band == "critical" or self.privacy_security_sensitivity >= 4

    @property
    def maintenance_priority(self) -> float:
        return round(
            0.25 * self.physical_condition
            + 0.25 * self.maintenance_debt
            + 0.20 * self.service_criticality
            + 0.15 * self.public_dependency
            + 0.10 * self.climate_exposure
            + 0.05 * (5 - self.reversibility),
            3,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "asset_id": self.asset_id,
            "physical_condition": self.physical_condition,
            "service_criticality": self.service_criticality,
            "public_dependency": self.public_dependency,
            "climate_exposure": self.climate_exposure,
            "cyber_dependency": self.cyber_dependency,
            "supply_chain_dependency": self.supply_chain_dependency,
            "maintenance_debt": self.maintenance_debt,
            "financial_pressure": self.financial_pressure,
            "legal_regulatory_risk": self.legal_regulatory_risk,
            "equity_access_risk": self.equity_access_risk,
            "privacy_security_sensitivity": self.privacy_security_sensitivity,
            "reversibility": self.reversibility,
            "pressure": self.pressure,
            "band": self.band,
            "blocks_publication": self.blocks_publication,
            "maintenance_priority": self.maintenance_priority,
            "notes": self.notes,
            "metadata": dict(self.metadata),
            "oak_note": "Risk tensor is a review signal, not a final engineering or authority decision.",
        }
