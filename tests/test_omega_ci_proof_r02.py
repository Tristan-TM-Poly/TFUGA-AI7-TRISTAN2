from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest

from omega_ci_proof_t.r02.cache import SemanticProofCache
from omega_ci_proof_t.r02.constitution import AutonomyConstitution
from omega_ci_proof_t.r02.coverage import ClaimCoverageEngine
from omega_ci_proof_t.r02.expiry import EvidenceExpiryEngine
from omega_ci_proof_t.r02.models import SemanticProofKey
from omega_ci_proof_t.r02.oak import run_oakbench
from omega_ci_proof_t.r02.promotion import PromotionProofBuilder, PromotionProofVerifier
from omega_ci_proof_t.r02.supply_chain import APPROVED_ACTIONS, SupplyChainAuditor

NOW = datetime(2026, 8, 3, 20, 0, tzinfo=timezone.utc)
CLAIM = {
    "claim_id": "CLAIM-R02",
    "subject_packages": ["omega_ci_proof_t.r02"],
    "required_test_ids": ["TEST-U", "TEST-A", "TEST-P"],
    "required_evidence": ["unit", "adversarial", "property"],
    "domain_of_validity": ["finite fixture"],
    "falsifiers": ["required test failure"],
    "evidence_ttl_days": 30,
    "criticality_weight": 2.0,
}
TESTS = [
    {"test_id": "TEST-U", "kind": "unit", "source_claim_ids": ["CLAIM-R02"]},
    {"test_id": "TEST-A", "kind": "adversarial", "source_claim_ids": ["CLAIM-R02"]},
    {"test_id": "TEST-P", "kind": "property", "source_claim_ids": ["CLAIM-R02"]},
]
RESULTS = [{"test_id": item["test_id"], "status": "PASSED", "environment": "python-3.12"} for item in TESTS]
BUNDLE = {"bundle_id": "EVID-R02", "claims_tested": ["CLAIM-R02"], "subject": {"affected_packages": ["omega_ci_proof_t.r02"]}}
CONSTITUTION = {
    "immutable_principles": [
        "no_scientific_claim_without_evidence_class", "no_sensitive_merge_without_human_approval",
        "no_secret_exfiltration", "no_irreversible_action_without_rollback_or_consent",
        "all_autonomous_actions_are_audited", "no_self_authority_escalation",
    ],
    "maximum_authorized_level": "A3",
    "permissions": {"A1": ["read_evidence"], "A2": ["expire_evidence"], "A3": ["generate_tests", "generate_diagnostics"]},
    "automatic_merge_allowed": False,
    "human_review_required": True,
    "amendment_requires_separate_pr": True,
}


def validity(**kwargs):
    return EvidenceExpiryEngine().evaluate(BUNDLE, [CLAIM], observed_at=NOW.isoformat(), evaluated_at=(NOW + timedelta(days=1)).isoformat(), **kwargs)


def full_coverage():
    return ClaimCoverageEngine().evaluate([CLAIM], TESTS, RESULTS).claims[0]


def test_current_evidence():
    item = validity(); assert item.status == "CURRENT"; assert len(item.validity_id) == 29


def test_expired_evidence():
    item = EvidenceExpiryEngine().evaluate(BUNDLE, [CLAIM], observed_at=NOW.isoformat(), evaluated_at=(NOW + timedelta(days=31)).isoformat())
    assert item.status == "EXPIRED"; assert "rerun_required_tests" in item.refresh_requirements


def test_package_change_invalidates():
    item = validity(changed_packages=["omega_ci_proof_t.r02"]); assert item.status == "INVALIDATED"


def test_test_change_invalidates():
    item = validity(changed_tests=["TEST-U"]); assert item.status == "INVALIDATED"


def test_dependency_change_marks_stale():
    item = validity(changed_dependencies=["pytest-major"]); assert item.status == "STALE"


def test_environment_change_marks_stale():
    item = validity(changed_environments=["python-3.14"]); assert item.status == "STALE"


def test_revocation_dominates():
    item = validity(revoked=True, changed_dependencies=["x"]); assert item.status == "REVOKED"


def test_superseded_evidence():
    item = validity(superseded_by="EVID-NEW"); assert item.status == "SUPERSEDED"


def test_claim_coverage_is_traceable_and_high():
    report = ClaimCoverageEngine().evaluate([CLAIM], TESTS, RESULTS); assert report.blocked_claims == 0; assert report.weighted_score >= 0.8


def test_missing_negative_evidence_blocks():
    report = ClaimCoverageEngine().evaluate([CLAIM], TESTS, [row for row in RESULTS if row["test_id"] != "TEST-A"])
    assert report.blocked_claims == 1; assert "adversarial" in report.claims[0].missing_kinds


def test_skipped_required_test_blocks():
    rows = [dict(row) for row in RESULTS]; rows[0]["status"] = "SKIPPED"
    assert ClaimCoverageEngine().evaluate([CLAIM], TESTS, rows).claims[0].blocked


def test_broken_provenance_blocks():
    tests = [dict(item) for item in TESTS]; tests[0]["source_claim_ids"] = []
    assert ClaimCoverageEngine().evaluate([CLAIM], tests, RESULTS).claims[0].blocked


def test_promotion_proof_eligible_for_human_review():
    proof = PromotionProofBuilder().build(claim_id="CLAIM-R02", from_status="PROTOTYPED", to_status="MEASURED", validity=[validity()], coverage=full_coverage(), evidence_bundle_ids=["EVID-R02"], evidence_integrity_verified=True, no_critical_residuals=True)
    assert proof.decision == "ELIGIBLE_FOR_HUMAN_REVIEW"; assert not proof.automatic_merge_allowed
    assert PromotionProofVerifier().verify(proof.to_dict())[0]


def test_invalid_transition_blocks_promotion():
    proof = PromotionProofBuilder().build(claim_id="CLAIM-R02", from_status="FERTILE", to_status="MEASURED", validity=[validity()], coverage=full_coverage(), evidence_bundle_ids=["EVID-R02"], evidence_integrity_verified=True, no_critical_residuals=True)
    assert proof.decision == "BLOCKED"


def test_expired_evidence_blocks_promotion():
    expired = EvidenceExpiryEngine().evaluate(BUNDLE, [CLAIM], observed_at=NOW.isoformat(), evaluated_at=(NOW + timedelta(days=31)).isoformat())
    proof = PromotionProofBuilder().build(claim_id="CLAIM-R02", from_status="PROTOTYPED", to_status="MEASURED", validity=[expired], coverage=full_coverage(), evidence_bundle_ids=["EVID-R02"], evidence_integrity_verified=True, no_critical_residuals=True)
    assert proof.decision == "BLOCKED"


def test_constitution_passes_and_is_deterministic():
    one = AutonomyConstitution(CONSTITUTION).audit(); two = AutonomyConstitution(CONSTITUTION).audit(); assert one.passed; assert one.constitution_digest == two.constitution_digest


def test_constitution_rejects_a4_authority():
    broken = dict(CONSTITUTION); broken["maximum_authorized_level"] = "A4"; assert not AutonomyConstitution(broken).audit().passed


def test_constitution_rejects_sensitive_a3_action():
    broken = json.loads(json.dumps(CONSTITUTION)); broken["permissions"]["A3"].append("merge"); assert not AutonomyConstitution(broken).audit().passed


def test_capability_token_allows_scoped_generation():
    constitution = AutonomyConstitution(CONSTITUTION)
    token = constitution.issue_token(agent="RegressionGenerator", run_id="RUN-1", level="A3", requested_actions=["generate_tests"], scope=["generated/tests"], issued_at=NOW.isoformat(), expires_at=(NOW + timedelta(hours=1)).isoformat())
    ok, reasons = constitution.authorize(token, action="generate_tests", resource="generated/tests/test_x.py", now=(NOW + timedelta(minutes=5)).isoformat())
    assert ok; assert reasons == ()


def test_capability_token_rejects_scope_escape():
    constitution = AutonomyConstitution(CONSTITUTION)
    token = constitution.issue_token(agent="RegressionGenerator", run_id="RUN-1", level="A3", requested_actions=["generate_tests"], scope=["generated/tests"], issued_at=NOW.isoformat(), expires_at=(NOW + timedelta(hours=1)).isoformat())
    assert not constitution.authorize(token, action="generate_tests", resource="omega_ci_proof_t/core.py", now=NOW.isoformat())[0]


def test_capability_token_rejects_expiry():
    constitution = AutonomyConstitution(CONSTITUTION)
    token = constitution.issue_token(agent="RegressionGenerator", run_id="RUN-1", level="A3", requested_actions=["generate_tests"], scope=["generated/tests"], issued_at=NOW.isoformat(), expires_at=(NOW + timedelta(minutes=1)).isoformat())
    assert not constitution.authorize(token, action="generate_tests", resource="generated/tests/x.py", now=(NOW + timedelta(minutes=2)).isoformat())[0]


def test_sensitive_capability_cannot_be_issued():
    with pytest.raises(PermissionError):
        AutonomyConstitution(CONSTITUTION).issue_token(agent="Bad", run_id="RUN", level="A3", requested_actions=["merge"], scope=[""], issued_at=NOW.isoformat(), expires_at=(NOW + timedelta(hours=1)).isoformat())


def test_supply_chain_accepts_reviewed_pins():
    text = "\n".join(f"- uses: {action}@{sha}" for action, sha in APPROVED_ACTIONS.items())
    findings = SupplyChainAuditor().audit_text(text); assert findings; assert all(item.severity == "info" for item in findings)


def test_supply_chain_rejects_moving_tag():
    findings = SupplyChainAuditor().audit_text("- uses: actions/checkout@v4"); assert findings[0].severity == "error"


def test_supply_chain_pin_rewriter_is_deterministic():
    auditor = SupplyChainAuditor(); source = "- uses: actions/checkout@v4\n"; assert auditor.pin_known_actions(source) == auditor.pin_known_actions(source)
    assert APPROVED_ACTIONS["actions/checkout"] in auditor.pin_known_actions(source)


def test_semantic_cache_key_is_deterministic_and_exact():
    key = SemanticProofKey("c", "s", "d", "linux-py312", "t"); cache = SemanticProofCache(); cache.put(key, "EVID")
    assert cache.get(key).bundle_id == "EVID"; assert SemanticProofKey("c", "s", "d", "linux-py312", "t").key == key.key


def test_semantic_cache_rejects_environment_mismatch():
    key = SemanticProofKey("c", "s", "d", "linux-py312", "t")
    ok, reasons = SemanticProofCache().evaluate_reuse(key, {"claim_digest": "c", "code_slice_digest": "s", "dependency_digest": "d", "environment_class": "windows-py312", "test_digest": "t"})
    assert not ok; assert reasons == ("semantic proof cache mismatch: environment_class",)


def test_oakbench_passes_without_merge_authority():
    result = run_oakbench(); assert result["passed"]; assert result["automatic_merge_allowed"] is False; assert result["maximum_authorized_level"] == "A3"
