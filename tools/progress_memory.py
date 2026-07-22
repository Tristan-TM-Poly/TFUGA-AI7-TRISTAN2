"""Progress Memory for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

No progress without trace. No trace without next action.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressTrace:
    what_changed: str
    why: str
    risk: str
    evidence: str
    check: str
    residue: str
    learning_note: str
    next_safe_action: str


def create_progress_trace(
    *,
    what_changed: str,
    why: str,
    next_safe_action: str,
    risk: str = "low_draft_only",
    evidence: str = "internal_artifact",
    check: str = "pending_test_or_review",
    residue: str = "none_recorded",
    learning_note: str = "none",
) -> ProgressTrace:
    return ProgressTrace(what_changed, why, risk, evidence, check, residue, learning_note, next_safe_action)
