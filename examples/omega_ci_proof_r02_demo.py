from datetime import datetime, timedelta, timezone

from omega_ci_proof_t.r02 import ClaimCoverageEngine, EvidenceExpiryEngine

claim = {
    "claim_id": "CLAIM-DEMO",
    "subject_packages": ["omega_ci_proof_t.r02"],
    "required_test_ids": ["TEST-UNIT", "TEST-ADV", "TEST-PROP"],
    "required_evidence": ["unit", "adversarial", "property"],
    "domain_of_validity": ["finite deterministic fixture"],
    "falsifiers": ["required test failure"],
    "evidence_ttl_days": 30,
}
tests = [
    {"test_id": "TEST-UNIT", "kind": "unit", "source_claim_ids": ["CLAIM-DEMO"]},
    {"test_id": "TEST-ADV", "kind": "adversarial", "source_claim_ids": ["CLAIM-DEMO"]},
    {"test_id": "TEST-PROP", "kind": "property", "source_claim_ids": ["CLAIM-DEMO"]},
]
results = [{"test_id": test["test_id"], "status": "PASSED", "environment": "python-3.12"} for test in tests]
coverage = ClaimCoverageEngine().evaluate([claim], tests, results)
now = datetime.now(timezone.utc)
validity = EvidenceExpiryEngine().evaluate(
    {"bundle_id": "EVID-DEMO", "claims_tested": ["CLAIM-DEMO"], "subject": {"affected_packages": ["omega_ci_proof_t.r02"]}},
    [claim], observed_at=now.isoformat(), evaluated_at=(now + timedelta(days=1)).isoformat(),
)
print(coverage.to_dict())
print(validity.to_dict())
