"""OAKGate: evidence, uncertainty, privacy, and publication guardrails."""

from .gates import evaluate_claim
from .model import Claim, EpistemicLayer, EpistemicStatus, GateDecision, GateReport

__all__ = [
    "Claim",
    "EpistemicLayer",
    "EpistemicStatus",
    "GateDecision",
    "GateReport",
    "evaluate_claim",
]

__version__ = "0.1.0"
