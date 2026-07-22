"""Self-Propelling Loop for Ω-AIT-CONTINUATION-ENGINE-T.

Converts a goal into a traceable continuation packet: safe action, artifact,
audit note, and next goal. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.autonomous_priority_engine import PriorityCandidate, choose_priority
from tools.oak_motion_states import OAKMotionState, describe_motion_state
from tools.safe_next_action_kernel import SafeNextAction, choose_safe_next_action


@dataclass(frozen=True)
class ContinuationCyclePacket:
    goal: str
    current_state: str
    safe_action: SafeNextAction
    motion_state: OAKMotionState
    artifact_created: str
    audit_note: str
    next_goal: str


def run_continuation_cycle(
    *,
    goal: str,
    current_state: str = "new_goal",
    missing_test: bool = False,
    missing_benchmark: bool = False,
    missing_safety: bool = False,
    review_required: bool = False,
) -> ContinuationCyclePacket:
    action = choose_safe_next_action(
        missing_test=missing_test,
        missing_benchmark=missing_benchmark,
        missing_safety=missing_safety,
        review_required=review_required,
    )

    candidates = (
        PriorityCandidate(action.action.value, impact=3, reversibility=4, testability=3, canon_gain=3, risk=1 if not review_required else 5),
        PriorityCandidate("create_audit_note", impact=1, reversibility=5, testability=1, canon_gain=2),
    )
    priority = choose_priority(candidates)

    if review_required:
        motion = OAKMotionState.M6_REVIEW_PACKET
    elif missing_safety:
        motion = OAKMotionState.M5_OAK_REPORT
    elif missing_test:
        motion = OAKMotionState.M4_TEST_GENERATION
    elif missing_benchmark:
        motion = OAKMotionState.M4_TEST_GENERATION
    else:
        motion = OAKMotionState.M2_DRAFT_PR

    motion_desc = describe_motion_state(motion)
    return ContinuationCyclePacket(
        goal=goal,
        current_state=current_state,
        safe_action=action,
        motion_state=motion,
        artifact_created=motion_desc.artifact,
        audit_note=f"Chosen priority: {priority.chosen.name} with score {priority.chosen.score}",
        next_goal=f"Continue from {action.next_step}",
    )
