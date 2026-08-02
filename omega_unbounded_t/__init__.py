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

__all__ = [
    "AdaptiveController",
    "AdditionRecord",
    "BatchResult",
    "CapacityPolicy",
    "CapacityState",
    "GitHubDryRunPlanner",
    "GitHubPlanPolicy",
    "GitHubPlanReport",
    "ListWorkSource",
    "MMinusLedger",
    "RunReport",
    "ShardRecord",
    "SyntheticCapacityExecutor",
    "iter_jsonl",
    "synthetic_additions",
]

__version__ = "0.2.0"
