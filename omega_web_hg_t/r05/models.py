"""Typed policy objects for Ω-WEB-HG-T∞ R0.5.

R0.5 treats a policy document as evidence used to build a technical gate. It
never treats the compiled result as legal advice or as permission beyond the
explicitly represented scope.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

POLICY_STATUSES = {
    "verified",
    "inferred",
    "ambiguous",
    "expired",
    "human_review_required",
}
REVIEW_STATUSES = {"pass", "fail", "human_review"}
RETENTION_MODES = {"forbidden", "ephemeral", "allowed"}
CONTACT_MODES = {"required", "recommended", "optional", "forbidden"}
ENFORCEMENT_MODES = {"reject", "redact"}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_object(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise TypeError("expected a list or tuple")
    result = tuple(str(item).strip() for item in value if str(item).strip())
    if len(set(result)) != len(result):
        raise ValueError("duplicate values are not allowed")
    return result


def _mapping(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError("expected a mapping")
    return {str(key): item for key, item in value.items()}


def _iso_date(value: str | None) -> str | None:
    if value is None:
        return None
    date.fromisoformat(value)
    return value


@dataclass(frozen=True)
class RequestRatePolicy:
    recommended_rps: float = 1.0
    maximum_rps: float | None = None
    burst: int = 1
    retry_after_required: bool = True

    def __post_init__(self) -> None:
        if self.recommended_rps <= 0:
            raise ValueError("recommended_rps must be positive")
        if self.maximum_rps is not None and self.maximum_rps <= 0:
            raise ValueError("maximum_rps must be positive")
        if self.maximum_rps is not None and self.recommended_rps > self.maximum_rps:
            raise ValueError("recommended_rps cannot exceed maximum_rps")
        if self.burst < 1:
            raise ValueError("burst must be at least one")

    @classmethod
    def from_mapping(cls, value: object) -> "RequestRatePolicy":
        data = _mapping(value)
        return cls(
            recommended_rps=float(data.get("recommended_rps", 1.0)),
            maximum_rps=float(data["maximum_rps"]) if data.get("maximum_rps") is not None else None,
            burst=int(data.get("burst", 1)),
            retry_after_required=bool(data.get("retry_after_required", True)),
        )


@dataclass(frozen=True)
class RequiredIdentityPolicy:
    user_agent_required: bool = True
    contact_email: str = "recommended"

    def __post_init__(self) -> None:
        if self.contact_email not in CONTACT_MODES:
            raise ValueError(f"invalid contact_email mode: {self.contact_email}")

    @classmethod
    def from_mapping(cls, value: object) -> "RequiredIdentityPolicy":
        data = _mapping(value)
        return cls(
            user_agent_required=bool(data.get("user_agent_required", True)),
            contact_email=str(data.get("contact_email", "recommended")),
        )


@dataclass(frozen=True)
class RetentionPolicy:
    raw_response: str = "forbidden"
    normalized_metadata: str = "allowed"
    maximum_days: int | None = None
    encrypted_at_rest: bool = False

    def __post_init__(self) -> None:
        if self.raw_response not in RETENTION_MODES:
            raise ValueError(f"invalid raw_response retention: {self.raw_response}")
        if self.normalized_metadata not in RETENTION_MODES:
            raise ValueError(f"invalid normalized_metadata retention: {self.normalized_metadata}")
        if self.maximum_days is not None and self.maximum_days < 1:
            raise ValueError("maximum_days must be positive")

    @classmethod
    def from_mapping(cls, value: object) -> "RetentionPolicy":
        data = _mapping(value)
        return cls(
            raw_response=str(data.get("raw_response", "forbidden")),
            normalized_metadata=str(data.get("normalized_metadata", "allowed")),
            maximum_days=int(data["maximum_days"]) if data.get("maximum_days") is not None else None,
            encrypted_at_rest=bool(data.get("encrypted_at_rest", False)),
        )


@dataclass(frozen=True)
class AttributionPolicy:
    required: bool = True
    required_fields: tuple[str, ...] = ("source_id", "canonical_url")

    @classmethod
    def from_mapping(cls, value: object) -> "AttributionPolicy":
        data = _mapping(value)
        return cls(
            required=bool(data.get("required", True)),
            required_fields=_tuple(data.get("required_fields", ("source_id", "canonical_url"))),
        )


@dataclass(frozen=True)
class ReviewPolicy:
    review_after_days: int = 30
    next_review_at: str | None = None

    def __post_init__(self) -> None:
        if self.review_after_days < 1:
            raise ValueError("review_after_days must be positive")
        _iso_date(self.next_review_at)

    @classmethod
    def from_mapping(cls, value: object) -> "ReviewPolicy":
        data = _mapping(value)
        return cls(
            review_after_days=int(data.get("review_after_days", 30)),
            next_review_at=_iso_date(str(data["next_review_at"])) if data.get("next_review_at") else None,
        )


@dataclass(frozen=True)
class PolicyProfile:
    source_id: str
    policy_url: str
    policy_observed_at: str
    policy_status: str
    allowed_routes: tuple[str, ...]
    allowed_content: tuple[str, ...] = ("metadata",)
    allowed_fields: tuple[str, ...] = ()
    forbidden_content: tuple[str, ...] = ("full_text",)
    forbidden_fields: tuple[str, ...] = ("abstract", "body", "full_text")
    required_environment: tuple[str, ...] = ()
    request_rate: RequestRatePolicy = field(default_factory=RequestRatePolicy)
    required_identity: RequiredIdentityPolicy = field(default_factory=RequiredIdentityPolicy)
    retention: RetentionPolicy = field(default_factory=RetentionPolicy)
    attribution: AttributionPolicy = field(default_factory=AttributionPolicy)
    review: ReviewPolicy = field(default_factory=ReviewPolicy)
    enforcement_mode: str = "reject"
    jurisdiction: str | None = None
    notes: tuple[str, ...] = ()
    schema_version: str = "omega-web-hg-policy-profile/1.0"

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")
        if not self.policy_url.startswith(("https://", "http://")):
            raise ValueError("policy_url must be an HTTP(S) URL")
        _iso_date(self.policy_observed_at)
        if self.policy_status not in POLICY_STATUSES:
            raise ValueError(f"invalid policy_status: {self.policy_status}")
        if not self.allowed_routes:
            raise ValueError("at least one allowed route is required")
        if self.enforcement_mode not in ENFORCEMENT_MODES:
            raise ValueError(f"invalid enforcement_mode: {self.enforcement_mode}")
        overlap = set(self.allowed_fields).intersection(self.forbidden_fields)
        if overlap:
            raise ValueError(f"fields cannot be both allowed and forbidden: {sorted(overlap)}")

    @property
    def digest(self) -> str:
        return digest_object(self.to_dict(include_digest=False))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if include_digest:
            payload["profile_digest"] = self.digest
        return payload

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PolicyProfile":
        data = dict(value)
        return cls(
            source_id=str(data["source_id"]),
            policy_url=str(data["policy_url"]),
            policy_observed_at=str(data["policy_observed_at"]),
            policy_status=str(data["policy_status"]),
            allowed_routes=_tuple(data.get("allowed_routes")),
            allowed_content=_tuple(data.get("allowed_content", ("metadata",))),
            allowed_fields=_tuple(data.get("allowed_fields")),
            forbidden_content=_tuple(data.get("forbidden_content", ("full_text",))),
            forbidden_fields=_tuple(data.get("forbidden_fields", ("abstract", "body", "full_text"))),
            required_environment=_tuple(data.get("required_environment")),
            request_rate=RequestRatePolicy.from_mapping(data.get("request_rate")),
            required_identity=RequiredIdentityPolicy.from_mapping(data.get("required_identity")),
            retention=RetentionPolicy.from_mapping(data.get("retention")),
            attribution=AttributionPolicy.from_mapping(data.get("attribution")),
            review=ReviewPolicy.from_mapping(data.get("review")),
            enforcement_mode=str(data.get("enforcement_mode", "reject")),
            jurisdiction=str(data["jurisdiction"]) if data.get("jurisdiction") is not None else None,
            notes=_tuple(data.get("notes")),
            schema_version=str(data.get("schema_version", "omega-web-hg-policy-profile/1.0")),
        )


@dataclass(frozen=True)
class CompiledPolicy:
    source_id: str
    allowed_routes: tuple[str, ...]
    allowed_content: tuple[str, ...]
    allowed_fields: tuple[str, ...]
    forbidden_content: tuple[str, ...]
    forbidden_fields: tuple[str, ...]
    retention_rules: dict[str, Any]
    rate_rules: dict[str, Any]
    identity_rules: dict[str, Any]
    attribution_rules: dict[str, Any]
    required_environment: tuple[str, ...]
    enforcement_mode: str
    review_status: str
    review_reasons: tuple[str, ...]
    policy_url: str
    policy_observed_at: str
    evaluated_as_of: str
    source_profile_digest: str
    schema_version: str = "omega-web-hg-compiled-policy/1.0"

    def __post_init__(self) -> None:
        if self.review_status not in REVIEW_STATUSES:
            raise ValueError(f"invalid review_status: {self.review_status}")

    @property
    def policy_digest(self) -> str:
        return digest_object(self.to_dict(include_digest=False))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if include_digest:
            payload["policy_digest"] = self.policy_digest
        return payload


@dataclass(frozen=True)
class GateViolation:
    code: str
    message: str
    path: str | None = None
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GateDecision:
    source_id: str
    action: str
    allowed: bool
    policy_digest: str
    violations: tuple[GateViolation, ...] = ()
    warnings: tuple[GateViolation, ...] = ()
    transformed_payload: dict[str, Any] | None = None
    decided_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def decision_digest(self) -> str:
        return digest_object(self.to_dict(include_digest=False))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if include_digest:
            payload["decision_digest"] = self.decision_digest
        return payload


@dataclass(frozen=True)
class StorageDecisionRecord:
    object_id: str
    source_id: str
    storage_level: int
    allowed: bool
    reason: str
    policy_digest: str
    retention_mode: str
    maximum_days: int | None = None
    encrypted_at_rest: bool = False

    def __post_init__(self) -> None:
        if self.storage_level not in {0, 1, 2, 3}:
            raise ValueError("storage_level must be 0, 1, 2 or 3")
        if self.retention_mode not in RETENTION_MODES:
            raise ValueError("invalid retention_mode")

    @property
    def digest(self) -> str:
        return digest_object(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "digest": self.digest}
