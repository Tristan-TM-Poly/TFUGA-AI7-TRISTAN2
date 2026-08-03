"""Ω-HISTOSCI-HG-T∞ R0.1.

Executable OAK-safe infrastructure for representing the history of science as a
worldwide, multi-scale, provenance-aware directed hypergraph.
"""
from .graph import GraphAudit, HistoricalHypergraph
from .models import (
    BranchRecord,
    EdgeKind,
    EpistemicStatus,
    HistoricalEvent,
    HistoricalHyperedge,
    HistoricalNode,
    NegativeMemoryRecord,
    NodeKind,
    OAKAssessment,
    OAKEvidence,
    SourceReference,
    TemporalLayer,
    canonical_dict,
    canonical_json,
    content_hash,
)
from .oak import DEFAULT_WEIGHTS, OAKThresholds, assess_evidence, minimum_status_for_public_narrative
from .registry import HistoryRegistry, RegistryAudit
from .report import build_report
from .seed import MACRO_BRANCHES, SUBBRANCHES, build_seed

__all__ = [
    "BranchRecord",
    "DEFAULT_WEIGHTS",
    "EdgeKind",
    "EpistemicStatus",
    "GraphAudit",
    "HistoricalEvent",
    "HistoricalHyperedge",
    "HistoricalHypergraph",
    "HistoricalNode",
    "HistoryRegistry",
    "MACRO_BRANCHES",
    "NegativeMemoryRecord",
    "NodeKind",
    "OAKAssessment",
    "OAKEvidence",
    "OAKThresholds",
    "RegistryAudit",
    "SUBBRANCHES",
    "SourceReference",
    "TemporalLayer",
    "assess_evidence",
    "build_report",
    "build_seed",
    "canonical_dict",
    "canonical_json",
    "content_hash",
    "minimum_status_for_public_narrative",
]

__version__ = "0.1.0"
