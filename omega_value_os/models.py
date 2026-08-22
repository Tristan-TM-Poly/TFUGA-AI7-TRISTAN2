"""Core data models for Ω Value OS.

The module is deliberately dependency-free so governance logic can run before
optional web, payments, or AI integrations are loaded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, Mapping, Tuple


class RevenueMode(str, Enum):
    ACTIVE = "active"
    PASSIVE = "passive"
    MIXED = "mixed"


class AutomationLevel(int, Enum):
    MANUAL = 0
    SUGGEST = 1
    HUMAN_APPROVED = 2
    BOUNDED_AUTONOMY = 3
    ZERO_TOUCH = 4
    SELF_REGENERATING = 5


class RegenerationLevel(int, Enum):
    ASSET = 0
    CHANNEL = 1
    OFFER = 2
    BUSINESS_MODEL = 3
    GENERATOR = 4
    ECOSYSTEM = 5


@dataclass(frozen=True)
class ValueGenome:
    need: str
    capability: str
    beneficiary: str
    transformation: str
    evidence: Tuple[str, ...] = ()
    assets: Tuple[str, ...] = ()
    channels: Tuple[str, ...] = ()
    revenue_mode: RevenueMode = RevenueMode.MIXED
    risks: Tuple[str, ...] = ()


@dataclass(frozen=True)
class StrategyGenome:
    market: str
    offer: str
    channel: str
    price_hypothesis: str
    experiment: str
    rollback: str
    no_action_baseline: str = "do_nothing"


@dataclass(frozen=True)
class AuthorityEnvelope:
    allowed_actions: FrozenSet[str]
    max_budget: float = 0.0
    max_irreversibility: float = 0.0
    requires_human_approval: FrozenSet[str] = frozenset()

    def allows(self, action: str) -> bool:
        return action in self.allowed_actions and action not in self.requires_human_approval


@dataclass(frozen=True)
class AutomationCandidate:
    action: str
    repeatability: float
    observability: float
    reversibility: float
    auditability: float
    verified_benefit: float
    downside: float
    irreversibility: float
    permission_sensitivity: float
    compliance_risk: float
    model_uncertainty: float
    estimated_cost: float = 0.0
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AutomationDecision:
    level: AutomationLevel
    score: float
    permitted: bool
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class ProofOfBetterReceipt:
    candidate: str
    baseline: str
    metrics_candidate: Dict[str, float]
    metrics_baseline: Dict[str, float]
    hard_gate_passed: bool
    uncertainty: float
    rollback: str


@dataclass(frozen=True)
class ProofCarryingRevenueStream:
    name: str
    beneficiary: str
    value_claim: str
    evidence: Tuple[str, ...]
    gross_revenue: float
    direct_cost: float
    trust_delta: float
    platform_dependency: float
    compliance_risk: float

    @property
    def contribution_margin(self) -> float:
        return self.gross_revenue - self.direct_cost
