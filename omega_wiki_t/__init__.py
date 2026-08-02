"""Ω-WIKI-T∞ / WikiForge-T multilingual evidence and hyperknowledge compiler.

R0.3 preserves provenance across Wikipedia extraction, repository-theory
absorption, atomic claims, evidence records, contradictions, temporal OAK
transitions, and action queues. Generated relations remain candidates rather
than verified truth or scientific certification.
"""

from .action_queue import ActionItem, build_action_queue, queue_summary
from .contradiction_engine import ClaimCollision, detect_claim_collisions
from .core import (
    ArticleRecord,
    ClaimRecord,
    CompileResult,
    MediaWikiClient,
    SourceRecord,
    WikiCompiler,
    invariant_tokens,
)
from .hyperknowledge import HyperKnowledgeCompiler
from .knowledge_cell import (
    AuditFinding,
    AuditReport,
    ClaimAtom,
    EvidenceRecord,
    KnowledgeCell,
    OakTransition,
    audit_cells,
)
from .theory_hypergraph import (
    KnowledgeHyperedge,
    TheoryHypergraph,
    TheoryHypergraphBuilder,
    TheoryNode,
    node_key,
    normalize_label,
    utility_score,
)

__all__ = [
    "ActionItem",
    "ArticleRecord",
    "AuditFinding",
    "AuditReport",
    "ClaimAtom",
    "ClaimCollision",
    "ClaimRecord",
    "CompileResult",
    "EvidenceRecord",
    "HyperKnowledgeCompiler",
    "KnowledgeCell",
    "KnowledgeHyperedge",
    "MediaWikiClient",
    "OakTransition",
    "SourceRecord",
    "TheoryHypergraph",
    "TheoryHypergraphBuilder",
    "TheoryNode",
    "WikiCompiler",
    "audit_cells",
    "build_action_queue",
    "detect_claim_collisions",
    "invariant_tokens",
    "node_key",
    "normalize_label",
    "queue_summary",
    "utility_score",
]

__version__ = "0.3.0"
