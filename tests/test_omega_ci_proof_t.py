from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_ci_proof_t import (
    AutonomyGate,
    Claim,
    ClaimRegistry,
    EvidenceBundleBuilder,
    EvidenceVerifier,
    MMinusRegressionGenerator,
    ProofLedger,
    ProofPlanner,
    TestResult as CiTestResult,
    TestSpec as CiTestSpec,
    audit_source,
    diagnose_pytest_log,
    hash_file,
    run_oakbench,
)
from omega_ci_proof_t.io import test_catalog_from_mapping as load_test_catalog


def claim_registry() -> ClaimRegistry:
    return ClaimRegistry([
        Claim(
            claim_id="CLAIM-A",
            statement="Package A is deterministic for fixed inputs.",
            subject_packages=("pkg.a",),
            required_test_ids=("TEST-A",),
            status="PROTOTYPED",
        ),
        Claim(
            claim_id="CLAIM-B",
            statement="Package B rejects corrupt artifacts.",
            subject_packages=("pkg.b",),
            required_test_ids=("TEST-B",),
        ),
    ])


def test_claim_registry_rejects_duplicate_ids():
    claim = Claim("CLAIM-X", "x", ("pkg",), ("TEST-X",))
    with pytest.raises(ValueError, match="duplicate"):
        ClaimRegistry([claim, claim])


def test_claim_promotion_is_ordered_and_cannot_skip():
    registry = claim_registry()
    promoted = registry.promote("CLAIM-B", "PROTOTYPED")
    assert promoted.status == "PROTOTYPED"
    with pytest.raises(ValueError, match="invalid claim transition"):
        registry.promote("CLAIM-B", "FERTILE")


def test_proof_plan_selects_claims_tests_and_stale_claims():
    catalog = {
        "TEST-A": CiTestSpec("TEST-A", "property", "pkg.a", "pytest -q -k a", "A", ("CLAIM-A",)),
    }
    impact = {
        "plan_id": "IMPACT-1",
        "changed_paths": ["pkg/a.py"],
        "affected_packages": ["pkg.a"],
        "unknown_paths": [],
        "manifest_digest": "manifest",
    }
    plan = ProofPlanner(claim_registry(), catalog, environments=("python-3.12",)).plan(impact)
    assert plan.claim_ids == ("CLAIM-A",)
    assert plan.stale_claim_ids == ("CLAIM-A",)
    assert [test.test_id for test in plan.tests] == ["TEST-A"]
    assert plan.missing_test_ids == ()


def test_plan_exposes_missing_test_gap_for_a3_generation():
    impact = {"changed_paths": ["pkg/b.py"], "affected_packages": ["pkg.b"], "manifest_digest": "m"}
    plan = ProofPlanner(claim_registry(), {}).plan(impact)
    assert plan.missing_test_ids == ("TEST-B",)
    assert any("generated candidate" in item for item in plan.limitations)


def test_plan_identity_is_deterministic_under_input_order():
    catalog = {"TEST-A": CiTestSpec("TEST-A", "unit", "pkg.a", "pytest -q", "A", ("CLAIM-A",))}
    planner = ProofPlanner(claim_registry(), catalog)
    a = planner.plan({"changed_paths": ["z", "a"], "affected_packages": ["pkg.a"], "manifest_digest": "m"})
    b = planner.plan({"changed_paths": ["a", "z"], "affected_packages": ["pkg.a"], "manifest_digest": "m"})
    assert a.plan_id == b.plan_id
    assert a.digest == b.digest


def _passing_result(test_id: str) -> CiTestResult:
    return CiTestResult(test_id, "PASSED", "python-3.12", "pytest", 1, f"digest-{test_id}")


def test_evidence_bundle_promotes_only_when_complete():
    test = CiTestSpec("TEST-A", "unit", "pkg.a", "pytest", "A", ("CLAIM-A",))
    plan = ProofPlanner(claim_registry(), {"TEST-A": test}).plan({
        "changed_paths": ["pkg/a.py"], "affected_packages": ["pkg.a"], "manifest_digest": "m"
    })
    bundle = EvidenceBundleBuilder().build(
        plan, run_id="RUN-1", commit_sha="abc", environment={"python": "3.12"},
        test_results=(_passing_result("TEST-A"),), properties={"deterministic": True},
    )
    assert bundle.decision.promotion_allowed is True
    assert bundle.decision.automatic_merge_allowed is False
    assert bundle.bundle_id.startswith("EVIDENCE-")


def test_incomplete_evidence_bundle_is_blocked():
    test = CiTestSpec("TEST-A", "unit", "pkg.a", "pytest", "A", ("CLAIM-A",))
    plan = ProofPlanner(claim_registry(), {"TEST-A": test}).plan({
        "changed_paths": ["pkg/a.py"], "affected_packages": ["pkg.a"], "manifest_digest": "m"
    })
    bundle = EvidenceBundleBuilder().build(
        plan, run_id="RUN-2", commit_sha="abc", environment={}, test_results=(), properties={"deterministic": True}
    )
    assert bundle.decision.status == "BLOCKED"
    assert any("missing test results" in reason for reason in bundle.decision.reasons)


def test_evidence_verifier_detects_missing_required_test():
    test = CiTestSpec("TEST-A", "unit", "pkg.a", "pytest", "A", ("CLAIM-A",))
    plan = ProofPlanner(claim_registry(), {"TEST-A": test}).plan({
        "changed_paths": ["pkg/a.py"], "affected_packages": ["pkg.a"], "manifest_digest": "m"
    })
    bundle = EvidenceBundleBuilder().build(
        plan, run_id="RUN", commit_sha="abc", environment={}, test_results=(), properties={}
    )
    ok, errors = EvidenceVerifier().verify(bundle, required_test_ids=["TEST-A"])
    assert ok is False
    assert any("required tests absent" in error for error in errors)


def test_artifact_integrity_detects_tampering(tmp_path: Path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("original", encoding="utf-8")
    receipt = hash_file(artifact)
    plan = ProofPlanner(claim_registry(), {}).plan({
        "changed_paths": ["pkg/b.py"], "affected_packages": ["pkg.b"], "manifest_digest": "m"
    })
    bundle = EvidenceBundleBuilder().build(
        plan, run_id="RUN", commit_sha="abc", environment={}, test_results=(), properties={}, artifacts=(receipt,)
    )
    artifact.write_text("tampered", encoding="utf-8")
    ok, errors = EvidenceVerifier().verify(bundle)
    assert ok is False
    assert any("integrity mismatch" in error for error in errors)


def test_ledger_hash_chain_and_tamper_detection(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = ProofLedger(path)
    ledger.append({"event": "plan"})
    ledger.append({"event": "bundle"})
    assert ledger.verify() == (True, ())
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["payload"]["event"] = "forged"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    ok, errors = ledger.verify()
    assert ok is False
    assert any("entry hash mismatch" in error for error in errors)


def test_mminus_generator_is_deterministic_and_traceable(tmp_path: Path):
    source = MMinusRegressionGenerator().generate(MMinusRegressionGenerator.load(
        Path(__file__).parents[1] / "data/omega_ci_proof_t/mminus.json"
    ))
    assert "M_MINUS-R0.3-001" in source
    assert "test_dot_github_prefix_is_preserved_generated" in source
    assert source == MMinusRegressionGenerator().generate(MMinusRegressionGenerator.load(
        Path(__file__).parents[1] / "data/omega_ci_proof_t/mminus.json"
    ))


def test_adversarial_audit_finds_trivial_assertion_and_hidden_workflow_failure(tmp_path: Path):
    test_file = tmp_path / "test_bad.py"
    test_file.write_text("def test_bad():\n    assert True\n", encoding="utf-8")
    workflow = tmp_path / "ci.yml"
    workflow.write_text("steps:\n  - uses: actions/checkout@v4\n    continue-on-error: true\n", encoding="utf-8")
    test_findings = audit_source(test_file)
    workflow_findings = audit_source(workflow)
    assert any(item.category == "trivial_assertion" and item.severity == "error" for item in test_findings)
    assert any(item.category == "hidden_failure" for item in workflow_findings)
    assert any(item.category == "unpinned_action" and item.severity == "warning" for item in workflow_findings)


def test_diagnosis_classifies_pytest_assertion_and_mminus_pattern():
    log = "FAILED tests/test_x.py::test_dot - AssertionError\n.github/workflows/ci.yml -> github/workflows/ci.yml"
    diagnostic = diagnose_pytest_log(log)
    assert diagnostic.failure_class == "deterministic_test_regression"
    assert diagnostic.stage == "test"
    assert any("leading dot" in cause for cause in diagnostic.suspected_causes)


def test_autonomy_gate_grants_a3_but_denies_a4_and_sensitive_work():
    gate = AutonomyGate()
    assert gate.evaluate("A3").allowed is True
    denied = gate.evaluate("A4")
    assert denied.allowed is False
    assert denied.automatic_merge_allowed is False
    sensitive = gate.evaluate("A3", security_sensitive=True)
    assert sensitive.allowed is False


def test_oakbench_enforces_no_auto_merge_and_ledger_integrity(tmp_path: Path):
    ledger = ProofLedger(tmp_path / "ledger.jsonl")
    ledger.append({"event": "proof"})
    result = run_oakbench(registry=claim_registry(), ledger_path=ledger.path)
    assert result["passed"] is True
    assert result["automatic_merge"] is False
    assert result["scientific_validation_claimed"] is False


def test_skipped_required_test_blocks_promotion():
    test = CiTestSpec("TEST-A", "unit", "pkg.a", "pytest", "A", ("CLAIM-A",))
    plan = ProofPlanner(claim_registry(), {"TEST-A": test}).plan({
        "changed_paths": ["pkg/a.py"], "affected_packages": ["pkg.a"], "manifest_digest": "m"
    })
    skipped = CiTestResult("TEST-A", "SKIPPED", "python-3.12", "pytest", 0, "skip")
    bundle = EvidenceBundleBuilder().build(
        plan, run_id="RUN-SKIP", commit_sha="abc", environment={}, test_results=(skipped,), properties={}
    )
    assert bundle.decision.promotion_allowed is False
    assert any("failed tests" in reason for reason in bundle.decision.reasons)


def test_serialized_bundle_verifier_detects_merkle_tampering():
    test = CiTestSpec("TEST-A", "unit", "pkg.a", "pytest", "A", ("CLAIM-A",))
    plan = ProofPlanner(claim_registry(), {"TEST-A": test}).plan({
        "changed_paths": ["pkg/a.py"], "affected_packages": ["pkg.a"], "manifest_digest": "m"
    })
    bundle = EvidenceBundleBuilder().build(
        plan, run_id="RUN-MERKLE", commit_sha="abc", environment={},
        test_results=(_passing_result("TEST-A"),), properties={"deterministic": True}
    )
    raw = bundle.to_dict()
    raw["merkle_root"] = "0" * 64
    ok, errors = EvidenceVerifier().verify_serialized(raw, required_test_ids=["TEST-A"])
    assert ok is False
    assert any("Merkle root" in error for error in errors)


def test_sample_catalog_loads_all_test_specs():
    raw = json.loads((Path(__file__).parents[1] / "data/omega_ci_proof_t/tests.json").read_text())
    catalog = load_test_catalog(raw)
    assert set(catalog) == {
        "TEST-REPOTWIN-DETERMINISM", "TEST-ROUTER-REVERSE-CLOSURE",
        "TEST-DOT-GITHUB-REGRESSION", "TEST-PROOF-TAMPER-DETECTION",
    }
