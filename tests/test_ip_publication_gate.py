from tools.ip_publication_gate import ReleaseStatus, decide_release_status


def test_sensitive_content_is_held():
    decision = decide_release_status(sensitive_content=True)
    assert decision.status == ReleaseStatus.HOLD


def test_public_goal_without_tests_needs_review():
    decision = decide_release_status(public_goal=True, has_sources=True, has_tests=False)
    assert decision.status == ReleaseStatus.NEEDS_REVIEW


def test_public_goal_with_sources_and_tests_is_candidate():
    decision = decide_release_status(public_goal=True, has_sources=True, has_tests=True)
    assert decision.status == ReleaseStatus.OPEN_RELEASE_CANDIDATE
