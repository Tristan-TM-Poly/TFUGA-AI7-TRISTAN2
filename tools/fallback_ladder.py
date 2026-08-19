"""Fallback Ladder for Ω-AIT-CONTINUATION-ENGINE-T.

Always descend to the strongest safe action available.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class FallbackLevel(IntEnum):
    DIRECT_ACTION = 0
    REVERSIBLE_ACTION = 1
    DRAFT_PR = 2
    REPO_ARTIFACT = 3
    SIMULATION = 4
    TEST = 5
    OAK_REPORT = 6
    M_MINUS = 7
    QUARANTINE_NOTE = 8
    SUMMARY_NEXT_ACTION = 9


@dataclass(frozen=True)
class FallbackDecision:
    level: FallbackLevel
    label: str
    safe_artifact: str


def choose_fallback_level(
    *,
    direct_allowed: bool = False,
    reversible_allowed: bool = False,
    draft_pr_allowed: bool = True,
    repo_artifact_allowed: bool = True,
    simulation_allowed: bool = True,
    test_allowed: bool = True,
    oak_report_allowed: bool = True,
) -> FallbackDecision:
    if direct_allowed:
        level = FallbackLevel.DIRECT_ACTION
        artifact = "direct_action"
    elif reversible_allowed:
        level = FallbackLevel.REVERSIBLE_ACTION
        artifact = "reversible_action"
    elif draft_pr_allowed:
        level = FallbackLevel.DRAFT_PR
        artifact = "draft_pr"
    elif repo_artifact_allowed:
        level = FallbackLevel.REPO_ARTIFACT
        artifact = "repo_file"
    elif simulation_allowed:
        level = FallbackLevel.SIMULATION
        artifact = "simulation"
    elif test_allowed:
        level = FallbackLevel.TEST
        artifact = "test"
    elif oak_report_allowed:
        level = FallbackLevel.OAK_REPORT
        artifact = "oak_report"
    else:
        level = FallbackLevel.SUMMARY_NEXT_ACTION
        artifact = "next_action_note"

    return FallbackDecision(level=level, label=level.name.lower(), safe_artifact=artifact)
