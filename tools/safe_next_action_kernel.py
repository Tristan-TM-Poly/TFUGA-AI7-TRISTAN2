"""SafeNextAction Kernel for Ω-AIT-CONTINUATION-ENGINE-T.

Every state should produce a safe next move. This module recommends artifacts and
next actions only; it does not execute external effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SafeActionType(StrEnum):
    CREATE_DOC = "create_doc"
    CREATE_SCHEMA = "create_schema"
    CREATE_TOOL = "create_tool"
    CREATE_TEST = "create_test"
    CREATE_BENCHMARK = "create_benchmark"
    CREATE_OAK_REPORT = "create_oak_report"
    CREATE_M_MINUS = "create_m_minus"
    CREATE_DRAFT_PR = "create_draft_pr"
    SIMULATE = "simulate"
    CREATE_REVIEW_PACKET = "create_review_packet"
    CREATE_QUARANTINE_NOTE = "create_quarantine_note"
    CREATE_NEXT_ACTION_NOTE = "create_next_action_note"


@dataclass(frozen=True)
class SafeNextAction:
    action: SafeActionType
    reason: str
    artifact_path_hint: str
    next_step: str


def choose_safe_next_action(
    *,
    missing_proof: bool = False,
    missing_test: bool = False,
    missing_data: bool = False,
    missing_benchmark: bool = False,
    missing_source: bool = False,
    missing_safety: bool = False,
    missing_rollback: bool = False,
    unclear_claim: bool = False,
    review_required: bool = False,
) -> SafeNextAction:
    if review_required:
        return SafeNextAction(SafeActionType.CREATE_REVIEW_PACKET, "Review threshold reached.", "docs/review_packets/", "Prepare review packet and safe options.")
    if missing_safety:
        return SafeNextAction(SafeActionType.CREATE_OAK_REPORT, "Safety boundary is not clear.", "docs/oak_reports/", "Write OAK report before implementation.")
    if missing_rollback:
        return SafeNextAction(SafeActionType.CREATE_DOC, "Rollback plan is missing.", "docs/rollback_plans/", "Create rollback or compensation plan.")
    if unclear_claim:
        return SafeNextAction(SafeActionType.CREATE_DOC, "Claim lacks clarity.", "docs/reality_anchors/", "Create RealityAnchor and scope note.")
    if missing_test:
        return SafeNextAction(SafeActionType.CREATE_TEST, "Tests are missing.", "tests/", "Create minimal regression or safety test.")
    if missing_benchmark:
        return SafeNextAction(SafeActionType.CREATE_BENCHMARK, "Benchmark is missing.", "benchmarks/", "Create toy benchmark or simple baseline.")
    if missing_data:
        return SafeNextAction(SafeActionType.SIMULATE, "Data is missing.", "examples/fixtures/", "Create synthetic fixture or simulation plan.")
    if missing_source:
        return SafeNextAction(SafeActionType.CREATE_DOC, "Source status is weak.", "docs/source_notes/", "Create source request or source status note.")
    if missing_proof:
        return SafeNextAction(SafeActionType.CREATE_TEST, "Proof is missing.", "tests/", "Create falsification test or toy example.")
    return SafeNextAction(SafeActionType.CREATE_DRAFT_PR, "State is safe enough for reversible progress.", "pull_request", "Create or update draft PR with tests and report.")
