"""Ω Value OS — proof-carrying regenerative monetization kernel."""

from .constitution import GateResult, evaluate_hard_gates, is_sensitive_action
from .engine import (
    automation_score,
    decide_automation,
    meta_stop_rule,
    proof_of_better,
    value_objective,
)
from .meta import GeneratorGenome, MetaCandidate, mutate_generator, should_create_meta_layer
from .models import (
    AutomationCandidate,
    AutomationDecision,
    AutomationLevel,
    AuthorityEnvelope,
    ProofCarryingRevenueStream,
    ProofOfBetterReceipt,
    RegenerationLevel,
    RevenueMode,
    StrategyGenome,
    ValueGenome,
)

__all__ = [
    "AutomationCandidate",
    "AutomationDecision",
    "AutomationLevel",
    "AuthorityEnvelope",
    "GateResult",
    "GeneratorGenome",
    "MetaCandidate",
    "ProofCarryingRevenueStream",
    "ProofOfBetterReceipt",
    "RegenerationLevel",
    "RevenueMode",
    "StrategyGenome",
    "ValueGenome",
    "automation_score",
    "decide_automation",
    "evaluate_hard_gates",
    "is_sensitive_action",
    "meta_stop_rule",
    "mutate_generator",
    "proof_of_better",
    "should_create_meta_layer",
    "value_objective",
]
