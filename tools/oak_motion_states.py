"""OAK Motion States for Ω-AIT-CONTINUATION-ENGINE-T.

Even the lowest motion state produces a safe artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class OAKMotionState(IntEnum):
    M0_DIRECT_CREATE = 0
    M1_REVERSIBLE_BUILD = 1
    M2_DRAFT_PR = 2
    M3_SIMULATION = 3
    M4_TEST_GENERATION = 4
    M5_OAK_REPORT = 5
    M6_REVIEW_PACKET = 6
    M7_QUARANTINE_ANALYSIS = 7
    M8_M_MINUS_LEARNING = 8
    M9_CANON_UPDATE = 9
    M10_SAFE_NEXT_ACTION_ONLY = 10


@dataclass(frozen=True)
class MotionStateDescription:
    state: OAKMotionState
    label: str
    artifact: str


def describe_motion_state(state: OAKMotionState) -> MotionStateDescription:
    artifacts = {
        OAKMotionState.M0_DIRECT_CREATE: "created_artifact",
        OAKMotionState.M1_REVERSIBLE_BUILD: "reversible_build_plan",
        OAKMotionState.M2_DRAFT_PR: "draft_pr",
        OAKMotionState.M3_SIMULATION: "simulation",
        OAKMotionState.M4_TEST_GENERATION: "test",
        OAKMotionState.M5_OAK_REPORT: "oak_report",
        OAKMotionState.M6_REVIEW_PACKET: "review_packet",
        OAKMotionState.M7_QUARANTINE_ANALYSIS: "quarantine_note",
        OAKMotionState.M8_M_MINUS_LEARNING: "m_minus",
        OAKMotionState.M9_CANON_UPDATE: "canon_update_note",
        OAKMotionState.M10_SAFE_NEXT_ACTION_ONLY: "next_action_note",
    }
    return MotionStateDescription(state=state, label=state.name.lower(), artifact=artifacts[state])
