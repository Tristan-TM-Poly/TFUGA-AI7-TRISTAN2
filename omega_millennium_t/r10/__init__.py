"""Ω-PROBLEM-ATLAS-T∞ R0.10 streaming and SQLite scale layer."""

from .streaming import (
    CELL_SCHEMA,
    audit_streaming_atlas,
    ingest_jsonl,
    materialize_synthetic_campaign,
    query_portfolio,
)

__all__ = [
    "CELL_SCHEMA",
    "audit_streaming_atlas",
    "ingest_jsonl",
    "materialize_synthetic_campaign",
    "query_portfolio",
]

__version__ = "0.10.0"
