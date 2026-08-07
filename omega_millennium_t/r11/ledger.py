"""Public API for Ω-PROBLEM-ATLAS-T∞ R0.11."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .hardening import install_hardening

install_hardening()

from . import audit as _audit_module
from . import compiler as _compiler_module
from .model import BUNDLE_SCHEMA, stable_digest

audit_competition_ledger = _audit_module.audit_competition_ledger
compile_competition_ledger = _compiler_module.compile_competition_ledger


def recommend_active_cycles(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    audit = audit_competition_ledger(output)
    if audit.get("valid") is not True:
        raise ValueError(f"competition ledger audit failed: {audit.get('errors')}")
    rows = json.loads((output / "recommendations.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    result = {
        "schema": "omega-competition-recommendations/11",
        "as_of": manifest["as_of"],
        "freshness_seconds": manifest["freshness_seconds"],
        "recommendation_timezone": manifest["recommendation_timezone"],
        "recommendation_count": len(rows),
        "rows": rows,
        "compiled_ledger_audit_digest": audit["audit_digest"],
        "freshness_is_relative_to_compiled_as_of": True,
        "requires_new_official_verification_after_as_of": True,
        "registration_performed": False,
        "submission_performed": False,
        "payment_performed": False,
        "winner_or_prize_guaranteed": False,
        "open_problem_status_inherited": False,
    }
    result["recommendation_report_digest"] = stable_digest(result)
    return result


__all__ = [
    "BUNDLE_SCHEMA",
    "audit_competition_ledger",
    "compile_competition_ledger",
    "recommend_active_cycles",
]
