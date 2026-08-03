from tools.fallback_ladder import FallbackLevel, choose_fallback_level


def test_direct_action_when_allowed():
    decision = choose_fallback_level(direct_allowed=True)
    assert decision.level == FallbackLevel.DIRECT_ACTION


def test_draft_pr_default_when_direct_not_allowed():
    decision = choose_fallback_level()
    assert decision.level == FallbackLevel.DRAFT_PR


def test_simulation_when_pr_and_repo_not_allowed():
    decision = choose_fallback_level(draft_pr_allowed=False, repo_artifact_allowed=False)
    assert decision.level == FallbackLevel.SIMULATION


def test_summary_when_all_main_options_off():
    decision = choose_fallback_level(
        draft_pr_allowed=False,
        repo_artifact_allowed=False,
        simulation_allowed=False,
        test_allowed=False,
        oak_report_allowed=False,
    )
    assert decision.level == FallbackLevel.SUMMARY_NEXT_ACTION
