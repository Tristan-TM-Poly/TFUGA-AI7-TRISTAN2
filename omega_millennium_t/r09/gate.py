"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.9."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import audit as _audit_module
from . import compiler as _compiler_module
from .hardening import evaluate_request_hardened
from .model import BUNDLE_SCHEMA, DESTINATIONS, PROMOTION_STATUSES, stable_digest

_BASE_EVALUATOR = _compiler_module.evaluate_request


def _hardened_evaluator(request):
    return evaluate_request_hardened(request, _BASE_EVALUATOR)


# Patch both compilation and replay-audit references before exposing the API.
_compiler_module.evaluate_request = _hardened_evaluator
_audit_module.evaluate_request = _hardened_evaluator

_compile_promotion_gate = _compiler_module.compile_promotion_gate
audit_promotion_gate = _audit_module.audit_promotion_gate


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
