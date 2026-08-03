"""Ω-MULTI-JUDGE-DOJO-T∞ R0.5."""

from .benchmark import main, run_r05_benchmark
from .engine import MultiJudgeEngine, MultiJudgePolicy, fixture_references
from .policy import (
    AccessRequest,
    ContaminationError,
    Decision,
    Normalizer,
    PLATFORMS,
    PlatformMode,
    PolicyGate,
    ProblemRef,
)

__all__ = [
    "AccessRequest",
    "ContaminationError",
    "Decision",
    "MultiJudgeEngine",
    "MultiJudgePolicy",
    "Normalizer",
    "PLATFORMS",
    "PlatformMode",
    "PolicyGate",
    "ProblemRef",
    "fixture_references",
    "main",
    "run_r05_benchmark",
]
