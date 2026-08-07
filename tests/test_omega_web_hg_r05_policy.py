from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from omega_web_hg_t.r05 import (
    BUILTIN_POLICIES,
    PolicyGate,
    PolicyProfile,
    PolicyRegistry,
    PolicyViolation,
    RequestContext,
    RetentionPolicy,
    ReviewPolicy,
    compare_compiled_policies,
    compile_policy,
    normalized_compilation,
    policy_by_id,
)
from omega_web_hg_t.r05.cli import main

AS_OF = "2026-08-03"


def valid_record(**extra):
    return {
        "source_id": "crossref",
        "record_id": "10.1/example",
        "canonical_url": "https://doi.org/10.1/example",
        "title": "Example",
        "record_type": "article",
        "identifiers": {"doi": "10.1/example"},
        **extra,
    }


def test_builtin_catalog_has_governed_and_review_only_sources():
    assert len(BUILTIN_POLICIES) == 12
    compiled = {item.source_id: compile_policy(item, as_of=AS_OF) for item in BUILTIN_POLICIES}
    assert sum(item.review_status == "pass" for item in compiled.values()) == 11
    assert compiled["arxiv"].review_status == "human_review"


def test_compilation_is_deterministic():
    profile = policy_by_id("crossref")
    first = normalized_compilation(profile, as_of=AS_OF)
    second = normalized_compilation(profile, as_of=AS_OF)
    assert first == second
    assert json.loads(first)["policy_digest"] == compile_policy(profile, as_of=AS_OF).policy_digest


def test_overdue_profile_fails_closed_into_human_review():
    compiled = compile_policy(policy_by_id("crossref"), as_of="2026-10-01")
    assert compiled.review_status == "human_review"
    assert "policy_review_overdue" in compiled.review_reasons


def test_expired_profile_is_not_executable():
    profile = replace(policy_by_id("crossref"), policy_status="expired")
    compiled = compile_policy(profile, as_of=AS_OF)
    assert compiled.review_status == "fail"


def test_profile_rejects_conflicting_allow_and_forbid_fields():
    original = policy_by_id("crossref").to_dict(include_digest=False)
    original["allowed_fields"] = ["title", "abstract"]
    original["forbidden_fields"] = ["abstract"]
    with pytest.raises(ValueError):
        PolicyProfile.from_mapping(original)


def test_request_gate_accepts_governed_route_with_identity():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision = gate.evaluate_request(
        RequestContext(
            route="rest_api",
            headers={"User-Agent": "Omega-Web-HG-R05/0.5"},
            environment={},
            requested_rps=0.5,
            contact_email="research@example.invalid",
        )
    )
    assert decision.allowed is True
    assert decision.violations == ()


def test_request_gate_rejects_unknown_route():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision = gate.evaluate_request(
        RequestContext("html_scrape", {"User-Agent": "test"}, {}, 0.5, "x@example.invalid")
    )
    assert decision.allowed is False
    assert {item.code for item in decision.violations} == {"ROUTE_NOT_ALLOWED"}


def test_request_gate_requires_user_agent():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision = gate.evaluate_request(RequestContext("rest_api", {}, {}, 0.5, "x@example.invalid"))
    assert "USER_AGENT_REQUIRED" in {item.code for item in decision.violations}


def test_key_required_source_fails_without_environment():
    gate = PolicyGate(compile_policy(policy_by_id("openalex"), as_of=AS_OF))
    decision = gate.evaluate_request(
        RequestContext("rest_api", {"User-Agent": "test"}, {}, 1.0, None)
    )
    assert decision.allowed is False
    assert any(item.path == "OPENALEX_API_KEY" for item in decision.violations)


def test_key_required_source_passes_with_environment():
    gate = PolicyGate(compile_policy(policy_by_id("openalex"), as_of=AS_OF))
    decision = gate.evaluate_request(
        RequestContext("rest_api", {"User-Agent": "test"}, {"OPENALEX_API_KEY": "secret-present"}, 1.0, None)
    )
    assert decision.allowed is True


def test_rate_above_maximum_is_rejected():
    gate = PolicyGate(compile_policy(policy_by_id("pubmed"), as_of=AS_OF))
    decision = gate.evaluate_request(
        RequestContext("eutils", {"User-Agent": "test"}, {}, 4.0, "x@example.invalid")
    )
    assert "MAXIMUM_RATE_EXCEEDED" in {item.code for item in decision.violations}


def test_policy_under_review_blocks_requests_even_on_known_route():
    gate = PolicyGate(compile_policy(policy_by_id("arxiv"), as_of=AS_OF))
    decision = gate.evaluate_request(
        RequestContext("api", {"User-Agent": "test"}, {}, 0.2, None)
    )
    assert decision.allowed is False
    assert "POLICY_NOT_EXECUTABLE" in {item.code for item in decision.violations}


def test_record_gate_rejects_abstract_body_and_full_text():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    for field in ("abstract", "body", "full_text"):
        decision = gate.evaluate_record(valid_record(**{field: "forbidden"}))
        assert decision.allowed is False
        assert "FORBIDDEN_FIELD" in {item.code for item in decision.violations}


def test_record_gate_detects_nested_and_camel_case_aliases():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision = gate.evaluate_record(valid_record(metadata={"fullText": "forbidden"}))
    assert decision.allowed is False
    assert any(item.path == "$.metadata.fullText" for item in decision.violations)


def test_record_gate_rejects_unknown_top_level_field():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision = gate.evaluate_record(valid_record(secret_payload="x"))
    assert decision.allowed is False
    assert "FIELD_NOT_ALLOWLISTED" in {item.code for item in decision.violations}


def test_redaction_mode_removes_forbidden_and_unknown_fields():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision = gate.evaluate_record(
        valid_record(abstract="remove", secret_payload="remove", metadata={"body": "remove"}),
        mode="redact",
    )
    assert decision.allowed is True
    assert "abstract" not in decision.transformed_payload
    assert "secret_payload" not in decision.transformed_payload
    assert "metadata" not in decision.transformed_payload
    assert decision.warnings


def test_enforce_record_raises_with_content_addressed_decision():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    with pytest.raises(PolicyViolation) as error:
        gate.enforce_record(valid_record(full_text="forbidden"))
    assert error.value.decision.decision_digest
    assert error.value.decision.allowed is False


def test_raw_response_storage_is_forbidden():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision, storage = gate.evaluate_storage(
        object_id="response:1", storage_level=2, content_class="raw_response"
    )
    assert decision.allowed is False
    assert storage.allowed is False
    assert storage.retention_mode == "forbidden"


def test_normalized_metadata_storage_is_allowed():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision, storage = gate.evaluate_storage(
        object_id="record:1", storage_level=1, content_class="metadata"
    )
    assert decision.allowed is True
    assert storage.allowed is True
    assert storage.retention_mode == "allowed"


def test_level_three_storage_requires_encryption():
    gate = PolicyGate(compile_policy(policy_by_id("crossref"), as_of=AS_OF))
    decision, _ = gate.evaluate_storage(
        object_id="record:1", storage_level=3, content_class="metadata", encrypted_at_rest=False
    )
    assert decision.allowed is False
    assert "ENCRYPTION_REQUIRED" in {item.code for item in decision.violations}


def test_policy_drift_flags_relaxed_forbidden_fields():
    original = policy_by_id("crossref")
    relaxed = replace(original, forbidden_fields=tuple(item for item in original.forbidden_fields if item != "abstract"))
    report = compare_compiled_policies(
        compile_policy(original, as_of=AS_OF),
        compile_policy(relaxed, as_of=AS_OF),
    )
    assert report["changed"] is True
    assert "forbidden_fields_relaxed" in report["risk_flags"]
    assert report["requires_human_review"] is True


def test_policy_drift_flags_raw_response_retention_relaxation():
    original = policy_by_id("crossref")
    relaxed = replace(original, retention=replace(original.retention, raw_response="allowed"))
    report = compare_compiled_policies(
        compile_policy(original, as_of=AS_OF),
        compile_policy(relaxed, as_of=AS_OF),
    )
    assert "raw_response_retention_relaxed" in report["risk_flags"]


def test_registry_deduplicates_and_exports_denials(tmp_path: Path):
    profile = policy_by_id("crossref")
    compiled = compile_policy(profile, as_of=AS_OF)
    gate = PolicyGate(compiled)
    denied = gate.evaluate_record(valid_record(abstract="forbidden"))
    storage_decision, storage = gate.evaluate_storage(
        object_id="response:1", storage_level=2, content_class="raw_response"
    )
    with PolicyRegistry(tmp_path / "registry.sqlite3") as registry:
        assert registry.record_profile(profile) is True
        assert registry.record_profile(profile) is False
        assert registry.record_compiled(compiled) is True
        assert registry.record_compiled(compiled) is False
        assert registry.record_decision(denied) is True
        assert registry.record_storage_decision(storage) is True
        assert registry.counts() == {
            "profiles": 1,
            "compiled_policies": 1,
            "gate_decisions": 1,
            "storage_decisions": 1,
        }
        assert registry.denied_decisions("crossref")[0]["allowed"] is False
        outputs = registry.export_jsonl(tmp_path / "export")
    assert all(path.exists() for path in outputs)
    manifest = json.loads((tmp_path / "export" / "registry-manifest.json").read_text())
    assert manifest["raw_policy_documents_persisted"] is False
    assert storage_decision.allowed is False


def test_cli_audit_passes(tmp_path: Path):
    output = tmp_path / "audit.json"
    assert main(["audit", "--as-of", AS_OF, "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "PASS"
    assert payload["source_count"] == 12
    assert payload["pass_count"] == 11


def test_cli_materializes_registry_and_profiles(tmp_path: Path):
    root = tmp_path / "materialized"
    assert main(["materialize", "--as-of", AS_OF, "--output-dir", str(root)]) == 0
    manifest = json.loads((root / "materialization-manifest.json").read_text())
    assert manifest["source_count"] == 12
    assert manifest["pass_count"] == 11
    assert manifest["human_review_count"] == 1
    assert (root / "profiles" / "crossref.json").exists()
    assert (root / "compiled" / "crossref.json").exists()
    assert (root / "policy-registry.sqlite3").exists()
