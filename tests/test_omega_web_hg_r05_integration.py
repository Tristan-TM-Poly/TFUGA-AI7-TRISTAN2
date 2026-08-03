from __future__ import annotations

from dataclasses import replace
import json

import pytest

from omega_web_hg_t.r04.max_adapters import adapter_by_id
from omega_web_hg_t.r05.gate import PolicyViolation
from omega_web_hg_t.r05.integration import (
    AdapterPolicyBindingError,
    audit_r04_bindings,
    bind_adapter,
    bind_all_r04_adapters,
)

AS_OF = "2026-08-03"


def test_every_r04_adapter_has_an_executable_r05_binding():
    report = audit_r04_bindings(as_of=AS_OF)
    assert report["status"] == "PASS"
    assert report["adapter_count"] == 11
    assert report["bound_count"] == 11
    assert report["failures"] == []
    assert report["binding_audit_is_network_execution"] is False
    assert report["raw_body_persisted"] is False


def test_binding_digests_are_stable_and_unique_by_source():
    first = bind_all_r04_adapters(as_of=AS_OF)
    second = bind_all_r04_adapters(as_of=AS_OF)
    assert [item.binding_digest for item in first] == [item.binding_digest for item in second]
    assert len({item.binding_digest for item in first}) == len(first)


def test_crossref_request_is_authorized_without_network_execution():
    bound = bind_adapter(adapter_by_id("crossref"), as_of=AS_OF)
    request = bound.authorize_request(
        "hypergraph",
        1,
        25,
        environment={},
        contact_email="research@example.invalid",
    )
    assert request.decision.allowed is True
    assert request.url.startswith("https://api.crossref.org/works?")
    evidence = request.to_dict()
    assert evidence["secret_query_values_persisted"] is False
    assert evidence["url_sha256"]
    assert "public_url" in evidence


def test_openalex_request_fails_closed_without_key():
    bound = bind_adapter(adapter_by_id("openalex"), as_of=AS_OF)
    with pytest.raises(PolicyViolation) as error:
        bound.authorize_request("hypergraph", 1, 25, environment={})
    assert "REQUIRED_ENVIRONMENT_MISSING" in {
        item.code for item in error.value.decision.violations
    }


def test_openalex_request_evidence_redacts_key_value():
    bound = bind_adapter(adapter_by_id("openalex"), as_of=AS_OF)
    request = bound.authorize_request(
        "hypergraph",
        1,
        25,
        environment={"OPENALEX_API_KEY": "super-secret-value"},
    )
    assert "super-secret-value" in request.url
    evidence = request.to_dict()
    assert "super-secret-value" not in json.dumps(evidence)
    assert "REDACTED" in evidence["public_url"]
    assert evidence["secret_query_values_persisted"] is False


def test_crossref_parser_output_passes_policy_gate():
    bound = bind_adapter(adapter_by_id("crossref"), as_of=AS_OF)
    body = json.dumps(
        {
            "message": {
                "items": [
                    {
                        "DOI": "10.1/example",
                        "title": ["Metadata fixture"],
                        "URL": "https://doi.org/10.1/example",
                        "type": "article",
                        "abstract": "parser must discard this",
                        "author": [{"family": "Discarded"}],
                    }
                ]
            }
        }
    ).encode()
    batch = bound.parse_and_gate(body, "receipt-1")
    assert batch.rejected_count == 0
    assert len(batch.records) == 1
    assert batch.records[0]["title"] == "Metadata fixture"
    assert "abstract" not in batch.records[0]
    assert "author" not in batch.records[0]
    assert batch.raw_body_persisted is False
    assert batch.full_text_collected is False


def test_malicious_parser_record_is_rejected_after_parsing():
    class EvilRecord:
        def to_dict(self):
            return {
                "source_id": "crossref",
                "record_id": "evil",
                "canonical_url": "https://example.invalid/evil",
                "title": "Evil fixture",
                "fullText": "must never pass",
            }

    adapter = replace(adapter_by_id("crossref"), parser=lambda body, receipt: [EvilRecord()])
    bound = bind_adapter(adapter, as_of=AS_OF)
    with pytest.raises(PolicyViolation) as error:
        bound.parse_and_gate(b"{}", "receipt-evil")
    assert any(item.path == "$.fullText" for item in error.value.decision.violations)


def test_batch_can_record_rejection_without_accepting_payload():
    class EvilRecord:
        def to_dict(self):
            return {
                "source_id": "crossref",
                "record_id": "evil",
                "canonical_url": "https://example.invalid/evil",
                "title": "Evil fixture",
                "body": "must never pass",
            }

    adapter = replace(adapter_by_id("crossref"), parser=lambda body, receipt: [EvilRecord()])
    batch = bind_adapter(adapter, as_of=AS_OF).parse_and_gate(
        b"{}", "receipt-evil", reject_batch_on_violation=False
    )
    assert batch.rejected_count == 1
    assert batch.records == ()
    assert batch.decisions[0].allowed is False


def test_policy_url_mismatch_prevents_binding():
    adapter = replace(adapter_by_id("crossref"), policy_url="https://example.invalid/wrong-policy")
    with pytest.raises(AdapterPolicyBindingError, match="policy_url_mismatch"):
        bind_adapter(adapter, as_of=AS_OF)


def test_adapter_rate_above_policy_maximum_prevents_binding():
    adapter = replace(adapter_by_id("pubmed"), requests_per_second=10.0)
    with pytest.raises(AdapterPolicyBindingError, match="adapter_rate_exceeds_policy_maximum"):
        bind_adapter(adapter, as_of=AS_OF)


def test_non_https_url_is_rejected_after_authorization():
    adapter = replace(
        adapter_by_id("crossref"),
        url_builder=lambda query, page, size, env: "http://example.invalid/insecure",
    )
    bound = bind_adapter(adapter, as_of=AS_OF)
    with pytest.raises(AdapterPolicyBindingError, match="absolute HTTPS"):
        bound.authorize_request(
            "hypergraph",
            1,
            25,
            contact_email="research@example.invalid",
        )
