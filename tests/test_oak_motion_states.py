from tools.oak_motion_states import OAKMotionState, describe_motion_state


def test_draft_pr_motion_creates_draft_pr_artifact():
    desc = describe_motion_state(OAKMotionState.M2_DRAFT_PR)
    assert desc.artifact == "draft_pr"


def test_safe_next_action_motion_still_creates_note():
    desc = describe_motion_state(OAKMotionState.M10_SAFE_NEXT_ACTION_ONLY)
    assert desc.artifact == "next_action_note"
