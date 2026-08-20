"""Fail-closed runtime gates for compiled Web-HG policies."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping

from .models import CompiledPolicy, GateDecision, GateViolation, StorageDecisionRecord


class PolicyViolation(RuntimeError):
    def __init__(self, decision: GateDecision):
        self.decision = decision
        details = "; ".join(item.message for item in decision.violations) or "policy denied action"
        super().__init__(details)


def _normalized_field(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _aliases(value: str) -> set[str]:
    normalized = _normalized_field(value)
    collapsed = normalized.replace("_", "")
    aliases = {normalized, collapsed}
    if normalized.endswith("s"):
        aliases.add(normalized[:-1])
        aliases.add(collapsed[:-1])
    else:
        aliases.add(normalized + "s")
        aliases.add(collapsed + "s")
    return aliases


def _matches(field: str, policy_fields: Iterable[str]) -> bool:
    field_aliases = _aliases(field)
    return any(field_aliases.intersection(_aliases(candidate)) for candidate in policy_fields)


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}"
            yield child, str(key), item
            yield from _walk(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _redact(value: Any, forbidden_fields: tuple[str, ...]) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _redact(item, forbidden_fields)
            for key, item in value.items()
            if not _matches(str(key), forbidden_fields)
        }
    if isinstance(value, list):
        return [_redact(item, forbidden_fields) for item in value]
    return deepcopy(value)


@dataclass(frozen=True)
class RequestContext:
    route: str
    headers: Mapping[str, str]
    environment: Mapping[str, str]
    requested_rps: float = 1.0
    contact_email: str | None = None


class PolicyGate:
    """Evaluate requests, normalized records and storage operations.

    The gate never silently upgrades a profile under human review into an
    allowed action. `redact` is explicit and still records every removed field.
    """

    def __init__(self, policy: CompiledPolicy):
        self.policy = policy

    def _decision(
        self,
        action: str,
        violations: list[GateViolation],
        warnings: list[GateViolation] | None = None,
        transformed_payload: dict[str, Any] | None = None,
    ) -> GateDecision:
        return GateDecision(
            source_id=self.policy.source_id,
            action=action,
            allowed=not violations,
            policy_digest=self.policy.policy_digest,
            violations=tuple(violations),
            warnings=tuple(warnings or ()),
            transformed_payload=transformed_payload,
        )

    def evaluate_request(self, context: RequestContext) -> GateDecision:
        violations: list[GateViolation] = []
        warnings: list[GateViolation] = []
        if self.policy.review_status != "pass":
            violations.append(GateViolation("POLICY_NOT_EXECUTABLE", f"policy review status is {self.policy.review_status}"))
        if context.route not in self.policy.allowed_routes:
            violations.append(GateViolation("ROUTE_NOT_ALLOWED", f"route {context.route!r} is not allowed"))

        header_map = {str(key).casefold(): str(value).strip() for key, value in context.headers.items()}
        if self.policy.identity_rules.get("user_agent_required") and not header_map.get("user-agent"):
            violations.append(GateViolation("USER_AGENT_REQUIRED", "a descriptive User-Agent header is required"))

        contact_mode = str(self.policy.identity_rules.get("contact_email", "optional"))
        contact = context.contact_email or header_map.get("from")
        if contact_mode == "required" and not contact:
            violations.append(GateViolation("CONTACT_EMAIL_REQUIRED", "a contact email is required"))
        elif contact_mode == "recommended" and not contact:
            warnings.append(GateViolation("CONTACT_EMAIL_RECOMMENDED", "a contact email is recommended", severity="warning"))
        elif contact_mode == "forbidden" and contact:
            violations.append(GateViolation("CONTACT_EMAIL_FORBIDDEN", "contact email must not be transmitted"))

        missing = [name for name in self.policy.required_environment if not str(context.environment.get(name, "")).strip()]
        for name in missing:
            violations.append(GateViolation("REQUIRED_ENVIRONMENT_MISSING", f"required environment variable {name} is missing", path=name))

        if context.requested_rps <= 0:
            violations.append(GateViolation("INVALID_REQUEST_RATE", "requested_rps must be positive"))
        recommended = float(self.policy.rate_rules.get("recommended_rps") or 1.0)
        maximum = self.policy.rate_rules.get("maximum_rps")
        if maximum is not None and context.requested_rps > float(maximum):
            violations.append(GateViolation("MAXIMUM_RATE_EXCEEDED", f"requested rate {context.requested_rps} exceeds maximum {maximum}"))
        elif context.requested_rps > recommended:
            warnings.append(GateViolation("RECOMMENDED_RATE_EXCEEDED", f"requested rate {context.requested_rps} exceeds recommended {recommended}", severity="warning"))
        return self._decision("request", violations, warnings)

    def authorize_request(self, context: RequestContext) -> GateDecision:
        decision = self.evaluate_request(context)
        if not decision.allowed:
            raise PolicyViolation(decision)
        return decision

    def evaluate_record(self, record: Mapping[str, Any], *, mode: str | None = None) -> GateDecision:
        enforcement = mode or self.policy.enforcement_mode
        if enforcement not in {"reject", "redact"}:
            raise ValueError("mode must be reject or redact")
        violations: list[GateViolation] = []
        warnings: list[GateViolation] = []
        forbidden_hits: list[tuple[str, str]] = []
        for path, key, _ in _walk(record):
            if _matches(key, self.policy.forbidden_fields):
                forbidden_hits.append((path, key))
        for path, key in forbidden_hits:
            item = GateViolation("FORBIDDEN_FIELD", f"field {key!r} is forbidden by policy", path=path)
            if enforcement == "reject":
                violations.append(item)
            else:
                warnings.append(GateViolation(item.code, item.message, item.path, "warning"))

        required_fields = tuple(self.policy.attribution_rules.get("required_fields") or ())
        if self.policy.attribution_rules.get("required"):
            top_level = {str(key) for key in record}
            for field in required_fields:
                if field not in top_level or record.get(field) in {None, ""}:
                    violations.append(GateViolation("ATTRIBUTION_FIELD_MISSING", f"required attribution field {field!r} is missing", path=f"$.{field}"))

        if self.policy.allowed_fields:
            exempt = {"digest", "epistemic_status", "request_receipt_id", "source_payload_sha256"}
            for key in record:
                if str(key) in exempt:
                    continue
                if not _matches(str(key), self.policy.allowed_fields) and not _matches(str(key), required_fields):
                    item = GateViolation("FIELD_NOT_ALLOWLISTED", f"field {key!r} is not allowlisted", path=f"$.{key}")
                    if enforcement == "reject":
                        violations.append(item)
                    else:
                        warnings.append(GateViolation(item.code, item.message, item.path, "warning"))

        transformed = _redact(record, self.policy.forbidden_fields) if enforcement == "redact" else None
        if transformed is not None and self.policy.allowed_fields:
            allowed = set(self.policy.allowed_fields).union(required_fields).union(
                {"digest", "epistemic_status", "request_receipt_id", "source_payload_sha256"}
            )
            transformed = {key: value for key, value in transformed.items() if _matches(str(key), allowed)}
        return self._decision("record_persistence", violations, warnings, transformed)

    def enforce_record(self, record: Mapping[str, Any], *, mode: str | None = None) -> dict[str, Any]:
        decision = self.evaluate_record(record, mode=mode)
        if not decision.allowed:
            raise PolicyViolation(decision)
        return decision.transformed_payload if decision.transformed_payload is not None else deepcopy(dict(record))

    def evaluate_storage(
        self,
        *,
        object_id: str,
        storage_level: int,
        content_class: str,
        encrypted_at_rest: bool = False,
    ) -> tuple[GateDecision, StorageDecisionRecord]:
        violations: list[GateViolation] = []
        if self.policy.review_status != "pass":
            violations.append(GateViolation("POLICY_NOT_EXECUTABLE", "storage denied while policy requires review"))
        if content_class in self.policy.forbidden_content:
            violations.append(GateViolation("CONTENT_CLASS_FORBIDDEN", f"content class {content_class!r} is forbidden"))
        retention_key = "raw_response" if content_class == "raw_response" else "normalized_metadata"
        retention_mode = str(self.policy.retention_rules.get(retention_key, "forbidden"))
        if retention_mode == "forbidden":
            violations.append(GateViolation("RETENTION_FORBIDDEN", f"retention for {content_class!r} is forbidden"))
        if storage_level == 3 and not encrypted_at_rest:
            violations.append(GateViolation("ENCRYPTION_REQUIRED", "storage level 3 requires encryption at rest"))
        decision = self._decision("storage", violations)
        record = StorageDecisionRecord(
            object_id=object_id,
            source_id=self.policy.source_id,
            storage_level=storage_level,
            allowed=decision.allowed,
            reason="allowed_by_compiled_policy" if decision.allowed else ";".join(item.code for item in violations),
            policy_digest=self.policy.policy_digest,
            retention_mode=retention_mode,
            maximum_days=self.policy.retention_rules.get("maximum_days"),
            encrypted_at_rest=encrypted_at_rest,
        )
        return decision, record
