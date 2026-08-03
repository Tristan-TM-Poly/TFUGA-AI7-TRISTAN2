from __future__ import annotations

from copy import deepcopy
from typing import Any

SENSITIVE_KEYS = {"source_url", "normalized_url", "drive_file_id"}


def redact_manifest(manifest: list[dict[str, Any]], expose_drive_id: bool = False) -> list[dict[str, Any]]:
    """Return a public-safe manifest copy.

    By default, remove raw Drive URLs and raw Drive IDs while preserving hashes,
    counts, kinds, OAK verdicts, risk levels and scanner flags.
    """

    redacted = deepcopy(manifest)
    for row in redacted:
        for key in ("source_url", "normalized_url"):
            if key in row:
                row[key] = "REDACTED"
        if not expose_drive_id and "drive_file_id" in row:
            row["drive_file_id"] = "REDACTED"
    return redacted


def redact_oak_report(report: dict[str, Any]) -> dict[str, Any]:
    safe = deepcopy(report)
    for key in ("unknown_links", "real_drive_links", "private_urls"):
        if key in safe:
            safe[key] = ["REDACTED" for _ in safe.get(key, [])]
    return safe
