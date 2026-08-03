"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.9."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audit import audit_promotion_gate
from .compiler import compile_promotion_gate as _compile_promotion_gate
from .model import BUNDLE_SCHEMA, DESTINATIONS, PROMOTION_STATUSES, stable_digest


def compile_promotion_gate(
    bundle_path: str | Path,
    output_dir: str | Path,
    *,
    clean: bool = True,
) -> dict[str, Any]:
    """Compile and remove filesystem-location noise from the public report."""
    output = Path(output_dir)
    _compile_promotion_gate(bundle_path, output, clean=clean)
    report_path = output / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report.pop("output_dir", None)
    report["report_digest"] = stable_digest(
        {key: value for key, value in report.items() if key != "report_digest"}
    )
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


__all__ = [
    "BUNDLE_SCHEMA",
    "DESTINATIONS",
    "PROMOTION_STATUSES",
    "audit_promotion_gate",
    "compile_promotion_gate",
]
