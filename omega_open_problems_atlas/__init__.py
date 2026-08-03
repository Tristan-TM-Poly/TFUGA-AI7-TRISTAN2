"""Ω-OPEN-PROBLEMS-ATLAS-T∞ R0.1.

Research-software infrastructure for representing, checking, decomposing and
routing open mathematical problems. The package never promotes a source claim,
finite computation or generated research cell into a mathematical proof.
"""

from .models import (
    EpistemicStatus,
    OpenStatus,
    ProblemGenome,
    ProblemKind,
    ResearchCell,
    SourceRecord,
)
from .oak import OAKDecision, evaluate_problem
from .registry import ProblemRegistry

__all__ = [
    "EpistemicStatus",
    "OpenStatus",
    "ProblemGenome",
    "ProblemKind",
    "ResearchCell",
    "SourceRecord",
    "OAKDecision",
    "ProblemRegistry",
    "evaluate_problem",
]

__version__ = "0.1.0"
