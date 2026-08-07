"""Ω-PROBLEM-ATLAS-T∞ R0.10 streaming and SQLite scale layer."""

from .streaming import (
    CELL_SCHEMA,
    audit_streaming_atlas,
    ingest_jsonl,
    materialize_synthetic_campaign,
    query_portfolio,
)
from .compatibility_strict import ingest_r03_max, verify_r03_max_source

__all__ = [
    "CELL_SCHEMA",
    "audit_streaming_atlas",
    "ingest_jsonl",
    "ingest_r03_max",
    "materialize_synthetic_campaign",
    "query_portfolio",
    "verify_r03_max_source",
]

__version__ = "0.10.1"
