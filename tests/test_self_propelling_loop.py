from tools.oak_motion_states import OAKMotionState
from tools.self_propelling_loop import run_continuation_cycle


def test_normal_cycle_routes_to_draft_pr_motion():
    packet = run_continuation_cycle(goal="continue safely")
    assert packet.motion_state == OAKMotionState.M2_DRAFT_PR
    assert packet.artifact_created == "draft_pr"


def test_missing_test_routes_to_test_generation():
    packet = run_continuation_cycle(goal="add tests", missing_test=True)
    assert packet.motion_state == OAKMotionState.M4_TEST_GENERATION


def test_missing_safety_routes_to_oak_report():
    packet = run_continuation_cycle(goal="add safety", missing_safety=True)
    assert packet.motion_state == OAKMotionState.M5_OAK_REPORT


def test_review_required_routes_to_review_packet():
    packet = run_continuation_cycle(goal="review scoped", review_required=True)
    assert packet.motion_state == OAKMotionState.M6_REVIEW_PACKET
