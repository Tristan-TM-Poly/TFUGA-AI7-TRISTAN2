"""Ω-TTM-EXEC-T — executable convergence layer for TTM-2048.

This package deliberately reuses the repository's canonical WorkUnit, Capability OS,
and Cognitive Computer instead of defining parallel copies of those abstractions.
"""

from .epistemic import Claim, EpistemicStatus, EvidenceClass, OAKDecision, evaluate_claim
from .primitives import TTM_PRIMITIVES, primitive_contract
from .runtime import TTMRuntime

__all__ = [
    "Claim",
    "EpistemicStatus",
    "EvidenceClass",
    "OAKDecision",
    "TTM_PRIMITIVES",
    "TTMRuntime",
    "evaluate_claim",
    "primitive_contract",
]

__version__ = "0.1.0"
