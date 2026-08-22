"""Ω Value OS — proof-carrying regenerative monetization kernel."""

from .constitution import GateResult, evaluate_hard_gates, is_sensitive_action
from .engine import (
    automation_score,
    decide_automation,
    meta_stop_rule,
    proof_of_better,
    value_objective,
)
from .entitlements import EntitlementEvent, EntitlementEventType, EntitlementLedger
from .media import (
    ChannelProfile,
    ContentAsset,
    ContentProjection,
    channel_score,
    compile_projections,
    route_channels,
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
    "ChannelProfile",
    "ContentAsset",
    "ContentProjection",
    "EntitlementEvent",
    "EntitlementEventType",
    "EntitlementLedger",
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
    "channel_score",
    "compile_projections",
    "decide_automation",
    "evaluate_hard_gates",
    "is_sensitive_action",
    "meta_stop_rule",
    "mutate_generator",
    "proof_of_better",
    "route_channels",
    "should_create_meta_layer",
    "value_objective",
]
