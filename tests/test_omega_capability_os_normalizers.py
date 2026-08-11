from __future__ import annotations

import json

import pytest

from omega_capability_os_t.core import Capability
from omega_capability_os_t.external import ExternalBinding, make_external_request
from omega_capability_os_t.normalizers import (
    ProviderResponseNormalizationError,
    ResponseContract,
    normalize_calendar_response,
    normalize_drive_response,
    normalize_files_response,
    normalize_github_response,
    normalize_gmail_response,
    normalize_provider_response,
    normalize_web_response,
)


def _request(
    *,
    connector: str = "GitHub",
    action: str = "fetch_pr",
    authority: str = "read",
    external_authority: str = "read",
    outputs: tuple[str, ...] = ("pr_metadata", "commit_sha"),
    candidate_sha: str | None = "abc123",
):
    cap = Capability(
        capability_id=f"test.{connector}.{action}",
        domains=("test",),
        consumes=("input",),
        produces=outputs,
        authority=authority,
        quality=1.0,
    )
    binding = ExternalBinding(
        capability_id=cap.capability_id,
        connector=connector,
        action=action,
        argument_template={"value": "$input"},
        external_authority=external_authority,
    )
    return make_external_request(
        cap,
        binding,
        {"input": "x"},
        candidate_sha=candidate_sha,
        plan_fingerprint="plan-r05",
    )


def test_github_normalizer_builds_exact_sha_bound_receipt():
    request = _request()
    raw = {
        "connector_name": "GitHub",
        "action_name": "fetch_pr",
        "result": {
            "pull_request": {
                "number": 417,
                "state": "open",
                "head_sha": "abc123",
            },
            "url": "https://github.com/example/repo/pull/417",
        },
    }
    receipt = normalize_github_response(
        request,
        raw,
        output_paths={
            "pr_metadata": "pull_request",
            "commit_sha": "pull_request.head_sha",
        },
    )
    assert receipt.status == "SUCCESS"
    assert receipt.outputs["commit_sha"] == "abc123"
    assert receipt.observed_candidate_sha == "abc123"
    assert receipt.sources == ("https://github.com/example/repo/pull/417",)
    assert any(note.startswith("raw_response_fingerprint=") for note in receipt.notes)


def test_github_normalizer_rejects_stale_candidate_sha():
    request = _request(candidate_sha="abc123")
    raw = {
        "result": {
            "pull_request": {"number": 417, "head_sha": "stale999"},
        }
    }
    with pytest.raises(ProviderResponseNormalizationError, match="observed_candidate_sha mismatch"):
        normalize_github_response(
            request,
            raw,
            output_paths={
                "pr_metadata": "pull_request",
                "commit_sha": "pull_request.head_sha",
            },
        )


def test_github_normalizer_requires_observed_sha_for_sha_bound_success():
    request = _request(candidate_sha="abc123")
    raw = {"result": {"pull_request": {"number": 417}, "derived": "abc123"}}
    with pytest.raises(ProviderResponseNormalizationError, match="lacks an observed candidate SHA"):
        normalize_github_response(
            request,
            raw,
            output_paths={
                "pr_metadata": "pull_request",
                "commit_sha": "derived",
            },
        )


def test_normalizer_rejects_misbound_connector_envelope():
    request = _request()
    raw = {
        "connector_name": "Gmail",
        "action_name": "fetch_pr",
        "result": {"pull_request": {"number": 417, "head_sha": "abc123"}},
    }
    with pytest.raises(ProviderResponseNormalizationError, match="connector identity"):
        normalize_github_response(
            request,
            raw,
            output_paths={
                "pr_metadata": "pull_request",
                "commit_sha": "pull_request.head_sha",
            },
        )


def test_normalizer_rejects_misbound_action_envelope():
    request = _request()
    raw = {
        "connector_name": "GitHub",
        "action_name": "merge_pull_request",
        "result": {"pull_request": {"number": 417, "head_sha": "abc123"}},
    }
    with pytest.raises(ProviderResponseNormalizationError, match="action identity"):
        normalize_github_response(
            request,
            raw,
            output_paths={
                "pr_metadata": "pull_request",
                "commit_sha": "pull_request.head_sha",
            },
        )


def test_success_missing_declared_output_fails_before_receipt():
    request = _request(candidate_sha=None)
    raw = {"result": {"pull_request": {"number": 417}}}
    with pytest.raises(ProviderResponseNormalizationError, match="missing declared outputs"):
        normalize_github_response(
            request,
            raw,
            output_paths={
                "pr_metadata": "pull_request",
                "commit_sha": "missing.sha",
            },
            require_candidate_sha=False,
        )


def test_connector_error_becomes_failure_receipt_for_runtime_fallback():
    request = _request()
    raw = {
        "connector_name": "GitHub",
        "action_name": "fetch_pr",
        "error": {"message": "provider unavailable"},
        "is_error": True,
    }
    receipt = normalize_github_response(
        request,
        raw,
        output_paths={
            "pr_metadata": "pull_request",
            "commit_sha": "pull_request.head_sha",
        },
    )
    assert receipt.status == "FAILURE"
    assert receipt.outputs == {}
    assert receipt.error == "provider unavailable"


def test_files_normalizer_unwraps_json_content_without_raw_persistence():
    request = _request(
        connector="files",
        action="search",
        outputs=("memory_pointer",),
        candidate_sha=None,
    )
    raw = {
        "content": json.dumps(
            {
                "pointer": {"checkpoint": "chatmem-live-1"},
                "resource_uri": "library://chatmem/global-pointer",
            }
        )
    }
    receipt = normalize_files_response(
        request,
        raw,
        output_paths={"memory_pointer": "pointer"},
    )
    assert receipt.outputs["memory_pointer"]["checkpoint"] == "chatmem-live-1"
    assert receipt.sources == ("library://chatmem/global-pointer",)
    rendered = json.dumps(receipt.to_dict(include_outputs=False), sort_keys=True)
    assert "chatmem-live-1" not in rendered


@pytest.mark.parametrize(
    ("connector", "action", "normalizer", "body", "path", "expected"),
    [
        (
            "Google_Drive",
            "fetch",
            normalize_drive_response,
            {"result": {"file": {"id": "drive-1", "name": "archive.json"}}},
            "file",
            "drive-1",
        ),
        (
            "Gmail",
            "read_message",
            normalize_gmail_response,
            {"result": {"message": {"id": "msg-1", "subject": "hello"}}},
            "message",
            "msg-1",
        ),
        (
            "Google_Calendar",
            "read_event",
            normalize_calendar_response,
            {"result": {"event": {"id": "evt-1", "summary": "review"}}},
            "event",
            "evt-1",
        ),
    ],
)
def test_google_family_provider_normalizers(connector, action, normalizer, body, path, expected):
    request = _request(
        connector=connector,
        action=action,
        outputs=("record",),
        candidate_sha=None,
    )
    receipt = normalizer(request, body, output_paths={"record": path})
    assert receipt.status == "SUCCESS"
    assert receipt.outputs["record"]["id"] == expected


def test_web_normalizer_supports_list_index_selectors():
    request = _request(
        connector="web",
        action="system1_search_query",
        outputs=("top_result",),
        candidate_sha=None,
    )
    raw = [{"title": "Result A", "url": "https://example.test/a"}]
    receipt = normalize_web_response(
        request,
        raw,
        output_paths={"top_result": "0"},
        source_paths=("0.url",),
    )
    assert receipt.outputs["top_result"]["title"] == "Result A"
    assert receipt.sources == ("https://example.test/a",)


def test_write_success_requires_explicit_mutation_attestation():
    request = _request(
        connector="Gmail",
        action="send",
        authority="write",
        external_authority="write",
        outputs=("message_id",),
        candidate_sha=None,
    )
    raw = {"result": {"id": "msg-sent-1"}}
    with pytest.raises(ProviderResponseNormalizationError, match="mutation_performed=true"):
        normalize_gmail_response(request, raw, output_paths={"message_id": "id"})

    receipt = normalize_gmail_response(
        request,
        raw,
        output_paths={"message_id": "id"},
        mutation_performed=True,
        mutation_refs=("msg-sent-1",),
    )
    assert receipt.status == "SUCCESS"
    assert receipt.mutation_performed is True
    assert "msg-sent-1" in receipt.mutation_refs


def test_read_response_claiming_mutation_fails_closed():
    request = _request(
        connector="Gmail",
        action="read_message",
        outputs=("message",),
        candidate_sha=None,
    )
    raw = {"result": {"message": {"id": "msg-1"}}}
    with pytest.raises(ProviderResponseNormalizationError, match="non-mutating external request"):
        normalize_gmail_response(
            request,
            raw,
            output_paths={"message": "message"},
            mutation_performed=True,
        )


def test_contract_cannot_map_outputs_not_declared_by_request():
    request = _request(outputs=("one",), candidate_sha=None)
    contract = ResponseContract(
        provider="github",
        output_paths={"one": "one", "two": "two"},
        require_candidate_sha=False,
    )
    with pytest.raises(ProviderResponseNormalizationError, match="undeclared outputs"):
        normalize_provider_response(request, {"one": 1, "two": 2}, contract)


def test_selector_fallbacks_are_deterministic():
    request = _request(outputs=("value",), candidate_sha=None)
    contract = ResponseContract(
        provider="github",
        output_paths={"value": ("preferred.value", "fallback.value")},
        require_candidate_sha=False,
    )
    receipt = normalize_provider_response(
        request,
        {"fallback": {"value": 7}},
        contract,
    )
    assert receipt.outputs == {"value": 7}
