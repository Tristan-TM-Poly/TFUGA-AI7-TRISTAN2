"""Ω-DISCOVERY-KERNEL-T∞ R0.4 adaptive frontier conductor.

The conductor does not define a permanent maximum event count. It turns a
finite resource envelope into a deterministic sequence of OAK-safe frontier
stages, observes the actual cost of each stage, and records every saturation as
negative memory before proposing the next action.

Counts produced here are workflow-event budgets and plans. They are not
scientific observations, discoveries, proofs, safety certifications, patents,
or market evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

CORE_LOOP_WIDTH = 8
SCHEMA_VERSION = "omega_discovery_kernel.frontier_conductor.v0.4"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _positive(name: str, value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def _non_negative(name: str, value: float) -> float:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def _align_loop(value: int) -> int:
    if value <= 0:
        raise ValueError("event target must be positive")
    return max(CORE_LOOP_WIDTH, math.ceil(value / CORE_LOOP_WIDTH) * CORE_LOOP_WIDTH)


class Decision(str, Enum):
    EXPAND = "EXPAND"
    RESHARD = "RESHARD"
    HOLD = "HOLD"
    REDESIGN = "REDESIGN"
    STOP = "STOP"


@dataclass(frozen=True, slots=True)
class ResourceEnvelope:
    """Finite execution resources, never a permanent total-event ceiling."""

    wall_time_seconds: float
    writable_bytes: int
    rss_soft_bytes: int
    rollback_reserve_bytes: int = 512 * 1024 * 1024
    minimum_throughput_events_per_second: float = 1_000.0
    maximum_error_rate: float = 0.0
    maximum_batch_latency_seconds: float = 2.0

    def __post_init__(self) -> None:
        _positive("wall_time_seconds", float(self.wall_time_seconds))
        _positive("writable_bytes", float(self.writable_bytes))
        _positive("rss_soft_bytes", float(self.rss_soft_bytes))
        _non_negative("rollback_reserve_bytes", float(self.rollback_reserve_bytes))
        _positive(
            "minimum_throughput_events_per_second",
            float(self.minimum_throughput_events_per_second),
        )
        if not 0.0 <= self.maximum_error_rate <= 1.0:
            raise ValueError("maximum_error_rate must be in [0, 1]")
        _positive(
            "maximum_batch_latency_seconds",
            float(self.maximum_batch_latency_seconds),
        )
        if self.rollback_reserve_bytes >= self.writable_bytes:
            raise ValueError("rollback reserve must be smaller than writable bytes")

    @property
    def payload_budget_bytes(self) -> int:
        return self.writable_bytes - self.rollback_reserve_bytes


@dataclass(frozen=True, slots=True)
class ConductorPolicy:
    initial_events: int = 1_000_000
    growth_factor: float = 2.0
    target_events_per_partition: int = 250_000
    minimum_partitions: int = 1
    maximum_parallelism_hint: int = 64
    validation_sample_ppm: int = 10_000
    bytes_per_event_estimate: float = 180.0
    throughput_estimate_events_per_second: float = 12_000.0
    stage_time_overhead_seconds: float = 3.0
    interruption_fraction: float = 0.524288
    deep_validation_subjects: int = 4_096

    def __post_init__(self) -> None:
        if self.initial_events < CORE_LOOP_WIDTH:
            raise ValueError("initial_events must cover at least one closed loop")
        _positive("growth_factor", float(self.growth_factor))
        if self.growth_factor <= 1.0:
            raise ValueError("growth_factor must be greater than one")
        if self.target_events_per_partition < CORE_LOOP_WIDTH:
            raise ValueError("target_events_per_partition is too small")
        if self.minimum_partitions < 1:
            raise ValueError("minimum_partitions must be positive")
        if self.maximum_parallelism_hint < 1:
            raise ValueError("maximum_parallelism_hint must be positive")
        if not 0 <= self.validation_sample_ppm <= 1_000_000:
            raise ValueError("validation_sample_ppm must be in [0, 1_000_000]")
        _positive("bytes_per_event_estimate", float(self.bytes_per_event_estimate))
        _positive(
            "throughput_estimate_events_per_second",
            float(self.throughput_estimate_events_per_second),
        )
        _non_negative(
            "stage_time_overhead_seconds",
            float(self.stage_time_overhead_seconds),
        )
        if not 0.0 < self.interruption_fraction < 1.0:
            raise ValueError("interruption_fraction must be in (0, 1)")
        if self.deep_validation_subjects < 1:
            raise ValueError("deep_validation_subjects must be positive")


@dataclass(frozen=True, slots=True)
class FrontierPartition:
    partition_index: int
    event_start: int
    event_stop: int
    event_count: int
    subject_start: int
    subject_stop: int
    subject_count: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FrontierStage:
    stage_index: int
    target_events: int
    target_subjects: int
    projected_bytes: int
    projected_seconds: float
    cumulative_events: int
    cumulative_bytes: int
    cumulative_seconds: float
    forced_interrupt_after: int
    partition_count: int
    parallelism_hint: int
    validation_sample_ppm: int
    deep_validation_subjects: int
    partitions: tuple[FrontierPartition, ...]
    stage_fingerprint: str

    def to_dict(self, *, include_partitions: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            key: value
            for key, value in asdict(self).items()
            if key not in {"partitions"}
        }
        if include_partitions:
            payload["partitions"] = [part.to_dict() for part in self.partitions]
        return payload


@dataclass(frozen=True, slots=True)
class FrontierPlan:
    plan_id: str
    created_at: str
    envelope: ResourceEnvelope
    policy: ConductorPolicy
    stages: tuple[FrontierStage, ...]
    exhausted_resource: str
    no_permanent_total_event_cap: bool = True
    oak_boundary: str = (
        "Planned workflow-event volume measures execution capacity, not truth, "
        "evidence quality, safety, patentability, or product value."
    )

    @property
    def planned_events(self) -> int:
        return sum(stage.target_events for stage in self.stages)

    @property
    def planned_subjects(self) -> int:
        return self.planned_events // CORE_LOOP_WIDTH

    @property
    def stage_count(self) -> int:
        return len(self.stages)

    def to_dict(self, *, include_partitions: bool = True) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "resource_envelope": asdict(self.envelope),
            "policy": asdict(self.policy),
            "stage_count": self.stage_count,
            "planned_events": self.planned_events,
            "planned_subjects": self.planned_subjects,
            "exhausted_resource": self.exhausted_resource,
            "no_permanent_total_event_cap": True,
            "stages": [
                stage.to_dict(include_partitions=include_partitions)
                for stage in self.stages
            ],
            "oak_boundary": self.oak_boundary,
        }

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.stages:
            issues.append("plan has no executable stages")
            return issues
        expected_cumulative_events = 0
        expected_cumulative_bytes = 0
        expected_cumulative_seconds = 0.0
        prior_target = 0
        for stage in self.stages:
            if stage.target_events % CORE_LOOP_WIDTH:
                issues.append(f"stage {stage.stage_index}: target is not loop aligned")
            if stage.target_subjects * CORE_LOOP_WIDTH != stage.target_events:
                issues.append(f"stage {stage.stage_index}: subject/event mismatch")
            if stage.stage_index and stage.target_events <= prior_target:
                issues.append(f"stage {stage.stage_index}: target did not grow")
            expected_cumulative_events += stage.target_events
            expected_cumulative_bytes += stage.projected_bytes
            expected_cumulative_seconds += stage.projected_seconds
            if stage.cumulative_events != expected_cumulative_events:
                issues.append(f"stage {stage.stage_index}: cumulative event mismatch")
            if stage.cumulative_bytes != expected_cumulative_bytes:
                issues.append(f"stage {stage.stage_index}: cumulative byte mismatch")
            if abs(stage.cumulative_seconds - expected_cumulative_seconds) > 1e-6:
                issues.append(f"stage {stage.stage_index}: cumulative time mismatch")
            if not 0 < stage.forced_interrupt_after < stage.target_events:
                issues.append(f"stage {stage.stage_index}: invalid interruption cursor")
            if sum(part.event_count for part in stage.partitions) != stage.target_events:
                issues.append(f"stage {stage.stage_index}: partition event mismatch")
            if stage.partition_count != len(stage.partitions):
                issues.append(f"stage {stage.stage_index}: partition count mismatch")
            expected_start = 0
            for partition in stage.partitions:
                if partition.event_start != expected_start:
                    issues.append(
                        f"stage {stage.stage_index}: non-contiguous partition range"
                    )
                    break
                if partition.event_count % CORE_LOOP_WIDTH:
                    issues.append(
                        f"stage {stage.stage_index}: partition is not loop aligned"
                    )
                expected_start = partition.event_stop
            expected_fingerprint = _stage_fingerprint(
                stage,
                include_fingerprint=False,
            )
            if stage.stage_fingerprint != expected_fingerprint:
                issues.append(f"stage {stage.stage_index}: fingerprint mismatch")
            prior_target = stage.target_events
        if self.stages[-1].cumulative_bytes > self.envelope.payload_budget_bytes:
            issues.append("plan exceeds writable payload budget")
        if self.stages[-1].cumulative_seconds > self.envelope.wall_time_seconds:
            issues.append("plan exceeds wall-time budget")
        expected_plan_id = _digest(
            {
                "envelope": asdict(self.envelope),
                "policy": asdict(self.policy),
                "stages": [stage.stage_fingerprint for stage in self.stages],
            }
        )[:32]
        if self.plan_id != expected_plan_id:
            issues.append("plan_id mismatch")
        if hasattr(self.policy, "max_total_events") or hasattr(
            self.envelope,
            "max_total_events",
        ):
            issues.append("permanent total event cap is forbidden")
        return issues


def _stage_fingerprint(
    stage: FrontierStage,
    *,
    include_fingerprint: bool = True,
) -> str:
    payload = stage.to_dict(include_partitions=True)
    if not include_fingerprint:
        payload.pop("stage_fingerprint", None)
    return _digest(payload)


def _make_partitions(
    target_events: int,
    target_per_partition: int,
) -> tuple[FrontierPartition, ...]:
    target_events = _align_loop(target_events)
    target_per_partition = _align_loop(target_per_partition)
    partition_count = max(1, math.ceil(target_events / target_per_partition))
    subjects = target_events // CORE_LOOP_WIDTH
    base_subjects, remainder = divmod(subjects, partition_count)
    partitions: list[FrontierPartition] = []
    subject_cursor = 0
    event_cursor = 0
    for index in range(partition_count):
        subject_count = base_subjects + int(index < remainder)
        event_count = subject_count * CORE_LOOP_WIDTH
        partitions.append(
            FrontierPartition(
                partition_index=index,
                event_start=event_cursor,
                event_stop=event_cursor + event_count,
                event_count=event_count,
                subject_start=subject_cursor,
                subject_stop=subject_cursor + subject_count,
                subject_count=subject_count,
            )
        )
        subject_cursor += subject_count
        event_cursor += event_count
    return tuple(partitions)


def build_plan(
    envelope: ResourceEnvelope,
    policy: ConductorPolicy | None = None,
) -> FrontierPlan:
    policy = policy or ConductorPolicy()
    stages: list[FrontierStage] = []
    cumulative_events = 0
    cumulative_bytes = 0
    cumulative_seconds = 0.0
    target = _align_loop(policy.initial_events)
    exhausted = "none"

    while True:
        projected_bytes = math.ceil(target * policy.bytes_per_event_estimate)
        projected_seconds = (
            target / policy.throughput_estimate_events_per_second
            + policy.stage_time_overhead_seconds
        )
        next_bytes = cumulative_bytes + projected_bytes
        next_seconds = cumulative_seconds + projected_seconds
        if next_bytes > envelope.payload_budget_bytes:
            exhausted = "writable_bytes"
            break
        if next_seconds > envelope.wall_time_seconds:
            exhausted = "wall_time_seconds"
            break

        partitions = _make_partitions(
            target,
            policy.target_events_per_partition,
        )
        forced_interrupt = _align_loop(
            max(CORE_LOOP_WIDTH, int(target * policy.interruption_fraction))
        )
        if forced_interrupt >= target:
            forced_interrupt = target - CORE_LOOP_WIDTH
        parallelism = min(
            policy.maximum_parallelism_hint,
            max(policy.minimum_partitions, len(partitions)),
        )
        cumulative_events += target
        cumulative_bytes = next_bytes
        cumulative_seconds = next_seconds
        provisional = FrontierStage(
            stage_index=len(stages),
            target_events=target,
            target_subjects=target // CORE_LOOP_WIDTH,
            projected_bytes=projected_bytes,
            projected_seconds=projected_seconds,
            cumulative_events=cumulative_events,
            cumulative_bytes=cumulative_bytes,
            cumulative_seconds=cumulative_seconds,
            forced_interrupt_after=forced_interrupt,
            partition_count=len(partitions),
            parallelism_hint=parallelism,
            validation_sample_ppm=policy.validation_sample_ppm,
            deep_validation_subjects=min(
                target // CORE_LOOP_WIDTH,
                policy.deep_validation_subjects,
            ),
            partitions=partitions,
            stage_fingerprint="",
        )
        stage = FrontierStage(
            **{
                **asdict(provisional),
                "partitions": partitions,
                "stage_fingerprint": _stage_fingerprint(
                    provisional,
                    include_fingerprint=False,
                ),
            }
        )
        stages.append(stage)
        target = _align_loop(math.ceil(target * policy.growth_factor))

    if not stages:
        raise ValueError(
            "resource envelope cannot execute the initial stage; reduce "
            "initial_events or increase the finite execution resources"
        )
    plan_id = _digest(
        {
            "envelope": asdict(envelope),
            "policy": asdict(policy),
            "stages": [stage.stage_fingerprint for stage in stages],
        }
    )[:32]
    plan = FrontierPlan(
        plan_id=plan_id,
        created_at=_utc_now(),
        envelope=envelope,
        policy=policy,
        stages=tuple(stages),
        exhausted_resource=exhausted,
    )
    issues = plan.validate()
    if issues:
        raise AssertionError("invalid generated plan: " + "; ".join(issues))
    return plan


@dataclass(frozen=True, slots=True)
class FrontierObservation:
    plan_id: str
    stage_index: int
    attempted_events: int
    accepted_events: int
    elapsed_seconds: float
    bytes_written: int
    peak_rss_bytes: int
    maximum_batch_latency_seconds: float
    error_count: int
    duplicate_count: int
    orphan_parent_count: int
    complete_subjects: int
    interrupted_and_resumed: bool
    ledger_digest: str
    observed_at: str = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if self.stage_index < 0:
            raise ValueError("stage_index cannot be negative")
        for name in (
            "attempted_events",
            "accepted_events",
            "bytes_written",
            "peak_rss_bytes",
            "error_count",
            "duplicate_count",
            "orphan_parent_count",
            "complete_subjects",
        ):
            if int(getattr(self, name)) < 0:
                raise ValueError(f"{name} cannot be negative")
        _positive("elapsed_seconds", float(self.elapsed_seconds))
        _non_negative(
            "maximum_batch_latency_seconds",
            float(self.maximum_batch_latency_seconds),
        )
        if self.accepted_events > self.attempted_events:
            raise ValueError("accepted_events cannot exceed attempted_events")
        if self.accepted_events % CORE_LOOP_WIDTH:
            raise ValueError("accepted_events must be closed-loop aligned")
        if self.complete_subjects * CORE_LOOP_WIDTH > self.accepted_events:
            raise ValueError("complete_subjects exceed accepted event capacity")
        if len(self.ledger_digest) != 64 or any(
            ch not in "0123456789abcdef"
            for ch in self.ledger_digest.lower()
        ):
            raise ValueError(
                "ledger_digest must be a 64-character hexadecimal digest"
            )

    @property
    def throughput(self) -> float:
        return self.accepted_events / self.elapsed_seconds

    @property
    def bytes_per_event(self) -> float:
        return self.bytes_written / max(1, self.accepted_events)

    @property
    def error_rate(self) -> float:
        return self.error_count / max(1, self.attempted_events)

    @property
    def completeness(self) -> float:
        expected = self.accepted_events // CORE_LOOP_WIDTH
        return self.complete_subjects / max(1, expected)

    def payload(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "throughput_events_per_second": self.throughput,
            "bytes_per_event": self.bytes_per_event,
            "error_rate": self.error_rate,
            "subject_completeness": self.completeness,
        }

    @property
    def observation_id(self) -> str:
        return _digest(self.payload())[:32]


@dataclass(frozen=True, slots=True)
class MMinusRecord:
    memory_id: str
    plan_id: str
    stage_index: int
    saturation_kind: str
    observed_value: float | int | bool
    threshold: float | int | bool
    context: str
    prohibited_inference: str
    reusable_rule: str
    redesign_action: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConductorDecision:
    decision: Decision
    reasons: tuple[str, ...]
    next_target_events: int | None
    recommended_partition_events: int | None
    m_minus: tuple[MMinusRecord, ...]
    calibrated_policy: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reasons": list(self.reasons),
            "next_target_events": self.next_target_events,
            "recommended_partition_events": self.recommended_partition_events,
            "m_minus": [record.to_dict() for record in self.m_minus],
            "calibrated_policy": dict(self.calibrated_policy),
        }


def _mminus(
    observation: FrontierObservation,
    kind: str,
    observed: float | int | bool,
    threshold: float | int | bool,
    prohibited: str,
    rule: str,
    redesign: str,
) -> MMinusRecord:
    payload = {
        "plan_id": observation.plan_id,
        "stage_index": observation.stage_index,
        "kind": kind,
        "observed": observed,
        "threshold": threshold,
        "ledger_digest": observation.ledger_digest,
    }
    return MMinusRecord(
        memory_id=f"mminus-{_digest(payload)[:24]}",
        plan_id=observation.plan_id,
        stage_index=observation.stage_index,
        saturation_kind=kind,
        observed_value=observed,
        threshold=threshold,
        context=(
            f"frontier stage {observation.stage_index} "
            f"under plan {observation.plan_id}"
        ),
        prohibited_inference=prohibited,
        reusable_rule=rule,
        redesign_action=redesign,
        created_at=_utc_now(),
    )


def decide_next(
    plan: FrontierPlan,
    observation: FrontierObservation,
) -> ConductorDecision:
    if observation.plan_id != plan.plan_id:
        raise ValueError("observation belongs to a different plan")
    if observation.stage_index >= len(plan.stages):
        raise ValueError("observation stage is outside the plan")
    stage = plan.stages[observation.stage_index]
    reasons: list[str] = []
    memories: list[MMinusRecord] = []

    integrity_failure = False
    if observation.duplicate_count:
        integrity_failure = True
        reasons.append("duplicate event IDs observed")
        memories.append(
            _mminus(
                observation,
                "duplicate_ids",
                observation.duplicate_count,
                0,
                (
                    "A resumed or parallel frontier is exactly-once merely "
                    "because it completed."
                ),
                (
                    "Reject promotion whenever duplicate IDs are non-zero; "
                    "preserve the conflicting shards and cursors."
                ),
                (
                    "quarantine overlapping ranges, rebuild partition leases, "
                    "and replay from the last verified checkpoint"
                ),
            )
        )
    if observation.orphan_parent_count:
        integrity_failure = True
        reasons.append("orphan parents observed")
        memories.append(
            _mminus(
                observation,
                "orphan_parents",
                observation.orphan_parent_count,
                0,
                "Partition completion implies lineage completeness.",
                "Require zero orphan parents before stage promotion or aggregation.",
                "reconstruct parent ranges and add cross-partition lineage proofs",
            )
        )
    if observation.completeness < 1.0:
        integrity_failure = True
        reasons.append("incomplete closed-loop subjects")
        memories.append(
            _mminus(
                observation,
                "subject_completeness",
                observation.completeness,
                1.0,
                "Raw accepted event count implies complete discovery loops.",
                (
                    "Count only fully closed eight-event subjects as completed "
                    "workflow units."
                ),
                "resume incomplete subjects before opening new ranges",
            )
        )
    if observation.accepted_events != stage.target_events:
        integrity_failure = True
        reasons.append("accepted event count differs from stage target")
    if not observation.interrupted_and_resumed:
        reasons.append("forced-resume proof missing")
        memories.append(
            _mminus(
                observation,
                "resume_proof",
                False,
                True,
                "A clean uninterrupted run demonstrates recoverability.",
                (
                    "Every promoted frontier scale must include at least one "
                    "forced interruption and exact resume."
                ),
                "rerun the stage with a deterministic forced interruption cursor",
            )
        )

    error_saturation = (
        observation.error_rate > plan.envelope.maximum_error_rate
    )
    if error_saturation:
        reasons.append("error rate exceeds envelope")
        memories.append(
            _mminus(
                observation,
                "error_rate",
                observation.error_rate,
                plan.envelope.maximum_error_rate,
                "Higher scale can compensate for a degraded error rate.",
                (
                    "Do not expand while the observed error rate exceeds the "
                    "declared envelope."
                ),
                "classify errors, create minimal reproductions, and repair before replay",
            )
        )

    throughput_saturation = (
        observation.throughput
        < plan.envelope.minimum_throughput_events_per_second
    )
    if throughput_saturation:
        reasons.append("throughput below envelope")
        memories.append(
            _mminus(
                observation,
                "throughput",
                observation.throughput,
                plan.envelope.minimum_throughput_events_per_second,
                "A completed stage is fast enough for geometric expansion.",
                (
                    "Calibrate growth from measured throughput rather than "
                    "target cardinality."
                ),
                (
                    "profile serialization, SQLite batches, shard rotation, "
                    "and validation sampling"
                ),
            )
        )

    latency_saturation = (
        observation.maximum_batch_latency_seconds
        > plan.envelope.maximum_batch_latency_seconds
    )
    if latency_saturation:
        reasons.append("batch latency above envelope")
        memories.append(
            _mminus(
                observation,
                "batch_latency",
                observation.maximum_batch_latency_seconds,
                plan.envelope.maximum_batch_latency_seconds,
                "Average throughput hides tail-latency saturation.",
                "Treat maximum batch latency as a separate expansion gate.",
                "reduce partition/shard size or increase independent writers",
            )
        )

    rss_saturation = observation.peak_rss_bytes > plan.envelope.rss_soft_bytes
    if rss_saturation:
        reasons.append("resident memory above soft envelope")
        memories.append(
            _mminus(
                observation,
                "rss",
                observation.peak_rss_bytes,
                plan.envelope.rss_soft_bytes,
                "Disk-backed execution cannot saturate memory.",
                (
                    "Keep memory as an independent measured budget even for "
                    "streamed workloads."
                ),
                (
                    "reduce in-process batches, validation windows, and "
                    "concurrent partitions"
                ),
            )
        )

    calibrated_bytes = max(1.0, observation.bytes_per_event)
    calibrated_throughput = max(1.0, observation.throughput)
    next_target = _align_loop(
        math.ceil(stage.target_events * plan.policy.growth_factor)
    )
    next_bytes = math.ceil(next_target * calibrated_bytes)
    next_seconds = (
        next_target / calibrated_throughput
        + plan.policy.stage_time_overhead_seconds
    )
    remaining_bytes = (
        plan.envelope.payload_budget_bytes - stage.cumulative_bytes
    )
    remaining_seconds = (
        plan.envelope.wall_time_seconds - stage.cumulative_seconds
    )
    resource_stop = (
        next_bytes > remaining_bytes or next_seconds > remaining_seconds
    )

    recommended_partition_events = _align_loop(
        plan.policy.target_events_per_partition
    )
    if latency_saturation or rss_saturation:
        recommended_partition_events = _align_loop(
            max(CORE_LOOP_WIDTH, recommended_partition_events // 2)
        )

    if integrity_failure or error_saturation:
        decision = Decision.REDESIGN
        next_value: int | None = stage.target_events
    elif resource_stop:
        decision = Decision.STOP
        next_value = None
        reasons.append(
            "remaining finite resource envelope cannot contain the next "
            "geometric stage"
        )
    elif latency_saturation or rss_saturation:
        decision = Decision.RESHARD
        next_value = next_target
    elif throughput_saturation or not observation.interrupted_and_resumed:
        decision = Decision.HOLD
        next_value = stage.target_events
    else:
        decision = Decision.EXPAND
        next_value = next_target
        reasons.append(
            "integrity, quality, throughput, latency, memory, and resume "
            "gates passed"
        )

    return ConductorDecision(
        decision=decision,
        reasons=tuple(reasons),
        next_target_events=next_value,
        recommended_partition_events=(
            recommended_partition_events if next_value is not None else None
        ),
        m_minus=tuple(memories),
        calibrated_policy={
            "bytes_per_event_estimate": calibrated_bytes,
            "throughput_estimate_events_per_second": calibrated_throughput,
            "target_events_per_partition": recommended_partition_events,
            "growth_factor": plan.policy.growth_factor,
            "no_permanent_total_event_cap": True,
        },
    )


@dataclass(frozen=True, slots=True)
class GeneratorCampaignProjection:
    campaign_records: int
    campaign_epochs: int
    campaign_partitions: int
    projected_discovery_events: int
    projected_discovery_subjects: int
    projection_digest: str
    no_permanent_total_addition_cap: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_generator_campaign(
    summary: Mapping[str, Any],
) -> GeneratorCampaignProjection:
    records = int(summary.get("planned_logical_records", 0))
    epochs = int(summary.get("epoch_count", 0))
    partitions = int(summary.get("partition_count", 0))
    no_cap = bool(summary.get("no_permanent_total_addition_cap", False))
    if records < 1 or epochs < 1 or partitions < 1:
        raise ValueError(
            "generator campaign summary must contain positive records, "
            "epochs, and partitions"
        )
    if not no_cap:
        raise ValueError(
            "generator campaign must declare that its finite plan is not a "
            "permanent cap"
        )
    projected_events = records * CORE_LOOP_WIDTH
    payload = {
        "campaign_records": records,
        "campaign_epochs": epochs,
        "campaign_partitions": partitions,
        "projected_discovery_events": projected_events,
    }
    return GeneratorCampaignProjection(
        campaign_records=records,
        campaign_epochs=epochs,
        campaign_partitions=partitions,
        projected_discovery_events=projected_events,
        projected_discovery_subjects=records,
        projection_digest=_digest(payload),
        no_permanent_total_addition_cap=True,
        boundary=(
            "Projection allocates one eight-event workflow loop per generated "
            "record. It does not materialize those events or upgrade candidates "
            "into evidence."
        ),
    )


class ConductorLedger:
    """Append-only hash-chained observation and decision ledger."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.entries_path = self.root / "conductor-ledger.jsonl"
        self.checkpoint_path = self.root / "conductor-checkpoint.json"
        self.mminus_path = self.root / "conductor-m-minus.jsonl"
        self.next_sequence = 0
        self.chain_digest = "0" * 64
        self.observation_ids: set[str] = set()
        self._restore()

    def _restore(self) -> None:
        if not self.entries_path.exists():
            return
        expected_sequence = 0
        chain = "0" * 64
        ids: set[str] = set()
        with self.entries_path.open(encoding="utf-8") as stream:
            for raw in stream:
                entry = json.loads(raw)
                if int(entry["sequence"]) != expected_sequence:
                    raise ValueError(
                        "non-contiguous conductor ledger sequence"
                    )
                body = dict(entry)
                observed_hash = str(body.pop("entry_hash"))
                observed_chain = str(body.pop("chain_digest"))
                if observed_hash != _digest(body):
                    raise ValueError(
                        "conductor ledger entry hash mismatch"
                    )
                chain = sha256(
                    (chain + observed_hash).encode("utf-8")
                ).hexdigest()
                if observed_chain != chain:
                    raise ValueError("conductor ledger chain mismatch")
                observation_id = str(entry["observation_id"])
                if observation_id in ids:
                    raise ValueError(
                        "duplicate observation in conductor ledger"
                    )
                ids.add(observation_id)
                expected_sequence += 1
        self.next_sequence = expected_sequence
        self.chain_digest = chain
        self.observation_ids = ids

    def append(
        self,
        observation: FrontierObservation,
        decision: ConductorDecision,
    ) -> bool:
        if observation.observation_id in self.observation_ids:
            return False
        body: dict[str, Any] = {
            "sequence": self.next_sequence,
            "observation_id": observation.observation_id,
            "observation": observation.payload(),
            "decision": decision.to_dict(),
            "previous_chain_digest": self.chain_digest,
        }
        entry_hash = _digest(body)
        next_chain = sha256(
            (self.chain_digest + entry_hash).encode("utf-8")
        ).hexdigest()
        entry = {
            **body,
            "entry_hash": entry_hash,
            "chain_digest": next_chain,
        }
        with self.entries_path.open("a", encoding="utf-8") as stream:
            stream.write(_canonical_json(entry) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if decision.m_minus:
            with self.mminus_path.open("a", encoding="utf-8") as stream:
                for record in decision.m_minus:
                    stream.write(
                        _canonical_json(record.to_dict()) + "\n"
                    )
                stream.flush()
                os.fsync(stream.fileno())
        self.next_sequence += 1
        self.chain_digest = next_chain
        self.observation_ids.add(observation.observation_id)
        _atomic_json(
            self.checkpoint_path,
            {
                "schema": SCHEMA_VERSION,
                "next_sequence": self.next_sequence,
                "chain_digest": self.chain_digest,
                "observation_count": len(self.observation_ids),
                "updated_at": _utc_now(),
            },
        )
        return True

    def audit(self) -> dict[str, Any]:
        restored = ConductorLedger(self.root)
        mminus_count = 0
        if restored.mminus_path.exists():
            with restored.mminus_path.open(encoding="utf-8") as stream:
                mminus_count = sum(1 for line in stream if line.strip())
        return {
            "schema": SCHEMA_VERSION,
            "status": "PASS",
            "entries": restored.next_sequence,
            "observations": len(restored.observation_ids),
            "m_minus_records": mminus_count,
            "chain_digest": restored.chain_digest,
            "no_permanent_total_event_cap": True,
        }


def write_plan(plan: FrontierPlan, output: str | Path) -> None:
    _atomic_json(Path(output), plan.to_dict(include_partitions=True))


def read_plan(path: str | Path) -> FrontierPlan:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    envelope = ResourceEnvelope(**raw["resource_envelope"])
    policy = ConductorPolicy(**raw["policy"])
    stages: list[FrontierStage] = []
    for item in raw["stages"]:
        item = dict(item)
        partitions = tuple(
            FrontierPartition(**part)
            for part in item.pop("partitions")
        )
        stages.append(
            FrontierStage(**{**item, "partitions": partitions})
        )
    plan = FrontierPlan(
        plan_id=str(raw["plan_id"]),
        created_at=str(raw["created_at"]),
        envelope=envelope,
        policy=policy,
        stages=tuple(stages),
        exhausted_resource=str(raw["exhausted_resource"]),
        no_permanent_total_event_cap=bool(
            raw.get("no_permanent_total_event_cap", False)
        ),
        oak_boundary=str(raw.get("oak_boundary", "")),
    )
    issues = plan.validate()
    if issues:
        raise ValueError(
            "invalid frontier plan: " + "; ".join(issues)
        )
    return plan


def _load_observation(path: str | Path) -> FrontierObservation:
    return FrontierObservation(
        **json.loads(Path(path).read_text(encoding="utf-8"))
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan and govern adaptive Ω-DISCOVERY frontiers."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser(
        "plan",
        help="Compile a finite resource envelope into geometric stages.",
    )
    plan.add_argument("--wall-time-seconds", type=float, required=True)
    plan.add_argument("--writable-bytes", type=int, required=True)
    plan.add_argument("--rss-soft-bytes", type=int, required=True)
    plan.add_argument("--initial-events", type=int, default=1_000_000)
    plan.add_argument("--growth-factor", type=float, default=2.0)
    plan.add_argument("--bytes-per-event", type=float, default=180.0)
    plan.add_argument("--throughput", type=float, default=12_000.0)
    plan.add_argument("--partition-events", type=int, default=250_000)
    plan.add_argument("--output", required=True)

    observe = sub.add_parser(
        "observe",
        help="Evaluate a measured stage and append its decision.",
    )
    observe.add_argument("--plan", required=True)
    observe.add_argument("--observation", required=True)
    observe.add_argument("--ledger-dir", required=True)
    observe.add_argument("--output")

    audit = sub.add_parser(
        "audit",
        help="Audit an existing conductor ledger.",
    )
    audit.add_argument("--ledger-dir", required=True)

    project = sub.add_parser(
        "project-generator",
        help="Project a generator campaign into discovery loops.",
    )
    project.add_argument("--campaign-summary", required=True)
    project.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "plan":
        envelope = ResourceEnvelope(
            wall_time_seconds=args.wall_time_seconds,
            writable_bytes=args.writable_bytes,
            rss_soft_bytes=args.rss_soft_bytes,
        )
        policy = ConductorPolicy(
            initial_events=args.initial_events,
            growth_factor=args.growth_factor,
            bytes_per_event_estimate=args.bytes_per_event,
            throughput_estimate_events_per_second=args.throughput,
            target_events_per_partition=args.partition_events,
        )
        plan = build_plan(envelope, policy)
        write_plan(plan, args.output)
        print(
            json.dumps(
                plan.to_dict(include_partitions=False),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "observe":
        plan = read_plan(args.plan)
        observation = _load_observation(args.observation)
        decision = decide_next(plan, observation)
        ledger = ConductorLedger(args.ledger_dir)
        appended = ledger.append(observation, decision)
        payload = {
            "appended": appended,
            "decision": decision.to_dict(),
            "audit": ledger.audit(),
        }
        if args.output:
            _atomic_json(Path(args.output), payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.command == "audit":
        print(
            json.dumps(
                ConductorLedger(args.ledger_dir).audit(),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "project-generator":
        summary = json.loads(
            Path(args.campaign_summary).read_text(encoding="utf-8")
        )
        projection = project_generator_campaign(summary).to_dict()
        if args.output:
            _atomic_json(Path(args.output), projection)
        print(json.dumps(projection, ensure_ascii=False, indent=2))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
