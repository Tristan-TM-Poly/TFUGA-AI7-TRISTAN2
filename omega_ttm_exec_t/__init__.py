"""Ω-TTM-EXEC-T — convergence layer reusing canonical Tristan runtimes."""

from .compile import compile_report
from .epistemic import Claim, EpistemicStatus, EvidenceClass, OAKDecision, evaluate_claim
from .execute import execute_report
from .primitives import TTM_PRIMITIVES, primitive_contract

__all__ = [
    "Claim", "EpistemicStatus", "EvidenceClass", "OAKDecision",
    "TTM_PRIMITIVES", "compile_report", "execute_report",
    "evaluate_claim", "primitive_contract",
]

__version__ = "0.1.0"
