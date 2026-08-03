"""Public API for Ω-PROBLEM-ATLAS-T∞ R0.8 evidence routing."""

from .audit import audit_routing_campaign
from .compiler import compile_routing_campaign
from .model import EVENT_RULES, EVENT_SCHEMA

__all__ = [
    "EVENT_RULES",
    "EVENT_SCHEMA",
    "audit_routing_campaign",
    "compile_routing_campaign",
]
