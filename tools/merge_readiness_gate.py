"""Merge Readiness Gate for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Classifies readiness states. Planning only; does not change PR state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReadinessState(StrEnum):
    DRAFT_HYPERSTRUCTURE = "draft_hyperstructure"
    AUDIT_READY = "audit_ready"
    IMPORT_READY = "import_ready"
    REVIEW_READY = "review_ready"
    SPLIT_READY = "split_ready"
    MERGE_READY = "merge_ready"


@dataclass(frozen=True)
class ReadinessDecision:
    state: ReadinessState
    missing: tuple[str, ...]
    next_step: str


def assess_merge_readiness(
    *,
    import_smoke: bool = False,
    layer_index: bool = False,
    connector_aliases: bool = False,
    ci_path_known: bool = False,
    micro_pr_plan: bool = False,
    oak_reports: bool = False,
) -> ReadinessDecision:
    missing = []
    if not import_smoke:
        missing.append("import_smoke")
    if not layer_index:
        missing.append("layer_index")
    if not connector_aliases:
        missing.append("connector_aliases")
    if not ci_path_known:
        missing.append("ci_path_known")
    if not micro_pr_plan:
        missing.append("micro_pr_plan")
    if not oak_reports:
        missing.append("oak_reports")

    if missing:
        return ReadinessDecision(ReadinessState.AUDIT_READY, tuple(missing), "complete missing readiness artifacts")
    return ReadinessDecision(ReadinessState.REVIEW_READY, (), "request review before any merge decision")
