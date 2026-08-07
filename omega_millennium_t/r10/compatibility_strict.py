"""Strict R0.3 MAX compatibility entry point for R0.10."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from omega_millennium_t.r03 import audit_max_output

from . import compatibility as _base
from .model import RuntimePolicy, stable_digest, write_json
from .store import AtlasStore

_REQUIRED_ARTIFACTS = {
    "sources.jsonl",
    "problems.jsonl",
    "research_targets.jsonl",
    "research_cells.jsonl",
    "hyperedges.jsonl",
    "methods.jsonl",
    "portfolio.json",
}
_BASE_VERIFY = _base.verify_r03_max_source
_BASE_INGEST = _base.ingest_r03_max


def verify_r03_max_source(source_dir: str | Path) -> dict[str, Any]:
    receipt = dict(_BASE_VERIFY(source_dir))
    blockers = list(receipt.get("blockers", []))
    artifact_paths = [str(item.get("path", "")) for item in receipt.get("artifacts", [])]
    if len(artifact_paths) != len(set(artifact_paths)):
        blockers.append("r03_duplicate_artifact_receipts")
    missing = sorted(_REQUIRED_ARTIFACTS - set(artifact_paths))
    extra = sorted(set(artifact_paths) - _REQUIRED_ARTIFACTS)
    if missing:
        blockers.append(f"r03_required_artifacts_missing:{','.join(missing)}")
    if extra:
        blockers.append(f"r03_unexpected_artifacts:{','.join(extra)}")
    try:
        native_audit = audit_max_output(source_dir)
    except Exception as exc:
        blockers.append(f"r03_native_audit_error:{type(exc).__name__}:{exc}")
    else:
        if native_audit.get("valid") is not True:
            blockers.append("r03_native_audit_invalid")
            blockers.extend(
                f"r03_native:{item}" for item in native_audit.get("errors", [])
            )
    receipt["blockers"] = sorted(set(blockers))
    receipt["valid"] = not receipt["blockers"]
    receipt["receipt_digest"] = stable_digest(
        {key: value for key, value in receipt.items() if key != "receipt_digest"}
    )
    return receipt


# The existing streaming importer resolves this global at call time.
_base.verify_r03_max_source = verify_r03_max_source


def ingest_r03_max(
    source_dir: str | Path,
    output_dir: str | Path,
    *,
    policy: RuntimePolicy | None = None,
    resume: bool = False,
    max_items: int | None = None,
    clean: bool = True,
) -> dict[str, Any]:
    runtime = policy or RuntimePolicy()
    output = Path(output_dir)
    report = _BASE_INGEST(
        source_dir,
        output,
        policy=runtime,
        resume=resume,
        max_items=max_items,
        clean=clean,
    )
    with AtlasStore(output / "atlas.sqlite3", runtime) as store:
        report["database_bytes"] = store.database_bytes()
    report["report_digest"] = stable_digest(
        {key: value for key, value in report.items() if key != "report_digest"}
    )
    write_json(output / "report.json", report)
    return report


__all__ = ["ingest_r03_max", "verify_r03_max_source"]
