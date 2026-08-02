"""OAKGate: evidence, uncertainty, privacy, provenance, and publication guardrails."""

from .config import DEFAULT_RULE_PACK, PatternRule, RulePack, load_rule_pack
from .gates import evaluate_claim
from .model import (
    Claim,
    EpistemicLayer,
    EpistemicStatus,
    GateDecision,
    GateReport,
    ScannedClaim,
    SourceLocation,
)
from .provenance import claim_provenance_hash, verify_claim_provenance
from .uncertainty import ConfidenceAssessment, assess_confidence

__all__ = [
    "Claim",
    "ConfidenceAssessment",
    "DEFAULT_RULE_PACK",
    "EpistemicLayer",
    "EpistemicStatus",
    "GateDecision",
    "GateReport",
    "PatternRule",
    "RulePack",
    "ScannedClaim",
    "SourceLocation",
    "assess_confidence",
    "claim_provenance_hash",
    "evaluate_claim",
    "load_rule_pack",
    "verify_claim_provenance",
]

__version__ = "0.2.0"
