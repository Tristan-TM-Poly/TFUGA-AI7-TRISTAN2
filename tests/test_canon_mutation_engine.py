from tools.canon_mutation_engine import MutationDecision, MutationType, plan_canon_mutation


def test_empty_target_rejected():
    plan = plan_canon_mutation(MutationType.ADD, ())
    assert plan.decision == MutationDecision.REJECT


def test_high_stakes_quarantines():
    plan = plan_canon_mutation(MutationType.ADD, ("node",), high_stakes=True)
    assert plan.decision == MutationDecision.QUARANTINE
    assert "qualified_review" in plan.required_gates


def test_missing_tests_for_upgrade_sandbox():
    plan = plan_canon_mutation(MutationType.UPGRADE, ("node",), missing_tests=True)
    assert plan.decision == MutationDecision.SANDBOX
    assert "tests" in plan.required_gates


def test_low_risk_goes_to_draft_pr():
    plan = plan_canon_mutation(MutationType.ADD, ("node",))
    assert plan.decision == MutationDecision.DRAFT_PR
