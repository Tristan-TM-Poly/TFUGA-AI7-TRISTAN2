from __future__ import annotations

import json

from omega_web_hg_t.r05 import PolicyGate, RequestContext, compile_policy, policy_by_id

policy = compile_policy(policy_by_id("crossref"), as_of="2026-08-03")
gate = PolicyGate(policy)

request = gate.evaluate_request(
    RequestContext(
        route="rest_api",
        headers={"User-Agent": "Omega-Web-HG-R05-Demo/0.5"},
        environment={},
        requested_rps=0.5,
        contact_email="research@example.invalid",
    )
)

safe_record = {
    "source_id": "crossref",
    "record_id": "10.0000/example",
    "canonical_url": "https://doi.org/10.0000/example",
    "title": "Synthetic metadata fixture",
    "record_type": "article",
    "identifiers": {"doi": "10.0000/example"},
}
unsafe_record = {**safe_record, "abstract": "This field must not be persisted."}

safe_decision = gate.evaluate_record(safe_record)
unsafe_decision = gate.evaluate_record(unsafe_record)
redacted_decision = gate.evaluate_record(unsafe_record, mode="redact")
raw_storage, raw_storage_record = gate.evaluate_storage(
    object_id="synthetic-response",
    storage_level=2,
    content_class="raw_response",
)

print(
    json.dumps(
        {
            "policy": {
                "source_id": policy.source_id,
                "review_status": policy.review_status,
                "policy_digest": policy.policy_digest,
            },
            "request": request.to_dict(),
            "safe_record": safe_decision.to_dict(),
            "unsafe_record": unsafe_decision.to_dict(),
            "redacted_record": redacted_decision.to_dict(),
            "raw_storage": raw_storage.to_dict(),
            "storage_decision": raw_storage_record.to_dict(),
            "legal_advice_claimed": False,
            "permission_beyond_profile_claimed": False,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
