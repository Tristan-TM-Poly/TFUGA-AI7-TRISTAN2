"""Canonical event envelope for Ω-DISCOVERY-KERNEL-T∞.

R0.2 delegates event semantics to the explicit Ω64 catalog.  The envelope is
append-only, deterministic, hash-verified, unit-aware, and conservative: an
event proves that a workflow record exists, not that its interpretation is
scientifically correct.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from .catalog import EVENT_TYPES, event_spec


OAK_STATUSES = {
    "IDEA",
    "ACTIVE",
    "FORMALIZED",
    "IMPLEMENTED",
    "SIMULATED",
    "DEMONSTRATED",
    "MEASURED",
    "CANONICAL",
    "CERTIFIED_MATH",
    "CERTIFIED_COMPUTATIONAL",
    "CERTIFIED_PHYSICS",
    "REFUTED",
    "REFORMULATED",
    "ARCHIVED",
}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def stable_id(prefix: str, *parts: object) -> str:
    raw = "\x1f".join(canonical_json(part) for part in parts).encode("utf-8")
    return f"{prefix}_{sha256(raw).hexdigest()[:24]}"


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _event_hash(payload: Mapping[str, Any]) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DiscoveryEvent:
    event_id: str
    event_type: str
    subject_id: str
    timestamp: str
    parent_ids: tuple[str, ...] = ()
    source_hash: str | None = None
    provenance: tuple[str, ...] = ()
    domain: str = "cross-domain"
    status: str = "candidate"
    payload: Mapping[str, Any] = field(default_factory=dict)
    units: Mapping[str, str] = field(default_factory=dict)
    uncertainty: Mapping[str, float] = field(default_factory=dict)
    human_approval: bool = False
    reversible: bool = True
    event_hash: str = ""

    @classmethod
    def create(
        cls,
        event_type: str,
        subject_id: str,
        timestamp: str,
        *,
        parent_ids: Sequence[str] = (),
        source_hash: str | None = None,
        provenance: Sequence[str] = (),
        domain: str = "cross-domain",
        status: str = "candidate",
        payload: Mapping[str, Any] | None = None,
        units: Mapping[str, str] | None = None,
        uncertainty: Mapping[str, float] | None = None,
        human_approval: bool = False,
        reversible: bool | None = None,
    ) -> "DiscoveryEvent":
        spec = event_spec(event_type)
        normalized_payload = dict(payload or {})
        normalized_units = {str(key): str(value) for key, value in (units or {}).items()}
        normalized_uncertainty = {str(key): float(value) for key, value in (uncertainty or {}).items()}
        normalized_parents = tuple(str(item) for item in parent_ids)
        normalized_provenance = tuple(str(item) for item in provenance)
        normalized_timestamp = parse_timestamp(timestamp).isoformat().replace("+00:00", "Z")
        normalized_reversible = spec.reversible_default if reversible is None else bool(reversible)
        event_id = stable_id(
            "evt",
            event_type,
            subject_id,
            normalized_timestamp,
            normalized_parents,
            normalized_payload,
        )
        event = cls(
            event_id=event_id,
            event_type=event_type,
            subject_id=str(subject_id),
            timestamp=normalized_timestamp,
            parent_ids=normalized_parents,
            source_hash=source_hash,
            provenance=normalized_provenance,
            domain=str(domain),
            status=str(status),
            payload=normalized_payload,
            units=normalized_units,
            uncertainty=normalized_uncertainty,
            human_approval=bool(human_approval),
            reversible=normalized_reversible,
        )
        return cls(**{**event.to_dict(), "event_hash": event.computed_hash()})

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DiscoveryEvent":
        return cls(
            event_id=str(value["event_id"]),
            event_type=str(value["event_type"]),
            subject_id=str(value["subject_id"]),
            timestamp=str(value["timestamp"]),
            parent_ids=tuple(value.get("parent_ids", ())),
            source_hash=value.get("source_hash"),
            provenance=tuple(value.get("provenance", ())),
            domain=str(value.get("domain", "cross-domain")),
            status=str(value.get("status", "candidate")),
            payload=dict(value.get("payload", {})),
            units={str(key): str(item) for key, item in dict(value.get("units", {})).items()},
            uncertainty={str(key): float(item) for key, item in dict(value.get("uncertainty", {})).items()},
            human_approval=bool(value.get("human_approval", False)),
            reversible=bool(value.get("reversible", True)),
            event_hash=str(value.get("event_hash", "")),
        )

    def hash_payload(self) -> dict[str, Any]:
        value = self.to_dict()
        value.pop("event_hash", None)
        return value

    def computed_hash(self) -> str:
        return _event_hash(self.hash_payload())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.event_type not in EVENT_TYPES:
            issues.append(f"{self.event_id}: unsupported event type {self.event_type}")
            return issues
        spec = event_spec(self.event_type)
        if not self.subject_id.strip():
            issues.append(f"{self.event_id}: subject_id is required")
        try:
            parse_timestamp(self.timestamp)
        except ValueError:
            issues.append(f"{self.event_id}: invalid timestamp {self.timestamp}")
        if any(value < 0 for value in self.uncertainty.values()):
            issues.append(f"{self.event_id}: uncertainty values must be non-negative")
        if self.event_hash != self.computed_hash():
            issues.append(f"{self.event_id}: event hash mismatch")

        missing_payload = [key for key in spec.required_payload if key not in self.payload]
        if missing_payload:
            issues.append(
                f"{self.event_id}: {self.event_type} missing payload fields {missing_payload}"
            )
        if spec.requires_human_approval and not self.human_approval:
            issues.append(f"{self.event_id}: {self.event_type} requires explicit human approval")
        if not self.reversible and self.event_type in {
            "ExperimentSpec",
            "ActionProposal",
            "DeploymentEvent",
            "PublicationEvent",
            "RetirementEvent",
        } and not self.human_approval:
            issues.append(f"{self.event_id}: irreversible {self.event_type} requires human approval")

        if self.event_type == "OAKTransition":
            before = str(self.payload.get("from_status", ""))
            after = str(self.payload.get("to_status", ""))
            if before not in OAK_STATUSES or after not in OAK_STATUSES:
                issues.append(f"{self.event_id}: invalid OAK transition {before} -> {after}")
        if self.event_type == "ActionProposal" and self.status == "autonomous_execution" and (
            not self.reversible or not self.human_approval
        ):
            issues.append(f"{self.event_id}: unsafe autonomous action proposal")
        if self.event_type == "ResultPacket":
            if not self.units:
                issues.append(f"{self.event_id}: ResultPacket requires units or explicit dimensionless markers")
            if not self.uncertainty:
                issues.append(f"{self.event_id}: ResultPacket requires uncertainty fields")
        if self.event_type == "MeasurementRun":
            if "calibration_id" not in self.payload:
                issues.append(f"{self.event_id}: MeasurementRun requires calibration_id")
            if not self.units or not self.uncertainty:
                issues.append(f"{self.event_id}: MeasurementRun requires units and uncertainty")
        return issues
