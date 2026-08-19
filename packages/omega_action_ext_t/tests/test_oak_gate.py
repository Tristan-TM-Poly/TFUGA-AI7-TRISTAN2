from omega_action_ext_t import ActionDNA, Decision, OAKGate, RiskTensor


def test_unapproved_send_email_becomes_draft_only():
    action = ActionDNA(
        name="Professor outreach",
        system="gmail",
        action_type="send_email",
        touches_humans=True,
        touches_ip=True,
        approved=False,
        risk=RiskTensor(ip=2, reputation=2, privacy=1),
    )
    report = OAKGate().dry_run(action)
    assert report.decision == Decision.ALLOW_DRAFT
    assert "explicit_send_confirmation" in report.required_approvals


def test_public_ip_action_requires_review():
    action = ActionDNA(
        name="Public release",
        system="github",
        action_type="publish_release",
        public=True,
        touches_ip=True,
        approved=False,
        risk=RiskTensor(ip=3, reputation=2),
    )
    report = OAKGate().dry_run(action)
    assert report.decision == Decision.NEEDS_APPROVAL
    assert "ip_review" in report.required_approvals


def test_critical_risk_requires_expert():
    action = ActionDNA(
        name="Critical physical action",
        system="lab",
        action_type="instrument_run",
        touches_safety=True,
        risk=RiskTensor(safety=5),
    )
    report = OAKGate().dry_run(action)
    assert report.decision == Decision.REQUIRE_EXPERT


def test_low_risk_reversible_action_can_auto():
    action = ActionDNA(
        name="Create local draft file",
        system="local_files",
        action_type="create_file",
        reversible=True,
        rollback="delete_file",
        risk=RiskTensor(irreversibility=1),
    )
    report = OAKGate().dry_run(action)
    assert report.decision == Decision.ALLOW_AUTO


def test_destructive_action_without_rollback_blocks():
    action = ActionDNA(
        name="Delete important folder",
        system="drive",
        action_type="delete_folder",
        destructive=True,
        reversible=False,
        rollback=None,
        risk=RiskTensor(irreversibility=4, privacy=2),
    )
    report = OAKGate().dry_run(action)
    assert report.decision == Decision.BLOCK
    assert "missing_rollback" in report.blocked_by
