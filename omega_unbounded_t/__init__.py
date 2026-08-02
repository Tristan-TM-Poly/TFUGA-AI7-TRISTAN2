"""Ω-SANS-PLAFOND-T∞ adaptive capacity-seeking iteration engine.

The package removes permanent addition-count caps from the control model. Each
run remains physically bounded by its finite workload, recoverability, quality
requirements, available resources, and external service rules.
"""

from .core import (
    AdaptiveController,
    BatchResult,
    CapacityPolicy,
    CapacityState,
    ListWorkSource,
    MMinusLedger,
    RunReport,
    SyntheticCapacityExecutor,
)
from .github_planner import (
    AdditionRecord,
    GitHubDryRunPlanner,
    GitHubPlanPolicy,
    GitHubPlanReport,
    ShardRecord,
    iter_jsonl,
    synthetic_additions,
)
from .self_improvement import (
    ControllerVariant,
    PromotionDecision,
    ScenarioOutcome,
    SelfImprovementLab as RawSelfImprovementLab,
    SelfImprovementReport,
    SelfImprovementScenario,
    VariantOutcome,
    adaptive_candidate_stream,
    default_scenarios,
    iter_variants_jsonl,
)
from .self_improvement_judge import ResourceAwareSelfImprovementLab
from .streaming import (
    BreakthroughEvent,
    MPlusLedger,
    RangeWorkSource,
    ResourceSampler,
    ResourceSnapshot,
)

SelfImprovementLab = ResourceAwareSelfImprovementLab

__all__ = [
    "AdaptiveController",
    "AdditionRecord",
    "BatchResult",
    "BreakthroughEvent",
    "CapacityPolicy",
    "CapacityState",
    "ControllerVariant",
    "GitHubDryRunPlanner",
    "GitHubPlanPolicy",
    "GitHubPlanReport",
    "ListWorkSource",
    "MMinusLedger",
    "MPlusLedger",
    "PromotionDecision",
    "RangeWorkSource",
    "RawSelfImprovementLab",
    "ResourceAwareSelfImprovementLab",
    "ResourceSampler",
    "ResourceSnapshot",
    "RunReport",
    "ScenarioOutcome",
    "SelfImprovementLab",
    "SelfImprovementReport",
    "SelfImprovementScenario",
    "ShardRecord",
    "SyntheticCapacityExecutor",
    "VariantOutcome",
    "adaptive_candidate_stream",
    "default_scenarios",
    "iter_jsonl",
    "iter_variants_jsonl",
    "synthetic_additions",
]

__version__ = "0.4.1"
