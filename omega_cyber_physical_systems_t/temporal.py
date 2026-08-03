from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .hybrid import HybridSample, HybridSimulationReport, Predicate


PROPERTY_KINDS = ("ALWAYS", "EVENTUALLY", "RESPONSE", "MODE_SEQUENCE")


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class TemporalProperty:
    property_id: str
    kind: str
    description: str
    predicate: Predicate | None = None
    target_mode: str | None = None
    trigger: Predicate | None = None
    trigger_mode: str | None = None
    response: Predicate | None = None
    response_mode: str | None = None
    within_s: float | None = None
    mode_sequence: tuple[str, ...] = ()
    start_s: float = 0.0
    end_s: float | None = None

    def validate(self) -> None:
        if not self.property_id.strip() or not self.description.strip():
            raise ValueError("property_id and description are required")
        if self.kind not in PROPERTY_KINDS:
            raise ValueError(f"unsupported temporal property kind: {self.kind}")
        if self.start_s < 0 or (self.end_s is not None and self.end_s < self.start_s):
            raise ValueError("temporal property interval is invalid")
        if self.within_s is not None and self.within_s < 0:
            raise ValueError("within_s cannot be negative")
        if self.kind == "ALWAYS" and self.predicate is None and self.target_mode is None:
            raise ValueError("ALWAYS requires a predicate or target_mode")
        if self.kind == "EVENTUALLY" and self.predicate is None and self.target_mode is None:
            raise ValueError("EVENTUALLY requires a predicate or target_mode")
        if self.kind == "RESPONSE":
            if self.trigger is None and self.trigger_mode is None:
                raise ValueError("RESPONSE requires a trigger")
            if self.response is None and self.response_mode is None:
                raise ValueError("RESPONSE requires a response")
            if self.within_s is None:
                raise ValueError("RESPONSE requires within_s")
        if self.kind == "MODE_SEQUENCE" and len(self.mode_sequence) < 2:
            raise ValueError("MODE_SEQUENCE requires at least two modes")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "property_id": self.property_id,
            "kind": self.kind,
            "description": self.description,
            "predicate": None if self.predicate is None else self.predicate.to_dict(),
            "target_mode": self.target_mode,
            "trigger": None if self.trigger is None else self.trigger.to_dict(),
            "trigger_mode": self.trigger_mode,
            "response": None if self.response is None else self.response.to_dict(),
            "response_mode": self.response_mode,
            "within_s": self.within_s,
            "mode_sequence": list(self.mode_sequence),
            "start_s": self.start_s,
            "end_s": self.end_s,
        }


@dataclass(frozen=True)
class TemporalWitness:
    time_s: float
    mode_id: str
    state: dict[str, float]
    reason: str

    @classmethod
    def from_sample(cls, sample: HybridSample, reason: str) -> "TemporalWitness":
        return cls(sample.time_s, sample.mode_id, dict(sample.state), reason)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TemporalPropertyResult:
    property: TemporalProperty
    passed: bool
    evaluation_count: int
    trigger_count: int
    satisfaction_count: int
    violation_count: int
    first_satisfaction: TemporalWitness | None
    first_violation: TemporalWitness | None
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "property": self.property.to_dict(),
            "passed": self.passed,
            "evaluation_count": self.evaluation_count,
            "trigger_count": self.trigger_count,
            "satisfaction_count": self.satisfaction_count,
            "violation_count": self.violation_count,
            "first_satisfaction": None if self.first_satisfaction is None else self.first_satisfaction.to_dict(),
            "first_violation": None if self.first_violation is None else self.first_violation.to_dict(),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class TemporalVerificationReport:
    trace_hash: str
    results: tuple[TemporalPropertyResult, ...]
    passed: bool
    property_count: int
    passed_count: int
    violation_count: int
    evidence_hash: str
    formal_proof: bool = False
    safety_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_hash": self.trace_hash,
            "results": [item.to_dict() for item in self.results],
            "passed": self.passed,
            "property_count": self.property_count,
            "passed_count": self.passed_count,
            "violation_count": self.violation_count,
            "evidence_hash": self.evidence_hash,
            "formal_proof": self.formal_proof,
            "safety_certified": self.safety_certified,
            "limitations": [
                "properties are checked on a finite sampled trace",
                "absence of a sampled violation is not a proof over continuous time",
                "response deadlines inherit integration-step resolution",
                "no temporal-logic theorem prover or safety certification",
            ],
        }


def _window(samples: Sequence[HybridSample], property: TemporalProperty) -> list[HybridSample]:
    end = float("inf") if property.end_s is None else property.end_s
    return [item for item in samples if property.start_s - 1e-15 <= item.time_s <= end + 1e-15]


def _matches(sample: HybridSample, predicate: Predicate | None, mode_id: str | None) -> bool:
    predicate_match = True if predicate is None else predicate.evaluate(sample.state)
    mode_match = True if mode_id is None else sample.mode_id == mode_id
    return predicate_match and mode_match


def evaluate_temporal_property(
    trace: HybridSimulationReport,
    property: TemporalProperty,
) -> TemporalPropertyResult:
    property.validate()
    samples = _window(trace.samples, property)
    if not samples:
        return TemporalPropertyResult(
            property,
            False,
            0,
            0,
            0,
            1,
            None,
            None,
            "no samples lie inside the declared evaluation interval",
        )

    if property.kind == "ALWAYS":
        violations = [item for item in samples if not _matches(item, property.predicate, property.target_mode)]
        first_ok = next((item for item in samples if _matches(item, property.predicate, property.target_mode)), None)
        return TemporalPropertyResult(
            property=property,
            passed=not violations,
            evaluation_count=len(samples),
            trigger_count=len(samples),
            satisfaction_count=len(samples) - len(violations),
            violation_count=len(violations),
            first_satisfaction=None if first_ok is None else TemporalWitness.from_sample(first_ok, "ALWAYS predicate satisfied"),
            first_violation=None if not violations else TemporalWitness.from_sample(violations[0], "ALWAYS predicate violated"),
            detail="all sampled states satisfy the property" if not violations else "at least one sampled state violates the property",
        )

    if property.kind == "EVENTUALLY":
        matches = [item for item in samples if _matches(item, property.predicate, property.target_mode)]
        deadline = property.within_s
        if deadline is not None:
            matches = [item for item in matches if item.time_s <= property.start_s + deadline + 1e-15]
        passed = bool(matches)
        violation_sample = samples[-1] if not passed else None
        return TemporalPropertyResult(
            property=property,
            passed=passed,
            evaluation_count=len(samples),
            trigger_count=1,
            satisfaction_count=int(passed),
            violation_count=int(not passed),
            first_satisfaction=None if not matches else TemporalWitness.from_sample(matches[0], "EVENTUALLY target reached"),
            first_violation=None if violation_sample is None else TemporalWitness.from_sample(violation_sample, "EVENTUALLY target not reached"),
            detail="target reached on the sampled trace" if passed else "target absent from the sampled trace",
        )

    if property.kind == "MODE_SEQUENCE":
        cursor = 0
        first_satisfaction: TemporalWitness | None = None
        for sample in samples:
            if sample.mode_id == property.mode_sequence[cursor]:
                if cursor == 0:
                    first_satisfaction = TemporalWitness.from_sample(sample, "MODE_SEQUENCE started")
                cursor += 1
                if cursor == len(property.mode_sequence):
                    break
        passed = cursor == len(property.mode_sequence)
        return TemporalPropertyResult(
            property=property,
            passed=passed,
            evaluation_count=len(samples),
            trigger_count=1,
            satisfaction_count=cursor,
            violation_count=int(not passed),
            first_satisfaction=first_satisfaction,
            first_violation=None if passed else TemporalWitness.from_sample(samples[-1], f"sequence stopped at index {cursor}"),
            detail="declared mode sequence observed in order" if passed else f"observed {cursor}/{len(property.mode_sequence)} sequence elements",
        )

    trigger_samples = [item for item in samples if _matches(item, property.trigger, property.trigger_mode)]
    satisfied = 0
    violations: list[HybridSample] = []
    first_response: HybridSample | None = None
    assert property.within_s is not None
    for trigger_sample in trigger_samples:
        deadline = trigger_sample.time_s + property.within_s
        candidates = [
            item
            for item in samples
            if trigger_sample.time_s - 1e-15 <= item.time_s <= deadline + 1e-15
        ]
        response_sample = next(
            (item for item in candidates if _matches(item, property.response, property.response_mode)),
            None,
        )
        if response_sample is None:
            violations.append(trigger_sample)
        else:
            satisfied += 1
            if first_response is None:
                first_response = response_sample
    passed = bool(trigger_samples) and not violations
    detail = (
        "every sampled trigger has a response within the deadline"
        if passed
        else "one or more triggers lack a sampled response" if trigger_samples else "no trigger was observed"
    )
    return TemporalPropertyResult(
        property=property,
        passed=passed,
        evaluation_count=len(samples),
        trigger_count=len(trigger_samples),
        satisfaction_count=satisfied,
        violation_count=len(violations) if trigger_samples else 1,
        first_satisfaction=None if first_response is None else TemporalWitness.from_sample(first_response, "RESPONSE observed"),
        first_violation=None if not violations else TemporalWitness.from_sample(violations[0], "RESPONSE deadline missed"),
        detail=detail,
    )


def verify_temporal_properties(
    trace: HybridSimulationReport,
    properties: Sequence[TemporalProperty],
) -> TemporalVerificationReport:
    if not properties:
        raise ValueError("at least one temporal property is required")
    property_ids: set[str] = set()
    results: list[TemporalPropertyResult] = []
    for property in properties:
        property.validate()
        if property.property_id in property_ids:
            raise ValueError("temporal property IDs must be unique")
        property_ids.add(property.property_id)
        results.append(evaluate_temporal_property(trace, property))
    passed_count = sum(item.passed for item in results)
    violation_count = sum(item.violation_count for item in results)
    payload = {
        "trace_hash": trace.evidence_hash,
        "results": [item.to_dict() for item in results],
        "formal_proof": False,
        "safety_certified": False,
    }
    return TemporalVerificationReport(
        trace_hash=trace.evidence_hash,
        results=tuple(results),
        passed=passed_count == len(results),
        property_count=len(results),
        passed_count=passed_count,
        violation_count=violation_count,
        evidence_hash=_stable_hash(payload),
    )


def demo_temporal_properties() -> tuple[TemporalProperty, ...]:
    return (
        TemporalProperty(
            "TEMP-SAFE-POSITION",
            "ALWAYS",
            "sampled position remains below the declared emergency envelope",
            predicate=Predicate("position_m", "<=", 0.26),
        ),
        TemporalProperty(
            "TEMP-THERMAL-DERATE",
            "RESPONSE",
            "crossing the thermal threshold is followed by derated mode",
            trigger=Predicate("temperature_k", ">=", 303.15),
            response_mode="derated",
            within_s=0.02,
        ),
        TemporalProperty(
            "TEMP-MODE-ORDER",
            "MODE_SEQUENCE",
            "startup, tracking and derated occur in order",
            mode_sequence=("startup", "tracking", "derated"),
        ),
        TemporalProperty(
            "TEMP-EVENTUAL-DERATE",
            "EVENTUALLY",
            "the deterministic fixture eventually enters derated mode",
            target_mode="derated",
            within_s=0.8,
        ),
    )


def demo_failing_temporal_property() -> TemporalProperty:
    return TemporalProperty(
        "TEMP-IMPOSSIBLE-COOLING",
        "EVENTUALLY",
        "adversarial property requiring an unreachable cryogenic temperature",
        predicate=Predicate("temperature_k", "<=", 100.0),
        within_s=0.2,
    )
