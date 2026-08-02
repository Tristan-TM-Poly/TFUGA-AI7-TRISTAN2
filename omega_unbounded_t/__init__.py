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
from .streaming import (
    BreakthroughEvent,
    MPlusLedger,
    RangeWorkSource,
    ResourceSampler,
    ResourceSnapshot,
)

__all__ = [
    "AdaptiveController",
    "AdditionRecord",
    "BatchResult",
    "BreakthroughEvent",
    "CapacityPolicy",
    "CapacityState",
    "GitHubDryRunPlanner",
    "GitHubPlanPolicy",
    "GitHubPlanReport",
    "ListWorkSource",
    "MMinusLedger",
    "MPlusLedger",
    "RangeWorkSource",
    "ResourceSampler",
    "ResourceSnapshot",
    "RunReport",
    "ShardRecord",
    "SyntheticCapacityExecutor",
    "iter_jsonl",
    "synthetic_additions",
]

__version__ = "0.3.0"
