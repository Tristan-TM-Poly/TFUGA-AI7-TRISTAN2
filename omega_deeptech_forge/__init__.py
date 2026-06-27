"""Omega DeepTech Intelligence Forge.

A small OAK-safe scaffold for deeptech intelligence, IP triage,
prototype routing, and revenue action extraction.
"""

from .core import (
    EvidenceLevel,
    IPClass,
    OAKStatus,
    Signal,
    ForgeDecision,
    classify_ip,
    oak_gate,
    forge_decision,
)

__all__ = [
    "EvidenceLevel",
    "IPClass",
    "OAKStatus",
    "Signal",
    "ForgeDecision",
    "classify_ip",
    "oak_gate",
    "forge_decision",
]
