from omega_action_ext_t.green_builder import (
    BuildAction,
    PRBlocker,
    PRGreenState,
    plan_build_to_green,
    render_plan_markdown,
)


def test_clean_pr_can_merge_now():
    state = PRGreenState(
        number=2,
        title="clean",
        draft=False,
        mergeable=True,
        checks_state="clean",
    )

    plan = plan_build_to_green(state)

    assert plan.can_merge_now
    assert plan.blockers == ()
    assert plan.steps[-1].action == BuildAction.MERGE_WHEN_CLEAN


def test_draft_pr_is_manual_required_and_not_marked_ready():
    state = PRGreenState(
        number=165,
        title="draft automation kernel",
        draft=True,
        mergeable=True,
        checks_state="clean",
    )

    plan = plan_build_to_green(state)

    assert plan.decision == "manual_required"
    assert PRBlocker.DRAFT in plan.blockers
    assert any(step.action == BuildAction.SKIP for step in plan.steps)


def test_conflicted_pr_requests_manual_resolution():
    state = PRGreenState(
        number=9,
        title="conflicted",
        draft=False,
        mergeable=False,
        checks_state="success",
        has_conflicts=True,
    )

    plan = plan_build_to_green(state)

    assert plan.decision == "manual_required"
    assert PRBlocker.CONFLICT in plan.blockers
    assert any(step.action == BuildAction.REQUEST_MANUAL_RESOLUTION for step in plan.steps)
    assert any(step.action == BuildAction.ADD_REPAIR_REPORT for step in plan.steps)


def test_failing_pr_gets_additive_enrichment_steps():
    state = PRGreenState(
        number=45,
        title="failing checks",
        draft=False,
        mergeable=True,
        checks_state="failure",
        changed_files=("sage_tristan/daily_omega.py", "tests/test_daily_omega.py"),
    )

    plan = plan_build_to_green(state)

    assert plan.can_auto_enrich
    assert PRBlocker.FAILING_CHECK in plan.blockers
    actions = {step.action for step in plan.steps}
    assert BuildAction.ADD_TEST in actions
    assert BuildAction.ADD_VALIDATOR in actions


def test_missing_or_ambiguous_checks_add_guardrail_not_merge():
    state = PRGreenState(
        number=99,
        title="ambiguous",
        draft=False,
        mergeable=True,
        checks_state="unknown",
    )

    plan = plan_build_to_green(state)
    markdown = render_plan_markdown(plan)

    assert plan.decision == "auto_enrich"
    assert PRBlocker.AMBIGUOUS_STATUS in plan.blockers
    assert any(step.action == BuildAction.ADD_GUARDRAIL for step in plan.steps)
    assert "never weaken checks" in markdown
