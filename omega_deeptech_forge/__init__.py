"""Omega DeepTech Intelligence Forge.

A small OAK-safe scaffold for deeptech intelligence, IP triage,
prototype routing, revenue action extraction, review packet generation,
and OAKBench action scoring.
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
from .review_packets import (
    ReviewPacket,
    ValueAxisScores,
    build_review_packet,
    build_offer_card,
    build_prior_art_query_pack,
    build_publication_note,
    build_ip_disclosure_draft,
)
from .oakbench import (
    OAKBenchResult,
    OAKBenchWeights,
    rank_signals,
    run_oakbench,
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
    "ReviewPacket",
    "ValueAxisScores",
    "build_review_packet",
    "build_offer_card",
    "build_prior_art_query_pack",
    "build_publication_note",
    "build_ip_disclosure_draft",
    "OAKBenchResult",
    "OAKBenchWeights",
    "rank_signals",
    "run_oakbench",
]
