from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .constitution import AutonomyConstitution
from .coverage import ClaimCoverageEngine
from .expiry import EvidenceExpiryEngine
from .promotion import PromotionProofBuilder
from .supply_chain import SupplyChainAuditor


def run_oakbench() -> dict[str, object]:
    now = datetime(2026, 8, 3, tzinfo=timezone.utc)
    claim = {
        "claim_id": "CLAIM-OAK-R02",
        "required_test_ids": ["TEST-POS", "TEST-NEG", "TEST-PROP"],
        "required_evidence": ["unit", "adversarial", "property"],
        "subject_packages": ["omega_ci_proof_t.r02"],
        "domain_of_validity": ["finite software fixtures"],
        "falsifiers": ["required test failure"],
        "evidence_ttl_days": 30,
    }
    tests = [
        {"test_id": "TEST-POS", "kind": "unit", "source_claim_ids": ["CLAIM-OAK-R02"]},
        {"test_id": "TEST-NEG", "kind": "adversarial", "source_claim_ids": ["CLAIM-OAK-R02"]},
        {"test_id": "TEST-PROP", "kind": "property", "source_claim_ids": ["CLAIM-OAK-R02"]},
    ]
    results = [{"test_id": item["test_id"], "status": "PASSED", "environment": "python-3.12"} for item in tests]
    coverage = ClaimCoverageEngine().evaluate([claim], tests, results)
    bundle = {"bundle_id": "EVID-OAK", "claims_tested": ["CLAIM-OAK-R02"], "subject": {"affected_packages": ["omega_ci_proof_t.r02"]}}
    validity = EvidenceExpiryEngine().evaluate(bundle, [claim], observed_at=now.isoformat(), evaluated_at=(now + timedelta(days=1)).isoformat())
    promotion = PromotionProofBuilder().build(
        claim_id="CLAIM-OAK-R02", from_status="PROTOTYPED", to_status="MEASURED",
        validity=[validity], coverage=coverage.claims[0], evidence_bundle_ids=["EVID-OAK"],
        evidence_integrity_verified=True, no_critical_residuals=True,
    )
    constitution = {
        "immutable_principles": [
            "no_scientific_claim_without_evidence_class", "no_sensitive_merge_without_human_approval",
            "no_secret_exfiltration", "no_irreversible_action_without_rollback_or_consent",
            "all_autonomous_actions_are_audited", "no_self_authority_escalation",
        ],
        "maximum_authorized_level": "A3",
        "permissions": {"A1": ["read_evidence"], "A2": ["plan_tests"], "A3": ["generate_tests", "generate_diagnostics"]},
        "automatic_merge_allowed": False,
        "human_review_required": True,
        "amendment_requires_separate_pr": True,
    }
    constitution_audit = AutonomyConstitution(constitution).audit()
    workflow = "- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n"
    supply_findings = SupplyChainAuditor().audit_text(workflow)
    checks = {
        "coverage": coverage.weighted_score >= 0.8 and coverage.blocked_claims == 0,
        "validity": validity.status == "CURRENT",
        "promotion": promotion.decision == "ELIGIBLE_FOR_HUMAN_REVIEW" and not promotion.automatic_merge_allowed,
        "constitution": constitution_audit.passed,
        "supply_chain": all(item.severity != "error" for item in supply_findings),
    }
    return {
        "schema": "omega-ci-r02-oak/v2",
        "passed": all(checks.values()),
        "checks": checks,
        "automatic_merge_allowed": False,
        "maximum_authorized_level": "A3",
        "scientific_validation_claimed": False,
        "theorem_claimed": False,
    }
