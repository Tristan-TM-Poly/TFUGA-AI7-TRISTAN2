from tools.ait_action_autonomy_gate import (
    AutonomyLevel,
    RiskDomain,
    TouchMode,
    decide_action_autonomy,
)


def test_medical_domain_is_no_touch_forbidden():
    decision = decide_action_autonomy([RiskDomain.MEDICAL])
    assert decision.mode == TouchMode.NO_TOUCH
    assert decision.level == AutonomyLevel.L10_FORBIDDEN
    assert "dose calculation" in decision.forbidden_actions


def test_irreversible_action_is_no_touch_forbidden():
    decision = decide_action_autonomy([RiskDomain.CODE], irreversible=True)
    assert decision.mode == TouchMode.NO_TOUCH
    assert decision.level == AutonomyLevel.L10_FORBIDDEN


def test_sensitive_domain_without_execution_is_dry_run():
    decision = decide_action_autonomy([RiskDomain.LEGAL])
    assert decision.mode == TouchMode.DRY_RUN
    assert decision.level == AutonomyLevel.L1_DRAFT_OR_SIMULATION


def test_sensitive_public_side_effect_is_one_touch():
    decision = decide_action_autonomy([RiskDomain.PUBLICATION], public_side_effect=True)
    assert decision.mode == TouchMode.ONE_TOUCH
    assert decision.level == AutonomyLevel.L6_MERGE_WITH_EXPLICIT_VALIDATION


def test_low_risk_github_can_reach_draft_pr():
    decision = decide_action_autonomy([RiskDomain.CODE, RiskDomain.GITHUB, RiskDomain.LOW_RISK_CREATIVE])
    assert decision.mode == TouchMode.ZERO_TOUCH
    assert decision.level == AutonomyLevel.L4_DRAFT_PR
    assert "open draft PR" in decision.allowed_actions


def test_unknown_domain_defaults_dry_run_explanation():
    decision = decide_action_autonomy([])
    assert decision.mode == TouchMode.DRY_RUN
    assert decision.level == AutonomyLevel.L0_EXPLANATION_ONLY
