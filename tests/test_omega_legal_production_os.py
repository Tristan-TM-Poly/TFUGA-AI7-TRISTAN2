from dataclasses import replace
from datetime import datetime, timezone
import json

import pytest

from omega_legal_production_os_t import (
    ActionLedger,
    ActionState,
    ActionType,
    ApprovalRecord,
    AuthorityGrant,
    DryRunReleaseProvider,
    ExternalActionEnvelope,
    GateDecision,
    LegalProductionPolicyGate,
    ReleaseArtifact,
    ReleaseCandidate,
    RiskLevel,
    audit_policy_atlas,
    generate_policy_atlas,
)


def digest(char: str = "a") -> str:
    return "sha256:" + char * 64


def release_candidate(**changes) -> ReleaseCandidate:
    data = dict(
        release_id="REL-2026-001",
        repository="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        commit_sha="a" * 40,
        version="3.4.0",
        tag="v3.4.0",
        artifacts=(
            ReleaseArtifact("tfuga-3.4.0.whl", digest("1"), "application/zip", 42),
            ReleaseArtifact("tfuga-3.4.0.tar.gz", digest("2"), "application/gzip", 64),
        ),
        validations={
            "tests": "PASS",
            "licenses": "PASS",
            "sbom": "PASS",
            "install": "PASS",
            "security": "PASS",
        },
        changelog_hash=digest("3"),
        sbom_hash=digest("4"),
        created_at="2026-08-02T21:40:00Z",
        source_issue=281,
    )
    data.update(changes)
    return ReleaseCandidate(**data)


def release_action() -> ExternalActionEnvelope:
    return release_candidate().to_action(
        company_id="tristan_parent_opco",
        requested_by="tristan",
    )


def grant(permission: str = "publish_release", person: str = "tristan", role: str = "director") -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="AUTH-001",
        person_id=person,
        company_id="tristan_parent_opco",
        role=role,
        permissions=(permission,),
        amount_limit_cad=1000,
        jurisdictions=("QC", "CA"),
        valid_from="2026-01-01T00:00:00Z",
        valid_until="2027-01-01T00:00:00Z",
        evidence_hash=digest("5"),
    )


def test_action_hash_is_deterministic():
    first = release_action()
    second = ExternalActionEnvelope.from_mapping(first.to_mapping())
    assert first.action_hash == second.action_hash


def test_secret_like_payload_keys_are_rejected():
    with pytest.raises(ValueError, match="secret-like"):
        ExternalActionEnvelope(
            action_id="ACT-001",
            action_type=ActionType.PAYMENT,
            company_id="tristan_parent_opco",
            requested_by="tristan",
            requested_at="2026-08-02T21:40:00Z",
            purpose="unsafe fixture",
            payload={"api_key": "do-not-store"},
        )


def test_approval_is_bound_to_exact_action_hash():
    action = release_action()
    approval = ApprovalRecord.create(
        action,
        approver="tristan",
        role="director",
        approved_at=datetime(2026, 8, 2, 21, 40, tzinfo=timezone.utc),
    )
    changed = replace(action, purpose="changed after approval")
    assert "approval_hash_mismatch" in approval.validate_for(changed)


def test_duplicate_approver_is_blocked():
    action = release_action()
    first = ApprovalRecord.create(action, approver="tristan", role="director")
    approved = action.add_approval(first)
    duplicate = ApprovalRecord.create(action, approver="Tristan", role="director")
    with pytest.raises(ValueError, match="duplicate approver"):
        approved.add_approval(duplicate)


def test_invalid_state_jump_is_blocked():
    with pytest.raises(ValueError, match="invalid action transition"):
        release_action().transition(ActionState.APPROVED)


def test_valid_state_path_can_progress():
    action = release_action()
    for state in (
        ActionState.NORMALIZED,
        ActionState.VALIDATED,
        ActionState.RISK_SCORED,
        ActionState.AUTHORITY_RESOLVED,
        ActionState.READY_FOR_APPROVAL,
        ActionState.APPROVED,
        ActionState.RESERVED,
    ):
        action = action.transition(state)
    assert action.state == ActionState.RESERVED


def test_authority_grant_enforces_company_amount_and_jurisdiction():
    item = grant(permission="execute_payment")
    now = datetime(2026, 8, 2, tzinfo=timezone.utc)
    assert item.permits("execute_payment", company_id="tristan_parent_opco", amount_cad=999, jurisdiction="QC", at=now)
    assert not item.permits("execute_payment", company_id="other", amount_cad=1, jurisdiction="QC", at=now)
    assert not item.permits("execute_payment", company_id="tristan_parent_opco", amount_cad=1001, jurisdiction="QC", at=now)
    assert not item.permits("execute_payment", company_id="tristan_parent_opco", amount_cad=1, jurisdiction="US", at=now)


def test_release_candidate_requires_exact_tag():
    with pytest.raises(ValueError, match="tag"):
        release_candidate(tag="latest")


def test_release_candidate_dry_run_produces_no_external_effect():
    candidate = release_candidate()
    receipt = DryRunReleaseProvider().prepare(candidate, workflow_ref=".github/workflows/release.yml@refs/heads/main")
    assert receipt.status == "DRY_RUN_PREPARED"
    assert receipt.artifact_count == 2
    assert "No tag" in receipt.detail


def test_release_candidate_blocks_missing_validation():
    candidate = release_candidate(validations={"tests": "PASS"})
    with pytest.raises(RuntimeError, match="release candidate blocked"):
        DryRunReleaseProvider().prepare(candidate, workflow_ref="workflow")


def test_release_policy_allows_valid_dry_run():
    report = LegalProductionPolicyGate().evaluate(release_action(), execute=False)
    assert report.decision == GateDecision.ALLOW_DRY_RUN
    assert report.allowed


def test_release_execution_requires_approval_and_grant():
    report = LegalProductionPolicyGate().evaluate(release_action(), grants=(), execute=True)
    assert report.decision == GateDecision.REQUIRE_APPROVAL
    assert "approval_count_insufficient" in report.reasons


def test_release_execution_passes_with_exact_approval_and_grant():
    action = release_action()
    approval = ApprovalRecord.create(action, approver="tristan", role="director")
    action = action.add_approval(approval)
    report = LegalProductionPolicyGate().evaluate(action, grants=(grant(),), execute=True)
    assert report.decision == GateDecision.ALLOW_EXECUTION


def test_payment_can_require_two_independent_approvers():
    action = ExternalActionEnvelope(
        action_id="PAY-2026-001",
        action_type=ActionType.PAYMENT,
        company_id="tristan_parent_opco",
        requested_by="tristan",
        requested_at="2026-08-02T21:40:00Z",
        purpose="Pay verified invoice",
        payload={
            "amount_cad": 750,
            "currency": "CAD",
            "invoice_hash": digest("6"),
            "counterparty_verified": True,
            "rail": "BANK",
            "jurisdiction": "QC",
        },
        required_approvals=2,
        risk_level=RiskLevel.HIGH,
        policy_id="PAYMENT-R01",
    )
    one = ApprovalRecord.create(action, approver="tristan", role="director")
    action = action.add_approval(one)
    report = LegalProductionPolicyGate().evaluate(
        action,
        grants=(grant("execute_payment"),),
        execute=True,
    )
    assert report.decision == GateDecision.REQUIRE_TWO_APPROVALS

    two = ApprovalRecord.create(action, approver="finance-reviewer", role="finance_approver")
    action = action.add_approval(two)
    finance = grant("execute_payment", person="finance-reviewer", role="finance_approver")
    report = LegalProductionPolicyGate().evaluate(
        action,
        grants=(grant("execute_payment"), finance),
        execute=True,
    )
    assert report.decision == GateDecision.ALLOW_EXECUTION


def test_government_filing_requires_professional_review_evidence():
    action = ExternalActionEnvelope(
        action_id="FILE-2026-001",
        action_type=ActionType.GOVERNMENT_FILING,
        company_id="tristan_parent_opco",
        requested_by="tristan",
        requested_at="2026-08-02T21:40:00Z",
        purpose="Prepare annual filing",
        payload={
            "jurisdiction": "QC",
            "filing_hash": digest("7"),
            "human_attestation_required": True,
        },
        professional_review_required=True,
        policy_id="FILING-R01",
    )
    report = LegalProductionPolicyGate().evaluate(action, execute=False)
    assert report.decision == GateDecision.PROFESSIONAL_REVIEW


def test_ledger_reservation_is_append_only_and_blocks_replay(tmp_path):
    action = release_action()
    ledger = ActionLedger(tmp_path / "ledger.jsonl")
    entry = ledger.reserve(action, provider="github-release-dry-run")
    assert entry.event == "RESERVED"
    assert ledger.audit()["valid"]
    with pytest.raises(RuntimeError, match="replay"):
        ledger.reserve(action, provider="github-release-dry-run")


def test_ledger_detects_tampering(tmp_path):
    action = release_action()
    path = tmp_path / "ledger.jsonl"
    ledger = ActionLedger(path)
    ledger.reserve(action, provider="github-release-dry-run")
    row = json.loads(path.read_text(encoding="utf-8"))
    row["event"] = "CLOSED"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    report = ledger.audit()
    assert not report["valid"]
    assert any(error.startswith("entry_hash_mismatch") for error in report["errors"])


def test_policy_atlas_has_exact_cardinality_and_reproducible_audit(tmp_path):
    first = generate_policy_atlas(tmp_path / "atlas")
    report = audit_policy_atlas(tmp_path / "atlas")
    assert first["expected_cells"] == 1176
    assert report["valid"]
    assert report["cells"] == 1176
    assert report["shards"] == 56
