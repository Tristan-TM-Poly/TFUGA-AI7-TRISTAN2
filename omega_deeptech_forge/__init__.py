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
    HandoffPacket,
    classify_ip,
    oak_gate,
    forge_decision,
    handoff_route,
    build_handoff_packet,
    dry_run_report,
    write_handoff_packet,
)

__all__ = [
    "EvidenceLevel",
    "IPClass",
    "OAKStatus",
    "Signal",
    "ForgeDecision",
    "HandoffPacket",
    "classify_ip",
    "oak_gate",
    "forge_decision",
    "handoff_route",
    "build_handoff_packet",
    "dry_run_report",
    "write_handoff_packet",
]
