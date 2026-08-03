import pytest

from omega_action_ext_t import (
    ActionDNA,
    ActionManifest,
    ApprovalDecision,
    ApprovalState,
    Decision,
    OAKGate,
    RiskTensor,
    recipe_for,
)
from omega_action_ext_t.connectors import CalendarDryRunConnector, DriveDryRunConnector, GmailDryRunConnector


def test_approval_state_machine_allows_expected_transition():
    decision = ApprovalDecision(state=ApprovalState.PENDING, reason="new")
    approved = decision.transition_to(ApprovalState.APPROVED, "reviewed")
    assert approved.state == ApprovalState.APPROVED
    assert "pending->approved" in approved.notes[-1]


def test_approval_state_machine_blocks_invalid_transition():
    decision = ApprovalDecision(state=ApprovalState.REJECTED, reason="no")
    with pytest.raises(ValueError):
        decision.transition_to(ApprovalState.APPROVED, "cannot resurrect rejected item")


def test_rollback_recipe_for_pr():
    recipe = recipe_for("open_pr")
    assert recipe is not None
    assert recipe.reversible is True
    assert recipe.rollback_hint == "close_draft_pr"


def test_public_payload_leak_finding_blocks():
    action = ActionDNA(
        name="Public artifact",
        system="github",
        action_type="publish_release",
        public=True,
        approved=True,
        reversible=False,
        risk=RiskTensor(ip=1),
        metadata={"payload_text": "token = 'ghp_abcdefghijklmnopqrstuvwxyz123456'"},
    )
    report = OAKGate().dry_run(action)
    assert report.decision == Decision.BLOCK
    assert "public_payload_leak_finding" in report.blocked_by


def test_gmail_dryrun_downgrades_send_to_draft_plan():
    action = ActionDNA(
        name="Outreach",
        system="gmail",
        action_type="send_email",
        approved=False,
        touches_humans=True,
        risk=RiskTensor(reputation=1),
    )
    manifest = ActionManifest.compile(action)
    plan = GmailDryRunConnector().plan(manifest)
    assert plan.would_call == "gmail.create_draft"


def test_calendar_dryrun_notes_missing_timezone():
    action = ActionDNA(name="Meeting", system="calendar", action_type="create_event", risk=RiskTensor())
    manifest = ActionManifest.compile(action)
    plan = CalendarDryRunConnector().plan(manifest)
    assert any("missing timezone" in note for note in plan.safety_notes)


def test_drive_dryrun_blocks_destructive_shape():
    action = ActionDNA(
        name="Remove folder",
        system="drive",
        action_type="delete_folder",
        destructive=True,
        risk=RiskTensor(irreversibility=3),
    )
    manifest = ActionManifest.compile(action)
    plan = DriveDryRunConnector().plan(manifest)
    assert plan.would_call == "drive.block_or_require_backup"
