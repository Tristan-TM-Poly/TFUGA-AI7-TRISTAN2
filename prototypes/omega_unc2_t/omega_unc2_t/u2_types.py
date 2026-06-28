"""Typed data structures for Ω-UNC²-T."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

OAKStatus = Literal["BLACK", "RED", "ORANGE", "YELLOW", "GREEN", "BLUE", "GOLD"]


def clamp01(value: float) -> float:
    """Clamp a numeric score to the closed interval [0, 1]."""

    return max(0.0, min(1.0, float(value)))


@dataclass(slots=True)
class EvidencePacket:
    """Evidence and counter-evidence attached to a claim.

    evidence_strength is intentionally separated from confidence. A model can be
    confident with weak evidence; Ω-UNC²-T treats that as confidence debt.
    """

    sources: list[str] = field(default_factory=list)
    experiments: list[str] = field(default_factory=list)
    counterexamples: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class U2Claim:
    """Claim object with first-order and second-order uncertainty.

    Scores use the convention 0 = low/benign and 1 = high/severe.
    reversibility uses the opposite semantic convention: 0 = irreversible,
    1 = fully reversible.
    """

    claim: str
    estimate: float | int | str | None = None
    uncertainty_u1: dict[str, float] = field(default_factory=dict)
    meta_uncertainty_u2: dict[str, float] = field(default_factory=dict)
    evidence_strength: float = 0.0
    residual_score: float = 0.0
    decision_cost: float = 0.0
    reversibility: float = 1.0
    fertility: float = 0.0
    value: float = 0.0
    domain_valid_when: list[str] = field(default_factory=list)
    domain_invalid_when: list[str] = field(default_factory=list)
    counter_hypotheses: list[str] = field(default_factory=list)
    evidence: EvidencePacket = field(default_factory=EvidencePacket)
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "U2Claim":
        """Return a copy with numeric scores clamped to [0, 1]."""

        return U2Claim(
            claim=self.claim,
            estimate=self.estimate,
            uncertainty_u1={k: clamp01(v) for k, v in self.uncertainty_u1.items()},
            meta_uncertainty_u2={k: clamp01(v) for k, v in self.meta_uncertainty_u2.items()},
            evidence_strength=clamp01(self.evidence_strength),
            residual_score=clamp01(self.residual_score),
            decision_cost=clamp01(self.decision_cost),
            reversibility=clamp01(self.reversibility),
            fertility=clamp01(self.fertility),
            value=clamp01(self.value),
            domain_valid_when=list(self.domain_valid_when),
            domain_invalid_when=list(self.domain_invalid_when),
            counter_hypotheses=list(self.counter_hypotheses),
            evidence=self.evidence,
            metadata=dict(self.metadata),
        )


@dataclass(slots=True)
class OAKU2Result:
    """Computed OAK-U² status and action recommendation."""

    status: OAKStatus
    u1: float
    u2: float
    risk: float
    maturity: float
    confidence_debt: float
    priority: float
    next_action: str
    rationale: list[str] = field(default_factory=list)
