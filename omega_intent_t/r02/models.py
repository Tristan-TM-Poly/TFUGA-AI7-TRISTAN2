from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


WORK_STATES = (
    "planned",
    "ready",
    "running",
    "validated",
    "rejected",
    "blocked",
    "cancelled",
)
TERMINAL_STATES = frozenset({"validated", "rejected", "blocked", "cancelled"})
RISK_LEVELS = ("low", "normal", "elevated", "ip_sensitive", "public", "irreversible")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        value = (value,)
    if not isinstance(value, Iterable) or isinstance(value, (bytes, bytearray, Mapping)):
        raise TypeError("expected a string or iterable of strings")
    return tuple(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


@dataclass(frozen=True)
class WorkRecord:
    intent_id: str
    kind: str
    payload: Mapping[str, Any]
    dependency_ids: tuple[str, ...] = ()
    risk: str = "normal"
    state: str = "planned"
    attempts: int = 0
    record_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.intent_id.strip():
            raise ValueError("intent_id cannot be empty")
        if not self.kind.strip():
            raise ValueError("kind cannot be empty")
        if self.risk not in RISK_LEVELS:
            raise ValueError(f"unknown risk level: {self.risk}")
        if self.state not in WORK_STATES:
            raise ValueError(f"unknown work state: {self.state}")
        if self.attempts < 0:
            raise ValueError("attempts cannot be negative")
        object.__setattr__(self, "intent_id", self.intent_id.strip())
        object.__setattr__(self, "kind", self.kind.strip())
        object.__setattr__(self, "dependency_ids", _strings(self.dependency_ids))
        if not self.record_id:
            object.__setattr__(self, "record_id", f"WU2-{stable_digest(self.identity_payload())[:20].upper()}")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, default_intent_id: str = "") -> "WorkRecord":
        payload = raw.get("payload")
        if payload is None:
            payload = {
                key: value
                for key, value in raw.items()
                if key
                not in {
                    "record_id",
                    "id",
                    "intent_id",
                    "kind",
                    "dependency_ids",
                    "dependencies",
                    "risk",
                    "state",
                    "attempts",
                    "metadata",
                }
            }
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be an object")
        metadata = raw.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("metadata must be an object")
        return cls(
            intent_id=str(raw.get("intent_id") or default_intent_id),
            kind=str(raw.get("kind") or "work"),
            payload=dict(payload),
            dependency_ids=_strings(raw.get("dependency_ids") or raw.get("dependencies")),
            risk=str(raw.get("risk") or "normal"),
            state=str(raw.get("state") or "planned"),
            attempts=int(raw.get("attempts") or 0),
            record_id=str(raw.get("record_id") or raw.get("id") or ""),
            metadata=dict(metadata),
        )

    def identity_payload(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "kind": self.kind,
            "payload": dict(self.payload),
            "dependency_ids": list(self.dependency_ids),
            "risk": self.risk,
        }

    @property
    def content_digest(self) -> str:
        return stable_digest(self.identity_payload())

    @property
    def estimated_bytes(self) -> int:
        return len(canonical_json(self.to_dict()).encode("utf-8"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "content_digest": self.content_digest,
            "intent_id": self.intent_id,
            "kind": self.kind,
            "payload": dict(self.payload),
            "dependency_ids": list(self.dependency_ids),
            "risk": self.risk,
            "state": self.state,
            "attempts": self.attempts,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class BudgetPolicy:
    initial_items: int = 256
    initial_bytes: int = 4 * 1024 * 1024
    minimum_items: int = 1
    minimum_bytes: int = 4096
    growth_factor: float = 1.6
    shrink_factor: float = 0.5
    quality_floor: float = 0.95
    failure_ceiling: float = 0.05
    backpressure_seconds: float = 30.0
    memory_pressure_ratio: float = 0.85

    def __post_init__(self) -> None:
        if self.initial_items < 1 or self.minimum_items < 1:
            raise ValueError("item budgets must be positive")
        if self.initial_bytes < 1 or self.minimum_bytes < 1:
            raise ValueError("byte budgets must be positive")
        if self.growth_factor <= 1:
            raise ValueError("growth_factor must be greater than one")
        if not 0 < self.shrink_factor < 1:
            raise ValueError("shrink_factor must be between zero and one")
        if not 0 <= self.quality_floor <= 1:
            raise ValueError("quality_floor must be between zero and one")
        if not 0 <= self.failure_ceiling <= 1:
            raise ValueError("failure_ceiling must be between zero and one")


@dataclass(frozen=True)
class BudgetObservation:
    processed: int
    accepted: int
    rejected: int
    failed: int
    elapsed_seconds: float
    peak_memory_ratio: float = 0.0
    queue_wait_seconds: float = 0.0

    def __post_init__(self) -> None:
        values = (self.processed, self.accepted, self.rejected, self.failed)
        if any(value < 0 for value in values):
            raise ValueError("observation counts cannot be negative")
        if self.accepted + self.rejected + self.failed > self.processed:
            raise ValueError("outcomes cannot exceed processed count")
        if self.elapsed_seconds < 0 or self.queue_wait_seconds < 0:
            raise ValueError("timings cannot be negative")

    @property
    def quality(self) -> float:
        return self.accepted / self.processed if self.processed else 1.0

    @property
    def failure_rate(self) -> float:
        return self.failed / self.processed if self.processed else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "quality": self.quality,
            "failure_rate": self.failure_rate,
        }


@dataclass(frozen=True)
class BudgetState:
    batch_items: int
    batch_bytes: int
    successful_batches: int = 0
    constrained_batches: int = 0
    frontier_events: int = 0
    generation: int = 0
    last_reason: str = "initial"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompletionContract:
    requirements_total: int
    requirements_verified: int
    requirements_blocked: int = 0
    requirements_rejected: int = 0
    claims_total: int = 0
    claims_evidence_backed: int = 0
    unresolved_claims: int = 0
    critical_risks_open: int = 0
    build_passed: bool = False
    tests_passed: bool = False
    documentation_synced: bool = False
    benchmarks_completed: int = 0
    benchmark_regressions: int = 0
    residuals_declared: bool = False

    def __post_init__(self) -> None:
        numeric = (
            self.requirements_total,
            self.requirements_verified,
            self.requirements_blocked,
            self.requirements_rejected,
            self.claims_total,
            self.claims_evidence_backed,
            self.unresolved_claims,
            self.critical_risks_open,
            self.benchmarks_completed,
            self.benchmark_regressions,
        )
        if any(value < 0 for value in numeric):
            raise ValueError("contract counts cannot be negative")
        if self.requirements_verified + self.requirements_blocked + self.requirements_rejected > self.requirements_total:
            raise ValueError("requirement outcomes cannot exceed total")
        if self.claims_evidence_backed > self.claims_total:
            raise ValueError("evidence-backed claims cannot exceed total claims")

    @property
    def requirement_closure_ratio(self) -> float:
        resolved = self.requirements_verified + self.requirements_blocked + self.requirements_rejected
        return resolved / self.requirements_total if self.requirements_total else 1.0

    @property
    def verification_ratio(self) -> float:
        return self.requirements_verified / self.requirements_total if self.requirements_total else 1.0

    @property
    def claim_evidence_ratio(self) -> float:
        return self.claims_evidence_backed / self.claims_total if self.claims_total else 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "requirement_closure_ratio": self.requirement_closure_ratio,
            "verification_ratio": self.verification_ratio,
            "claim_evidence_ratio": self.claim_evidence_ratio,
        }


@dataclass(frozen=True)
class CompletionDecision:
    complete: bool
    status: str
    closure_ratio: float
    verification_ratio: float
    claim_evidence_ratio: float
    blockers: tuple[str, ...]
    next_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["next_actions"] = list(self.next_actions)
        return payload


@dataclass(frozen=True)
class FailureRecord:
    work_unit_id: str
    phase: str
    message: str
    exception_type: str = ""
    evidence: tuple[str, ...] = ()
    attempt: int = 1

    @property
    def failure_id(self) -> str:
        return f"FAIL-{stable_digest(asdict(self))[:20].upper()}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failure_id"] = self.failure_id
        payload["evidence"] = list(self.evidence)
        return payload


@dataclass(frozen=True)
class RepairAction:
    action_id: str
    failure_id: str
    category: str
    objective: str
    validations: tuple[str, ...]
    risk: str
    automatic_candidate: bool
    human_gate: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["validations"] = list(self.validations)
        return payload


@dataclass(frozen=True)
class StackShard:
    shard_id: str
    branch: str
    level: int
    sequence: int
    work_unit_ids: tuple[str, ...]
    estimated_bytes: int
    risks: tuple[str, ...]
    depends_on_shards: tuple[str, ...]
    requires_human_approval: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("work_unit_ids", "risks", "depends_on_shards"):
            payload[key] = list(payload[key])
        return payload
