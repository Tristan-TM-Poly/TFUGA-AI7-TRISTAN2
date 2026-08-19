"""Stability Assessor for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Scores draft architecture maturity. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class StabilityLevel(IntEnum):
    S0_LOW = 0
    S1_DRAFT = 1
    S2_LOADABLE = 2
    S3_CHECKED = 3
    S4_INDEXED = 4
    S5_PACKAGE_READY = 5
    S6_REWORK_READY = 6
    S7_REVIEW_READY = 7


@dataclass(frozen=True)
class StabilityReport:
    score: int
    level: StabilityLevel
    next_step: str


def assess_stability(
    *,
    load_checks: int = 0,
    tests: int = 0,
    docs: int = 0,
    schemas: int = 0,
    reports: int = 0,
    traceability: int = 0,
    orphan_count: int = 0,
    issue_count: int = 0,
) -> StabilityReport:
    score = load_checks + tests + docs + schemas + reports + traceability - orphan_count - issue_count
    if score >= 24:
        level = StabilityLevel.S7_REVIEW_READY
    elif score >= 20:
        level = StabilityLevel.S6_REWORK_READY
    elif score >= 16:
        level = StabilityLevel.S5_PACKAGE_READY
    elif score >= 12:
        level = StabilityLevel.S4_INDEXED
    elif score >= 8:
        level = StabilityLevel.S3_CHECKED
    elif score >= 4:
        level = StabilityLevel.S2_LOADABLE
    elif score >= 1:
        level = StabilityLevel.S1_DRAFT
    else:
        level = StabilityLevel.S0_LOW
    next_steps = {
        StabilityLevel.S0_LOW: "add docs and checks",
        StabilityLevel.S1_DRAFT: "add load checks",
        StabilityLevel.S2_LOADABLE: "add focused tests",
        StabilityLevel.S3_CHECKED: "add architecture index",
        StabilityLevel.S4_INDEXED: "prepare package boundary",
        StabilityLevel.S5_PACKAGE_READY: "prepare rework plan",
        StabilityLevel.S6_REWORK_READY: "request review before status change",
        StabilityLevel.S7_REVIEW_READY: "maintain checks and gates",
    }
    return StabilityReport(score, level, next_steps[level])
