"""Ω-PROBLEM-ATLAS-T∞ R0.4 source ingestion layer.

Offline, revision-pinned adapters compile source snapshots into R0.3-compatible
imports with dated status receipts and fail-closed quarantine.  No external
retrieval, current-status certification, theorem proof or solution is claimed.
"""

from .source_adapters import (
    ALLOWED_OBSERVED_STATUSES,
    ALLOWED_VERIFICATION_BASES,
    MANIFEST_SCHEMA,
    REPORT_SCHEMA,
    SNAPSHOT_SCHEMA,
    SOURCE_POLICIES,
    QuarantineRecord,
    SourceSnapshot,
    StatusReceipt,
    audit_source_bundle,
    compile_source_bundle,
    load_source_snapshot,
)

__all__ = [
    "ALLOWED_OBSERVED_STATUSES",
    "ALLOWED_VERIFICATION_BASES",
    "MANIFEST_SCHEMA",
    "REPORT_SCHEMA",
    "SNAPSHOT_SCHEMA",
    "SOURCE_POLICIES",
    "QuarantineRecord",
    "SourceSnapshot",
    "StatusReceipt",
    "audit_source_bundle",
    "compile_source_bundle",
    "load_source_snapshot",
]

__version__ = "0.4.0"
