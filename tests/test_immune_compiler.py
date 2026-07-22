from tools.ait_action_autonomy_gate import RiskDomain, TouchMode
from tools.immune_compiler import OakStatus, RollbackProof, compile_action_immune_packet


def test_low_risk_action_with_rollback_can_pass():
    packet = compile_action_immune_packet(
        goal="Create a draft PR for documentation",
        expected_benefit="Improves canon structure",
        risk_domains=(RiskDomain.CODE, RiskDomain.GITHUB, RiskDomain.LOW_RISK_CREATIVE),
        action_text="Create branch and draft PR with tests",
        rollback=RollbackProof(exists=True, tested=True, summary="Close PR and delete branch if needed."),
    )
    assert packet.oak_status == OakStatus.PASS
    assert packet.autonomy_decision.mode == TouchMode.ZERO_TOUCH
    assert not packet.risk_debt.blocks_zero_touch


def test_medical_action_routes_no_touch():
    packet = compile_action_immune_packet(
        goal="Handle medical dose question",
        expected_benefit="Safety routing",
        risk_domains=(RiskDomain.MEDICAL,),
        action_text="medical dose question",
        rollback=RollbackProof(exists=False, tested=False),
    )
    assert packet.oak_status == OakStatus.NO_TOUCH
    assert packet.autonomy_decision.mode == TouchMode.NO_TOUCH
    assert "IA ≠ médecin" in packet.m_minus_matches


def test_canary_triggers_slow_max():
    packet = compile_action_immune_packet(
        goal="Publish guaranteed result",
        expected_benefit="Fast communication",
        risk_domains=(RiskDomain.CODE,),
        action_text="This is guaranteed and zero risk, no tests needed",
        rollback=RollbackProof(exists=True, tested=True),
        missing_tests=True,
    )
    assert packet.oak_status == OakStatus.SLOW_MAX
    assert "overconfidence_guarantee" in packet.canaries
    assert "overconfidence_zero_risk" in packet.canaries


def test_sensitive_data_requires_review():
    packet = compile_action_immune_packet(
        goal="Prepare private data publication",
        expected_benefit="Share results",
        risk_domains=(RiskDomain.PRIVACY, RiskDomain.PUBLICATION),
        action_text="publish sensitive data",
        sensitive_data_unclear=True,
        irreversible_or_public_side_effect=True,
    )
    assert packet.oak_status in {OakStatus.NO_TOUCH, OakStatus.ONE_TOUCH}
    assert packet.privacy_status == "needs_review"
    assert packet.risk_debt.blocks_zero_touch
