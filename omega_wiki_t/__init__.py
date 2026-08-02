"""Ω-WIKI-T∞ / WikiForge-T multilingual evidence and theory compiler.

R0.2 preserves provenance across Wikipedia extraction and repository-theory
absorption. Generated claims, rankings, and hypergraph relations remain OAK
candidates rather than verified truth or scientific certification.
"""

from .core import (
    ArticleRecord,
    ClaimRecord,
    CompileResult,
    MediaWikiClient,
    SourceRecord,
    WikiCompiler,
    invariant_tokens,
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
    "ArticleRecord",
    "ClaimRecord",
    "CompileResult",
    "KnowledgeHyperedge",
    "MediaWikiClient",
    "SourceRecord",
    "TheoryHypergraph",
    "TheoryHypergraphBuilder",
    "TheoryNode",
    "WikiCompiler",
    "invariant_tokens",
    "node_key",
    "normalize_label",
    "utility_score",
]

__version__ = "0.2.0"
