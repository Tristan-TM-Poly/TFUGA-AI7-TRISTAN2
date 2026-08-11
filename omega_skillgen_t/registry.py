from __future__ import annotations

from pathlib import Path
import json
from typing import Any

PROMOTION_STATES = (
    "DRAFT",
    "STATIC_PASS",
    "EVAL_READY",
    "TRUST_REVIEWED",
    "BEHAVIORAL_PASS",
    "PROMOTE_CANDIDATE",
    "PROMOTED",
)


def validate_transition(before: str, after: str, evidence: dict[str, Any]) -> list[str]:
    errors = []
    if before not in PROMOTION_STATES or after not in PROMOTION_STATES:
        return ["unknown promotion state"]
    if PROMOTION_STATES.index(after) < PROMOTION_STATES.index(before):
        if not evidence.get("rollback_reason"):
            errors.append("backward transition requires rollback_reason")
        return errors
    if PROMOTION_STATES.index(after) > PROMOTION_STATES.index(before) + 1:
        errors.append("promotion transitions may not skip evidence states")
    requirements = {
        "STATIC_PASS": ("lint_pass",),
        "EVAL_READY": ("eval_coverage_pass",),
        "TRUST_REVIEWED": ("trust_reviewed",),
        "BEHAVIORAL_PASS": ("behavioral_eval_pass",),
        "PROMOTE_CANDIDATE": ("regressions_pass", "rollback_available"),
        "PROMOTED": ("promotion_authorized",),
    }
    for key in requirements.get(after, ()):
        if not evidence.get(key):
            errors.append(f"missing evidence for {after}: {key}")
    return errors


def append_transition(ledger: str | Path, *, skill: str, version: str, before: str, after: str, evidence: dict[str, Any]) -> dict[str, Any]:
    errors = validate_transition(before, after, evidence)
    record = {
        "skill": skill,
        "version": version,
        "before": before,
        "after": after,
        "evidence": evidence,
        "accepted": not errors,
        "errors": errors,
    }
    path = Path(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
