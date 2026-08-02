"""Ω-WIKI-T∞ / WikiForge-T multilingual evidence compiler.

R0.1 is a read-only, OAK-safe scaffold. It preserves provenance and does not
claim that Wikipedia text, citations, translations, or generated summaries are
verified truth.
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

__all__ = [
    "ArticleRecord",
    "ClaimRecord",
    "CompileResult",
    "MediaWikiClient",
    "SourceRecord",
    "WikiCompiler",
    "invariant_tokens",
]

__version__ = "0.1.0"
