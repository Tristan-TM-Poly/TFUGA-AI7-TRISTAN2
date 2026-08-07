"""Policy-bound integration layer for R0.4 MAX adapters.

This module does not perform network access. It authorizes request construction,
then gates every normalized record produced by an existing adapter parser.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from omega_web_hg_t.r04.max_adapters import Adapter, MAX_ADAPTERS

from .builtin_policies import policy_by_id
from .compiler import compile_policy
from .gate import PolicyGate, PolicyViolation, RequestContext
from .models import CompiledPolicy, GateDecision, digest_object

ROUTE_BY_SOURCE: dict[str, str] = {
    "wikimedia": "mediawiki_api",
    "crossref": "rest_api",
    "pubmed": "eutils",
    "pmc_open": "oai_pmh",
    "nist_pdr": "rmm_api",
    "nasa_open": "rest_api",
    "cern_open_data": "rest_api",
    "usgs": "fdsn_event_api",
    "esa_cci": "opensearch",
    "canada_open": "ckan_api",
    "openalex": "rest_api",
}
SECRET_QUERY_MARKERS = ("api_key", "apikey", "key", "token", "secret", "password")


class AdapterPolicyBindingError(ValueError):
    """Raised when an adapter and policy cannot be safely bound."""


def _public_url(url: str) -> str:
    parsed = urlparse(url)
    redacted = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized = key.casefold().replace("-", "_")
        if any(marker in normalized for marker in SECRET_QUERY_MARKERS):
            redacted.append((key, "REDACTED"))
        else:
            redacted.append((key, value))
    return urlunparse(parsed._replace(query=urlencode(redacted, doseq=True)))


@dataclass(frozen=True)
class AuthorizedRequest:
    source_id: str
    route: str
    url: str
    page: int
    size: int
    binding_digest: str
    decision: GateDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "route": self.route,
            "public_url": _public_url(self.url),
            "url_sha256": sha256(self.url.encode("utf-8")).hexdigest(),
            "secret_query_values_persisted": False,
            "page": self.page,
            "size": self.size,
            "binding_digest": self.binding_digest,
            "decision": self.decision.to_dict(),
        }


@dataclass(frozen=True)
class GatedParseBatch:
    source_id: str
    receipt_id: str
    body_sha256: str
    binding_digest: str
    records: tuple[dict[str, Any], ...]
    decisions: tuple[GateDecision, ...]
    rejected_count: int
    raw_body_persisted: bool = False
    full_text_collected: bool = False

    @property
    def batch_digest(self) -> str:
        return digest_object(self.to_dict(include_digest=False))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload = {
            "source_id": self.source_id,
            "receipt_id": self.receipt_id,
            "body_sha256": self.body_sha256,
            "binding_digest": self.binding_digest,
            "records": list(self.records),
            "decisions": [item.to_dict() for item in self.decisions],
            "rejected_count": self.rejected_count,
            "raw_body_persisted": self.raw_body_persisted,
            "full_text_collected": self.full_text_collected,
        }
        if include_digest:
            payload["batch_digest"] = self.batch_digest
        return payload


@dataclass(frozen=True)
class PolicyBoundAdapter:
    adapter: Adapter
    policy: CompiledPolicy
    route: str

    @property
    def binding_digest(self) -> str:
        return digest_object(
            {
                "source_id": self.adapter.source_id,
                "adapter_name": self.adapter.name,
                "route": self.route,
                "adapter_policy_url": self.adapter.policy_url,
                "adapter_required_env": list(self.adapter.required_env),
                "adapter_requests_per_second": self.adapter.requests_per_second,
                "adapter_metadata_only": self.adapter.metadata_only,
                "policy_digest": self.policy.policy_digest,
            }
        )

    def authorize_request(
        self,
        query: str,
        page: int,
        size: int,
        *,
        environment: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        contact_email: str | None = None,
    ) -> AuthorizedRequest:
        if page < 1 or size < 1:
            raise ValueError("page and size must be positive")
        env = dict(environment or {})
        request_headers = dict(headers or {"User-Agent": "Omega-Web-HG-R05/0.5"})
        decision = PolicyGate(self.policy).authorize_request(
            RequestContext(
                route=self.route,
                headers=request_headers,
                environment=env,
                requested_rps=self.adapter.requests_per_second,
                contact_email=contact_email,
            )
        )
        url = self.adapter.url_builder(query, page, size, env)
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise AdapterPolicyBindingError("authorized adapters must produce an absolute HTTPS URL")
        return AuthorizedRequest(
            source_id=self.adapter.source_id,
            route=self.route,
            url=url,
            page=page,
            size=size,
            binding_digest=self.binding_digest,
            decision=decision,
        )

    def parse_and_gate(
        self,
        body: bytes,
        receipt_id: str,
        *,
        mode: str | None = None,
        reject_batch_on_violation: bool = True,
    ) -> GatedParseBatch:
        records = self.adapter.parser(body, receipt_id)
        accepted: list[dict[str, Any]] = []
        decisions: list[GateDecision] = []
        rejected = 0
        gate = PolicyGate(self.policy)
        for record in records:
            if not hasattr(record, "to_dict"):
                raise AdapterPolicyBindingError("adapter parser returned a non-normalizable object")
            payload = record.to_dict()
            decision = gate.evaluate_record(payload, mode=mode)
            decisions.append(decision)
            if decision.allowed:
                accepted.append(
                    decision.transformed_payload
                    if decision.transformed_payload is not None
                    else payload
                )
            else:
                rejected += 1
                if reject_batch_on_violation:
                    raise PolicyViolation(decision)
        return GatedParseBatch(
            source_id=self.adapter.source_id,
            receipt_id=receipt_id,
            body_sha256=sha256(body).hexdigest(),
            binding_digest=self.binding_digest,
            records=tuple(accepted),
            decisions=tuple(decisions),
            rejected_count=rejected,
        )


def bind_adapter(adapter: Adapter, *, as_of: str = "2026-08-03") -> PolicyBoundAdapter:
    try:
        profile = policy_by_id(adapter.source_id)
    except KeyError as exc:
        raise AdapterPolicyBindingError(f"no R0.5 policy profile for adapter {adapter.source_id}") from exc
    policy = compile_policy(profile, as_of=as_of)
    route = ROUTE_BY_SOURCE.get(adapter.source_id)
    errors: list[str] = []
    if route is None:
        errors.append("route_binding_missing")
    elif route not in policy.allowed_routes:
        errors.append("bound_route_not_allowed")
    if policy.review_status != "pass":
        errors.append(f"policy_review_status_{policy.review_status}")
    if adapter.policy_url != policy.policy_url:
        errors.append("policy_url_mismatch")
    if not adapter.metadata_only or "metadata" not in policy.allowed_content:
        errors.append("metadata_only_contract_missing")
    if not set(adapter.required_env).issubset(set(policy.required_environment)):
        errors.append("adapter_environment_not_covered")
    maximum = policy.rate_rules.get("maximum_rps")
    if maximum is not None and adapter.requests_per_second > float(maximum):
        errors.append("adapter_rate_exceeds_policy_maximum")
    if errors:
        raise AdapterPolicyBindingError(
            f"cannot bind {adapter.source_id}: {','.join(sorted(errors))}"
        )
    assert route is not None
    return PolicyBoundAdapter(adapter=adapter, policy=policy, route=route)


def bind_all_r04_adapters(*, as_of: str = "2026-08-03") -> tuple[PolicyBoundAdapter, ...]:
    return tuple(bind_adapter(adapter, as_of=as_of) for adapter in MAX_ADAPTERS)


def audit_r04_bindings(*, as_of: str = "2026-08-03") -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for adapter in MAX_ADAPTERS:
        try:
            bound = bind_adapter(adapter, as_of=as_of)
            rows.append(
                {
                    "source_id": adapter.source_id,
                    "route": bound.route,
                    "binding_digest": bound.binding_digest,
                    "policy_digest": bound.policy.policy_digest,
                    "required_environment": list(bound.policy.required_environment),
                }
            )
        except AdapterPolicyBindingError as exc:
            failures.append({"source_id": adapter.source_id, "error": str(exc)})
    return {
        "schema": "omega-web-hg-r05-r04-binding-audit/1.0",
        "as_of": as_of,
        "adapter_count": len(MAX_ADAPTERS),
        "bound_count": len(rows),
        "status": "PASS" if not failures else "FAIL",
        "bindings": rows,
        "failures": failures,
        "raw_body_persisted": False,
        "full_text_collected": False,
        "binding_audit_is_network_execution": False,
        "audit_digest": digest_object({"as_of": as_of, "bindings": rows, "failures": failures}),
    }
