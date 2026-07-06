"""Risk tensor primitives for Ω-GOV-QC-T.

RiskTensor converts public-sector concerns into explicit dimensions so that
risks are visible, comparable, and reviewable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

RiskBand = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class RiskTensor:
    """Multi-axis risk score for public-sector modules."""

    risk_id: str
    name: str
    legal: int = 0
    privacy: int = 0
    security: int = 0
    fairness: int = 0
    human_impact: int = 0
    reversibility: int = 5
    evidence_quality: int = 3
    public_utility: int = 3
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.risk_id.strip():
            errors.append("risk_id is required")
        if not self.name.strip():
            errors.append("name is required")
        for field_name in [
            "legal",
            "privacy",
            "security",
            "fairness",
            "human_impact",
            "reversibility",
            "evidence_quality",
            "public_utility",
        ]:
            value = getattr(self, field_name)
            if not 0 <= value <= 5:
                errors.append(f"{field_name} must be between 0 and 5")
        return errors

    @property
    def risk_pressure(self) -> int:
        return self.legal + self.privacy + self.security + self.fairness + self.human_impact

    @property
    def support_strength(self) -> int:
        return self.reversibility + self.evidence_quality + self.public_utility

    @property
    def net_score(self) -> int:
        return self.support_strength - self.risk_pressure

    @property
    def band(self) -> RiskBand:
        if max(self.legal, self.privacy, self.security, self.fairness, self.human_impact) >= 5:
            return "critical"
        if self.risk_pressure >= 16:
            return "high"
        if self.risk_pressure >= 8:
            return "medium"
        return "low"

    @property
    def blocks_deployment(self) -> bool:
        return self.band == "critical" or self.legal >= 4 or self.privacy >= 4 or self.security >= 4

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "name": self.name,
            "legal": self.legal,
            "privacy": self.privacy,
            "security": self.security,
            "fairness": self.fairness,
            "human_impact": self.human_impact,
            "reversibility": self.reversibility,
            "evidence_quality": self.evidence_quality,
            "public_utility": self.public_utility,
            "risk_pressure": self.risk_pressure,
            "support_strength": self.support_strength,
            "net_score": self.net_score,
            "band": self.band,
            "blocks_deployment": self.blocks_deployment,
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }


@dataclass
class RiskRegister:
    """Collection of RiskTensor objects."""

    risks: Dict[str, RiskTensor] = field(default_factory=dict)
    m_minus: List[str] = field(default_factory=list)

    def add(self, risk: RiskTensor) -> None:
        errors = risk.validate()
        if errors:
            raise ValueError("Invalid RiskTensor: " + "; ".join(errors))
        if risk.risk_id in self.risks:
            self.m_minus.append(f"duplicate risk ignored: {risk.risk_id}")
            raise ValueError(f"duplicate risk_id: {risk.risk_id}")
        self.risks[risk.risk_id] = risk

    def blockers(self) -> List[RiskTensor]:
        return [risk for risk in self.risks.values() if risk.blocks_deployment]

    def quality_report(self) -> Dict[str, Any]:
        by_band: Dict[str, int] = {}
        for risk in self.risks.values():
            by_band[risk.band] = by_band.get(risk.band, 0) + 1
        return {
            "risk_count": len(self.risks),
            "by_band": by_band,
            "blockers": [risk.risk_id for risk in self.blockers()],
            "m_minus": list(self.m_minus),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_gov_qc_t.risk_register.v0",
            "risks": [risk.to_dict() for risk in self.risks.values()],
            "quality_report": self.quality_report(),
        }
