from tools.safe_next_action_kernel import SafeActionType, choose_safe_next_action


def test_missing_test_routes_to_test():
    action = choose_safe_next_action(missing_test=True)
    assert action.action == SafeActionType.CREATE_TEST


def test_missing_safety_routes_to_oak_report():
    action = choose_safe_next_action(missing_safety=True)
    assert action.action == SafeActionType.CREATE_OAK_REPORT


def test_review_required_routes_to_review_packet():
    action = choose_safe_next_action(review_required=True)
    assert action.action == SafeActionType.CREATE_REVIEW_PACKET


def test_safe_default_routes_to_draft_pr():
    action = choose_safe_next_action()
    assert action.action == SafeActionType.CREATE_DRAFT_PR
