from __future__ import annotations

from omega_capability_os_t.core import Capability, Intent, load_registry, plan
from omega_capability_os_t.external import (
    ExternalActionReceipt,
    ExternalBinding,
    ExternalResolver,
    load_external_bindings,
    make_external_request,
    validate_external_bindings,
    validate_external_receipt,
)
from omega_capability_os_t.runtime import CapabilityRuntime


def _capability(*, authority: str = "read", alternatives: tuple[str, ...] = ()) -> Capability:
    return Capability(
        capability_id="github.fetch_pr",
        domains=("github", "software"),
        consumes=("repo", "pr_number"),
        produces=("pr_metadata", "commit_sha"),
        authority=authority,
        quality=0.99,
        information_gain=0.95,
        verifiability=0.99,
        reuse=0.95,
        cost=0.10,
        latency=0.10,
        risk=0.05,
        alternatives=alternatives,
    )


def _binding() -> ExternalBinding:
    return ExternalBinding(
        capability_id="github.fetch_pr",
        connector="GitHub",
        action="fetch_pr",
        argument_template={"repo_full_name": "$repo", "pr_number": "$pr_number"},
    )


def _intent(*, allow_mutation: bool = False) -> Intent:
    return Intent(
        intent_id="EXT-DEMO",
        available_inputs=("repo", "pr_number"),
        required_outputs=("pr_metadata", "commit_sha"),
        domains=("github", "software"),
        allow_mutation=allow_mutation,
    )


def _values() -> dict[str, object]:
    return {"repo": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2", "pr_number": 417}


def test_binding_validation_accepts_declared_input_tokens():
    result = validate_external_bindings((_capability(),), (_binding(),))
    assert result["status"] == "PASS", result
    assert result["binding_count"] == 1


def test_binding_validation_rejects_undeclared_template_token():
    bad = ExternalBinding(
        capability_id="github.fetch_pr",
        connector="GitHub",
        action="fetch_pr",
        argument_template={"repo_full_name": "$repo", "secret": "$undeclared"},
    )
    result = validate_external_bindings((_capability(),), (bad,))
    assert result["status"] == "FAIL"
    assert "undeclared" in result["errors"][0]


def test_external_request_redacts_arguments_by_default():
    request = make_external_request(
        _capability(),
        _binding(),
        _values(),
        candidate_sha="abc123",
        plan_fingerprint="plan123",
    )
    audit = request.to_dict()
    assert audit["arguments_redacted"] is True
    assert "arguments" not in audit
    assert audit["arguments_fingerprint"]
    execution = request.execution_payload()
    assert execution["arguments"]["pr_number"] == 417
    assert execution["arguments"]["repo_full_name"].endswith("TFUGA-AI7-TRISTAN2")


def test_external_request_id_is_deterministic_and_input_sensitive():
    first = make_external_request(_capability(), _binding(), _values(), candidate_sha="sha")
    second = make_external_request(_capability(), _binding(), _values(), candidate_sha="sha")
    changed = make_external_request(
        _capability(),
        _binding(),
        {"repo": _values()["repo"], "pr_number": 418},
        candidate_sha="sha",
    )
    assert first.request_id == second.request_id
    assert first.request_id != changed.request_id


def test_runtime_suspends_with_normalized_external_request_not_fake_success():
    cap = _capability()
    resolver = ExternalResolver((_binding(),), candidate_sha="abc123")
    receipt = CapabilityRuntime(resolver=resolver).execute(
        (cap,),
        _intent(),
        initial_values=_values(),
        candidate_sha="abc123",
        evidence_sha="abc123",
    )
    assert receipt["execution_status"] == "HOLD"
    assert receipt["oak"]["status"] == "HOLD"
    action = receipt["actions_required"][0]
    request = action["external_request"]
    assert request["connector"] == "GitHub"
    assert request["action"] == "fetch_pr"
    assert request["arguments_redacted"] is True
    assert "arguments" not in request
    assert resolver.pending_requests(include_arguments=True)[0]["arguments"]["pr_number"] == 417


def test_external_receipt_resumes_same_plan_and_reaches_oak_pass():
    cap = _capability()
    first_resolver = ExternalResolver((_binding(),), candidate_sha="abc123")
    first = CapabilityRuntime(resolver=first_resolver).execute(
        (cap,),
        _intent(),
        initial_values=_values(),
        candidate_sha="abc123",
        evidence_sha="abc123",
    )
    assert first["oak"]["status"] == "HOLD"
    request = first_resolver.pending_requests(include_arguments=True)[0]
    external_receipt = {
        "request_id": request["request_id"],
        "capability_id": "github.fetch_pr",
        "connector": "GitHub",
        "action": "fetch_pr",
        "status": "SUCCESS",
        "outputs": {
            "pr_metadata": {"number": 417, "state": "open"},
            "commit_sha": "abc123",
        },
        "sources": ["github://pull/417"],
        "observed_candidate_sha": "abc123",
    }
    resumed = ExternalResolver(
        (_binding(),),
        receipts=(external_receipt,),
        candidate_sha="abc123",
    )
    receipt = CapabilityRuntime(resolver=resumed).execute(
        (cap,),
        _intent(),
        initial_values=_values(),
        candidate_sha="abc123",
        evidence_sha="abc123",
    )
    assert receipt["execution_status"] == "COMPLETE"
    assert receipt["oak"]["status"] == "PASS"
    assert receipt["actions_required"] == []
    assert receipt["health_after"]["github.fetch_pr"]["status"] == "PASS"
    assert resumed.consumed_receipt_ids == (request["request_id"],)


def test_success_receipt_missing_declared_output_is_rejected():
    request = make_external_request(_capability(), _binding(), _values())
    receipt = ExternalActionReceipt.from_dict(
        {
            "request_id": request.request_id,
            "capability_id": request.capability_id,
            "connector": request.connector,
            "action": request.action,
            "status": "SUCCESS",
            "outputs": {"pr_metadata": {"number": 417}},
        }
    )
    result = validate_external_receipt(request, receipt)
    assert result["status"] == "FAIL"
    assert result["missing_outputs"] == ["commit_sha"]


def test_external_failure_can_recover_through_safe_local_fallback():
    primary = _capability(alternatives=("local.fallback",))
    fallback = Capability(
        capability_id="local.fallback",
        domains=("github", "software"),
        consumes=("repo", "pr_number"),
        produces=("pr_metadata", "commit_sha"),
        authority="read",
        quality=0.2,
    )
    request = make_external_request(primary, _binding(), _values(), candidate_sha="sha")
    failed = {
        "request_id": request.request_id,
        "capability_id": primary.capability_id,
        "connector": "GitHub",
        "action": "fetch_pr",
        "status": "FAILURE",
        "outputs": {},
        "error": "provider unavailable",
    }
    resolver = ExternalResolver((_binding(),), receipts=(failed,), candidate_sha="sha")
    runtime = CapabilityRuntime(
        {
            "local.fallback": lambda cap, inputs: {
                "pr_metadata": {"fallback": True},
                "commit_sha": "sha",
            }
        },
        resolver=resolver,
    )
    receipt = runtime.execute(
        (primary, fallback),
        _intent(),
        initial_values=_values(),
        candidate_sha="sha",
        evidence_sha="sha",
    )
    assert receipt["oak"]["status"] == "PASS"
    assert receipt["observations"][0]["outcome"] == "RECOVERED"
    assert receipt["observations"][0]["fallback"] == "local.fallback"
    assert receipt["health_after"]["github.fetch_pr"]["m_minus"] == 1
    assert receipt["health_after"]["local.fallback"]["m_plus"] == 1


def test_write_capability_does_not_emit_external_request_without_mutation_permission():
    cap = _capability(authority="write")
    resolver = ExternalResolver((_binding(),), candidate_sha="sha")
    receipt = CapabilityRuntime(resolver=resolver).execute(
        (cap,),
        _intent(allow_mutation=False),
        initial_values=_values(),
        candidate_sha="sha",
        evidence_sha="sha",
    )
    assert plan((cap,), _intent())["status"] == "HOLD"
    assert receipt["actions_required"] == []
    assert resolver.pending_requests() == []


def test_real_example_binding_manifest_matches_registry_shape():
    registry = load_registry(
        {
            "capabilities": [
                {
                    "id": "github.fetch_pr",
                    "domains": ["github"],
                    "consumes": ["repo", "pr_number"],
                    "produces": ["pr_metadata", "commit_sha"],
                    "authority": "read",
                }
            ]
        }
    )
    bindings = load_external_bindings(
        {
            "bindings": [
                {
                    "capability_id": "github.fetch_pr",
                    "connector": "GitHub",
                    "action": "fetch_pr",
                    "argument_template": {
                        "repo_full_name": "$repo",
                        "pr_number": "$pr_number",
                    },
                }
            ]
        }
    )
    assert validate_external_bindings(registry, bindings)["status"] == "PASS"
