from omega_action_ext_t.green_builder import PRGreenState
from omega_action_ext_t.zero_manual_forge import (
    ForgeDecision,
    RepairTactic,
    plan_zero_manual_forge,
    render_zero_manual_report,
)


def test_clean_non_draft_pr_can_merge_with_expected_sha():
    state = PRGreenState(
        number=9,
        title="clean",
        draft=False,
        mergeable=True,
        checks_state="success",
        metadata={"head_sha": "abc"},
    )

    plan = plan_zero_manual_forge(state)

    assert plan.can_merge_now
    assert plan.decision == ForgeDecision.MERGE_WHEN_CLEAN
    assert RepairTactic.MERGE_WITH_EXPECTED_SHA in plan.tactics


def test_draft_is_enriched_but_never_marked_ready():
    state = PRGreenState(
        number=165,
        title="draft external action kernel",
        draft=True,
        mergeable=True,
        checks_state="success",
        safety_flags=("external_action_kernel",),
    )

    plan = plan_zero_manual_forge(state)
    report = render_zero_manual_report(plan)

    assert plan.decision == ForgeDecision.SKIP_DRAFT
    assert RepairTactic.UPDATE_MACHINE_REPORT in plan.tactics
    assert "never marked ready automatically" in report
    assert "higher-impact actions require stronger gates" in report


def test_conflict_uses_preserve_and_synthesize_not_manual_request():
    state = PRGreenState(
        number=9,
        title="canon conflict",
        draft=False,
        mergeable=False,
        checks_state="success",
        has_conflicts=True,
    )

    plan = plan_zero_manual_forge(state)

    assert plan.decision == ForgeDecision.PRESERVE_AND_SYNTHESIZE
    assert RepairTactic.PRESERVE_BRANCH_VERSION in plan.tactics
    assert RepairTactic.REALIGN_CANONICAL_PATH in plan.tactics
    assert RepairTactic.SYNTHESIZE_CANON_ARTIFACT in plan.tactics
    assert plan.failure_memory[0].failure_class == "merge_conflict"


def test_failing_check_routes_to_autonomous_repair():
    state = PRGreenState(
        number=45,
        title="failing CLI",
        draft=False,
        mergeable=True,
        checks_state="failure",
    )

    plan = plan_zero_manual_forge(state)

    assert plan.decision == ForgeDecision.AUTONOMOUS_REPAIR
    assert RepairTactic.REPO_ROOT_IMPORT_BOOTSTRAP in plan.tactics
    assert RepairTactic.ADD_REGRESSION_TEST in plan.tactics
    assert plan.failure_memory[0].failure_class == "failing_check"


def test_pending_checks_wait_not_merge():
    state = PRGreenState(
        number=99,
        title="queued",
        draft=False,
        mergeable=True,
        checks_state="in_progress",
    )

    plan = plan_zero_manual_forge(state)

    assert plan.decision == ForgeDecision.WAIT_FOR_CHECKS
    assert RepairTactic.RERUN_OR_WAIT_CHECKS in plan.tactics
    assert not plan.can_merge_now


def test_report_contains_oak_zero_manual_rule():
    state = PRGreenState(
        number=12,
        title="ambiguous",
        draft=False,
        mergeable=True,
        checks_state="unknown",
    )

    report = render_zero_manual_report(plan_zero_manual_forge(state))

    assert "Zero-Manual PR Forge report" in report
    assert "absence of evidence is not green evidence" in report
    assert "never unsafe automation" in report
