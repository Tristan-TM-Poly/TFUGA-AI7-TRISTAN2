"""Ω-VALUE-OS-T∞ R0.1 — executable value constitution and OAK judiciary."""

from .constitution import CONSTITUTION, CONTEXT_PROFILES, KERNELS
from .engine import evaluate_case, evaluate_portfolio, oak_report
from .models import (
    AutonomyLevel,
    DecisionReport,
    DecisionStatus,
    EvidenceLevel,
    ValueCase,
    ValueDimension,
)

__all__ = [
    "AutonomyLevel",
    "CONSTITUTION",
    "CONTEXT_PROFILES",
    "DecisionReport",
    "DecisionStatus",
    "EvidenceLevel",
    "KERNELS",
    "ValueCase",
    "ValueDimension",
    "evaluate_case",
    "evaluate_portfolio",
    "oak_report",
]

__version__ = "0.1.0"
