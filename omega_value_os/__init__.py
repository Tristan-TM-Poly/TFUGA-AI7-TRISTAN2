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
from .portfolio import RevenueStreamMetrics, platform_concentration, prune_candidates, revenue_mode_mix
from .world_model import EconomicState, Shock, ShockResult, apply_shock, shock_curriculum

__all__ = [
    "AutomationCandidate",
    "AutomationDecision",
    "AutomationLevel",
    "AuthorityEnvelope",
    "ChannelProfile",
    "ContentAsset",
    "ContentProjection",
    "EconomicState",
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
    "RevenueStreamMetrics",
    "Shock",
    "ShockResult",
    "StrategyGenome",
    "ValueGenome",
    "apply_shock",
    "automation_score",
    "channel_score",
    "compile_projections",
    "decide_automation",
    "evaluate_hard_gates",
    "is_sensitive_action",
    "meta_stop_rule",
    "mutate_generator",
    "platform_concentration",
    "proof_of_better",
    "prune_candidates",
    "revenue_mode_mix",
    "route_channels",
    "shock_curriculum",
    "should_create_meta_layer",
    "value_objective",
]
