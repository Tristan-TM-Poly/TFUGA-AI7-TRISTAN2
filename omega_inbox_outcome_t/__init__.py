"""Ω-INBOX-TO-OUTCOME-T: bounded autonomous case, deliverable, and reply OS."""

from .engine import InboxOutcomeEngine, OutcomeResult
from .intake import IntakeRegistry
from .intent import analyze_request
from .models import (
    AutonomousDeliveryContract,
    CaseRecord,
    Channel,
    DataClass,
    DeliverableManifest,
    GateResult,
    IntakeEvent,
    Intent,
    ReplyDecision,
    ResolvedIdentity,
)
from .policy import gate_case

__all__ = [
    "AutonomousDeliveryContract",
    "CaseRecord",
    "Channel",
    "DataClass",
    "DeliverableManifest",
    "GateResult",
    "InboxOutcomeEngine",
    "IntakeEvent",
    "IntakeRegistry",
    "Intent",
    "OutcomeResult",
    "ReplyDecision",
    "ResolvedIdentity",
    "analyze_request",
    "gate_case",
]

__version__ = "0.1.0"
