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

__all__ = [
    "AdaptiveController",
    "BatchResult",
    "CapacityPolicy",
    "CapacityState",
    "ListWorkSource",
    "MMinusLedger",
    "RunReport",
    "SyntheticCapacityExecutor",
]

__version__ = "0.1.0"
