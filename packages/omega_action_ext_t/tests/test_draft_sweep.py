from omega_action_ext_t.draft_sweep import (
    DraftBlocker,
    DraftSignal,
    DraftSweepInput,
    infer_signals_from_files,
    plan_draft_sweep,
    render_draft_sweep_report,
)
from omega_action_ext_t.green_builder import PRGreenState


def test_infer_signals_from_files_for_action_kernel():
    state = PRGreenState(
        number=165,
        title="external action kernel",
        draft=True,
        mergeable=True,
        checks_state="success",
    )
    files = (
        "packages/omega_action_ext_t/docs/ZERO_MANUAL_PR_FORGE.md",
        "packages/omega_action_ext_t/omega_action_ext_t/policy.py",
        "packages/omega_action_ext_t/omega_action_ext_t/connectors/github_dryrun.py",
        "packages/omega_action_ext_t/omega_action_ext_t/rollback.py",
        "packages/omega_action_ext_t/omega_action_ext_t/approval_queue.py",
        "packages/omega_action_ext_t/omega_action_ext_t/ledger.py",
        "packages/omega_action_ext_t/omega_action_ext_t/incident_codex.py",
        "packages/omega_action_ext_t/omega_action_ext_t/leak_scan.py",
        "packages/omega_action_ext_t/tests/test_oak_gate.py",
    )

    signals = infer_signals_from_files(state, files)

    assert signals[DraftSignal.HAS_TESTS]
    assert signals[DraftSignal.HAS_DOCS]
    assert signals[DraftSignal.HAS_OAK_GUARDRAILS]
    assert signals[DraftSignal.HAS_DRY_RUN_DEFAULT]
    assert signals[DraftSignal.HAS_ROLLBACK_OR_COMPENSATION]
    assert signals[DraftSignal.HAS_APPROVAL_QUEUE]
    assert signals[DraftSignal.HAS_PROOF_LEDGER]
    assert signals[DraftSignal.HAS_M_MINUS_MEMORY]
    assert signals[DraftSignal.HAS_LEAK_SCAN]
    assert signals[DraftSignal.HAS_GREEN_CHECKS]
    assert signals[DraftSignal.IS_MERGEABLE]


def test_draft_sweep_never_promotes_draft_automatically():
    state = PRGreenState(
        number=165,
        title="external action kernel",
        draft=True,
        mergeable=True,
        checks_state="success",
    )
    plan = plan_draft_sweep(
        DraftSweepInput(
            state=state,
            changed_files=(
                "docs/README.md",
                "packages/pkg/policy.py",
                "packages/pkg/connectors/github_dryrun.py",
                "packages/pkg/rollback.py",
                "packages/pkg/approval_queue.py",
                "packages/pkg/ledger.py",
                "packages/pkg/incident_codex.py",
                "packages/pkg/leak_scan.py",
                "tests/test_policy.py",
            ),
        )
    )

    assert DraftBlocker.STILL_DRAFT in plan.blockers
    assert plan.is_ready_candidate
    assert all("marking draft ready" in memory.unsafe_shortcut for memory in plan.failure_memory)


def test_missing_safety_layers_generate_autonomous_actions():
    state = PRGreenState(
        number=149,
        title="zeta mandel draft",
        draft=True,
        mergeable=True,
        checks_state="unknown",
        safety_flags=("math_claims",),
    )
    plan = plan_draft_sweep(DraftSweepInput(state=state, changed_files=("docs/theory.md",)))

    assert DraftBlocker.MISSING_TESTS in plan.blockers
    assert DraftBlocker.MISSING_OAK_GUARDRAILS in plan.blockers
    assert DraftBlocker.CHECKS_NOT_GREEN in plan.blockers
    assert DraftBlocker.SAFETY_SENSITIVE in plan.blockers
    assert any("tests" in action for action in plan.next_autonomous_actions)
    assert any("guardrails" in action for action in plan.next_autonomous_actions)


def test_report_is_machine_readable_and_oak_safe():
    state = PRGreenState(
        number=47,
        title="digest draft",
        draft=True,
        mergeable=False,
        checks_state="failure",
    )
    plan = plan_draft_sweep(DraftSweepInput(state=state, changed_files=()))
    report = render_draft_sweep_report(plan)

    assert "Draft Sweep report" in report
    assert "Ready candidate" in report
    assert "draft promotion is not automatic" in report
    assert "not_mergeable" in report
