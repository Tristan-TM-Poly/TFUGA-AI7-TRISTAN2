from __future__ import annotations

from omega_capability_os_t.chatmem import (
    chatmem_bootstrap_intent,
    chatmem_capabilities,
    chatmem_checkpoint_intent,
    chatmem_external_bindings,
    checkpoint_gate_handler,
    default_chatmem_bootstrap_values,
)
from omega_capability_os_t.core import Capability, plan
from omega_capability_os_t.external import (
    ExternalActionReceipt,
    ExternalBinding,
    ExternalResolver,
    make_external_request,
    validate_external_bindings,
    validate_external_receipt,
)
from omega_capability_os_t.runtime import CapabilityRuntime


def _valid_manifest():
    return {
        "checkpoint_id": "CHATMEM-CP-0002",
        "previous_checkpoint": "CHATMEM-CP-0001",
        "oak_status": "PASS",
        "public_derivation_only": True,
        "raw_transcript_committed": False,
        "source_hashes": ["sha256:abc123"],
        "touched_systems": ["Ω-CAPABILITY-OS-T∞", "Ω-CHATMEM-HGFM-T∞"],
    }


def _checkpoint_values():
    return {
        "checkpoint_manifest": _valid_manifest(),
        "library_container_path": "/mnt/data/chatmem-checkpoint-r04.zip",
        "library_destination": "/Tristan/ChatGPT Memory/Checkpoints/chatmem-checkpoint-r04.zip",
        "repo": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        "branch": "feature/omega-capability-os-r01",
        "checkpoint_path": "memory/chatgpt/live/CHATMEM-CP-0002/checkpoint.json",
        "checkpoint_content": '{"checkpoint_id":"CHATMEM-CP-0002"}',
        "commit_message": "feat(chatmem): checkpoint CHATMEM-CP-0002",
        "pointer_path": "memory/chatgpt/CHATMEM_GLOBAL_POINTER.json",
        "pointer_content": '{"latest_checkpoint":"memory/chatgpt/live/CHATMEM-CP-0002/checkpoint.json"}',
        "pointer_blob_sha": "0123456789abcdef",
        "pointer_commit_message": "chore(chatmem): advance global pointer",
    }


def _run_checkpoint(receipts=()):
    caps = chatmem_capabilities()
    intent = chatmem_checkpoint_intent(allow_mutation=True)
    planned = plan(caps, intent)
    resolver = ExternalResolver(
        chatmem_external_bindings(),
        receipts=receipts,
        candidate_sha="candidate-sha",
        plan_fingerprint=planned["fingerprint"],
    )
    runtime = CapabilityRuntime(
        {"chatmem.validate_checkpoint": checkpoint_gate_handler},
        resolver=resolver,
    )
    result = runtime.execute(
        caps,
        intent,
        initial_values=_checkpoint_values(),
        candidate_sha="candidate-sha",
        evidence_sha="candidate-sha",
    )
    return result, resolver, planned


def _success_receipt(request, output_token, value):
    return {
        "request_id": request["request_id"],
        "capability_id": request["capability_id"],
        "connector": request["connector"],
        "action": request["action"],
        "status": "SUCCESS",
        "outputs": {output_token: value},
        "mutation_performed": True,
        "mutation_refs": [f"{request['connector']}:{request['action']}"],
        "observed_candidate_sha": "candidate-sha",
    }


def test_chatmem_binding_manifest_passes_external_authority_validation():
    result = validate_external_bindings(
        chatmem_capabilities(),
        chatmem_external_bindings(),
    )
    assert result["status"] == "PASS", result


def test_bootstrap_is_read_only_and_prefers_library_retrieval():
    caps = chatmem_capabilities()
    intent = chatmem_bootstrap_intent()
    planned = plan(caps, intent)
    ids = [step["capability_id"] for step in planned["steps"]]
    assert planned["status"] == "READY", planned
    assert ids == [
        "chatmem.library_search_pointer",
        "chatmem.library_search_context",
    ]
    assert all(step["authority"] == "read" for step in planned["steps"])


def test_bootstrap_external_request_is_redacted_and_non_mutating():
    caps = chatmem_capabilities()
    intent = chatmem_bootstrap_intent()
    planned = plan(caps, intent)
    resolver = ExternalResolver(
        chatmem_external_bindings(),
        candidate_sha="sha",
        plan_fingerprint=planned["fingerprint"],
    )
    result = CapabilityRuntime(resolver=resolver).execute(
        caps,
        intent,
        initial_values=default_chatmem_bootstrap_values("Capability OS"),
        candidate_sha="sha",
        evidence_sha="sha",
    )
    assert result["oak"]["status"] == "HOLD"
    request = result["actions_required"][0]["external_request"]
    assert request["external_authority"] == "read"
    assert request["arguments_redacted"] is True
    assert "arguments" not in request


def test_checkpoint_without_explicit_mutation_permission_stays_hold():
    planned = plan(
        chatmem_capabilities(),
        chatmem_checkpoint_intent(allow_mutation=False),
    )
    assert planned["status"] == "HOLD"
    assert planned["steps"] == []
    assert set(planned["unresolved_outputs"]) == {
        "library_persistence_receipt",
        "github_checkpoint_receipt",
        "github_pointer_update_receipt",
    }


def test_checkpoint_invalid_oak_privacy_manifest_stops_before_external_mutation():
    values = _checkpoint_values()
    values["checkpoint_manifest"] = {
        **_valid_manifest(),
        "oak_status": "HOLD",
        "raw_transcript_committed": True,
    }
    caps = chatmem_capabilities()
    intent = chatmem_checkpoint_intent(allow_mutation=True)
    planned = plan(caps, intent)
    resolver = ExternalResolver(
        chatmem_external_bindings(),
        candidate_sha="candidate-sha",
        plan_fingerprint=planned["fingerprint"],
    )
    result = CapabilityRuntime(
        {"chatmem.validate_checkpoint": checkpoint_gate_handler},
        resolver=resolver,
    ).execute(
        caps,
        intent,
        initial_values=values,
        candidate_sha="candidate-sha",
        evidence_sha="candidate-sha",
    )
    assert result["oak"]["status"] == "HOLD"
    assert result["actions_required"] == []
    assert resolver.pending_requests() == []
    assert result["observations"][0]["capability_id"] == "chatmem.validate_checkpoint"
    assert result["observations"][0]["outcome"] == "FAILURE"


def test_checkpoint_suspend_resume_orders_library_then_github_then_pointer():
    first, first_resolver, _ = _run_checkpoint()
    assert first["oak"]["status"] == "HOLD"
    request1 = first_resolver.pending_requests(include_arguments=True)[0]
    assert request1["capability_id"] == "chatmem.library_upload_bundle"
    assert request1["external_authority"] == "write"

    receipt1 = _success_receipt(
        request1,
        "library_persistence_receipt",
        {"path": "/Tristan/ChatGPT Memory/Checkpoints/chatmem-checkpoint-r04.zip"},
    )
    second, second_resolver, _ = _run_checkpoint((receipt1,))
    request2 = second_resolver.pending_requests(include_arguments=True)[0]
    assert request2["capability_id"] == "chatmem.github_create_checkpoint"

    receipt2 = _success_receipt(
        request2,
        "github_checkpoint_receipt",
        {"commit_sha": "checkpoint-commit"},
    )
    third, third_resolver, _ = _run_checkpoint((receipt1, receipt2))
    request3 = third_resolver.pending_requests(include_arguments=True)[0]
    assert request3["capability_id"] == "chatmem.github_update_pointer"
    assert request3["external_authority"] == "write"

    receipt3 = _success_receipt(
        request3,
        "github_pointer_update_receipt",
        {"commit_sha": "pointer-commit"},
    )
    final, final_resolver, _ = _run_checkpoint((receipt1, receipt2, receipt3))
    assert final["execution_status"] == "COMPLETE"
    assert final["oak"]["status"] == "PASS"
    assert final["actions_required"] == []
    assert len(final_resolver.consumed_receipt_ids) == 3
    ids = [item["capability_id"] for item in final["observations"]]
    assert ids == [
        "chatmem.validate_checkpoint",
        "chatmem.library_upload_bundle",
        "chatmem.github_create_checkpoint",
        "chatmem.github_update_pointer",
    ]


def test_read_capability_cannot_bind_to_mutating_external_action():
    cap = Capability(
        capability_id="unsafe.read.label",
        domains=("github",),
        consumes=("repo",),
        produces=("result",),
        authority="read",
    )
    binding = ExternalBinding(
        capability_id=cap.capability_id,
        connector="GitHub",
        action="merge_pull_request",
        external_authority="irreversible",
        argument_template={"repository_full_name": "$repo"},
    )
    validation = validate_external_bindings((cap,), (binding,))
    assert validation["status"] == "FAIL"
    assert "exceeds capability authority" in validation["errors"][0]


def test_make_external_request_fails_closed_on_authority_mismatch_even_without_manifest_validation():
    cap = Capability(
        capability_id="unsafe.write-through-read",
        domains=("github",),
        consumes=("repo",),
        produces=("result",),
        authority="read",
    )
    binding = ExternalBinding(
        capability_id=cap.capability_id,
        connector="GitHub",
        action="update_file",
        external_authority="write",
        argument_template={"repository_full_name": "$repo"},
    )
    try:
        make_external_request(cap, binding, {"repo": "owner/repo"})
    except ValueError as exc:
        assert "exceeds capability authority" in str(exc)
    else:
        raise AssertionError("authority mismatch must fail closed")


def test_non_mutating_request_rejects_receipt_claiming_remote_mutation():
    cap = Capability(
        capability_id="read.only",
        domains=("github",),
        consumes=("repo",),
        produces=("result",),
        authority="read",
    )
    binding = ExternalBinding(
        capability_id=cap.capability_id,
        connector="GitHub",
        action="fetch",
        external_authority="read",
        argument_template={"url": "$repo"},
    )
    request = make_external_request(cap, binding, {"repo": "https://example.invalid"})
    receipt = ExternalActionReceipt.from_dict(
        {
            "request_id": request.request_id,
            "capability_id": request.capability_id,
            "connector": request.connector,
            "action": request.action,
            "status": "SUCCESS",
            "outputs": {"result": "ok"},
            "mutation_performed": True,
        }
    )
    validation = validate_external_receipt(request, receipt)
    assert validation["status"] == "FAIL"
    assert "non-mutating external request" in validation["errors"][0]


def test_successful_write_receipt_must_attest_mutation_performed():
    cap = Capability(
        capability_id="write.remote",
        domains=("github",),
        consumes=("repo",),
        produces=("result",),
        authority="write",
    )
    binding = ExternalBinding(
        capability_id=cap.capability_id,
        connector="GitHub",
        action="update_file",
        external_authority="write",
        argument_template={"repository_full_name": "$repo"},
    )
    request = make_external_request(cap, binding, {"repo": "owner/repo"})
    receipt = ExternalActionReceipt.from_dict(
        {
            "request_id": request.request_id,
            "capability_id": request.capability_id,
            "connector": request.connector,
            "action": request.action,
            "status": "SUCCESS",
            "outputs": {"result": "ok"},
            "mutation_performed": False,
        }
    )
    validation = validate_external_receipt(request, receipt)
    assert validation["status"] == "FAIL"
    assert "lacks mutation_performed=true" in validation["errors"][0]
