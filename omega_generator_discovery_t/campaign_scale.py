"""Unbounded multi-epoch scaling for Ω-GENERATOR-DISCOVERY campaigns.

The module plans and validates finite campaign waves without canonizing a
permanent total-addition ceiling. Generated objects remain candidate templates
and synthetic benchmarks, not scientific evidence.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterator, Mapping

from .campaign import CampaignSpec, iter_generator_bundles

PROFILE_MULTIPLIERS: dict[str, int] = {
    "million": 1,
    "ten-million": 10,
    "hundred-million": 100,
    "billion": 1_000,
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _positive(name: str, value: int) -> int:
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def resolve_target_records(
    spec: CampaignSpec,
    *,
    profile: str | None = None,
    target_records: int | None = None,
) -> int:
    """Resolve a finite run target; it is a workload budget, never a global cap."""
    if (profile is None) == (target_records is None):
        raise ValueError("provide exactly one of profile or target_records")
    if target_records is not None:
        return _positive("target_records", int(target_records))
    assert profile is not None
    try:
        multiplier = PROFILE_MULTIPLIERS[profile]
    except KeyError as exc:
        raise ValueError(f"unknown profile: {profile}") from exc
    return spec.logical_record_count * multiplier


def epoch_spec(base: CampaignSpec, epoch_index: int) -> CampaignSpec:
    """Create a deterministic, content-distinct campaign epoch."""
    if epoch_index < 0:
        raise ValueError("epoch_index cannot be negative")
    return CampaignSpec(
        campaign_id=f"{base.campaign_id}/epoch-{epoch_index:08d}",
        axes=base.axes,
        benchmark_variants=base.benchmark_variants,
        schema_version="R0.4",
    )


def _epoch_prefix(epoch_index: int, spec: CampaignSpec) -> str:
    return f"E{epoch_index:08d}-{spec.fingerprint[:12].upper()}"


def _prefixed(prefix: str, identifier: str) -> str:
    return f"{prefix}-{identifier}"


def epochize_record(
    record: Mapping[str, Any],
    *,
    epoch_index: int,
    spec: CampaignSpec,
) -> dict[str, Any]:
    """Namespace IDs and links so epochs can be merged without collisions."""
    prefix = _epoch_prefix(epoch_index, spec)
    payload = dict(record.get("payload", {}))
    kind = str(record.get("kind", ""))
    old_id = str(payload.get("id", record.get("addition_id", "")))
    if not old_id:
        raise ValueError("record has no identifier")
    payload["id"] = _prefixed(prefix, old_id)
    if kind == "generator_candidate":
        benchmark_ids = payload.get("benchmark_ids", ())
        payload["benchmark_ids"] = [_prefixed(prefix, str(value)) for value in benchmark_ids]
    elif kind == "synthetic_benchmark":
        generator_id = str(payload.get("generator_id", ""))
        if not generator_id:
            raise ValueError("benchmark record has no generator_id")
        payload["generator_id"] = _prefixed(prefix, generator_id)

    metadata = dict(record.get("metadata", {}))
    metadata.update(
        {
            "scale_schema_version": "R0.4",
            "epoch_index": epoch_index,
            "epoch_fingerprint": spec.fingerprint,
        }
    )
    provenance = [str(value) for value in record.get("provenance", ())]
    provenance.extend((spec.campaign_id, spec.fingerprint))
    risk = str(payload.get("risk", record.get("risk", "normal")))
    return {
        **dict(record),
        "addition_id": payload["id"],
        "payload": payload,
        "provenance": list(dict.fromkeys(provenance)),
        "risk": risk,
        "metadata": metadata,
    }


def iter_epoch_bundles(
    base: CampaignSpec,
    epoch_index: int,
    *,
    start: int = 0,
    stop: int | None = None,
) -> Iterator[dict[str, Any]]:
    spec = epoch_spec(base, epoch_index)
    for record in iter_generator_bundles(spec, start=start, stop=stop):
        yield epochize_record(record, epoch_index=epoch_index, spec=spec)


@dataclass(frozen=True, slots=True)
class ScalePolicy:
    target_records_per_partition: int = 250_000
    bundles_per_shard: int = 2_048
    parallelism_hint: int = 16
    validation_sample_ppm: int = 10_000
    exhaustive_risks: tuple[str, ...] = (
        "branch_ambiguity",
        "non_identifiability",
        "hidden_state",
        "numerical_instability",
        "unit_mismatch",
        "causal_overclaim",
    )

    def __post_init__(self) -> None:
        _positive("target_records_per_partition", self.target_records_per_partition)
        _positive("bundles_per_shard", self.bundles_per_shard)
        _positive("parallelism_hint", self.parallelism_hint)
        if not 0 <= self.validation_sample_ppm <= 1_000_000:
            raise ValueError("validation_sample_ppm must be between 0 and 1,000,000")
        if len(self.exhaustive_risks) != len(set(self.exhaustive_risks)):
            raise ValueError("exhaustive_risks contains duplicates")


@dataclass(frozen=True, slots=True)
class ScalePartition:
    global_partition_index: int
    epoch_index: int
    epoch_partition_index: int
    epoch_partition_count: int
    generator_start: int
    generator_stop: int
    generator_bundles: int
    logical_records: int
    suggested_shards: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScaleEpoch:
    epoch_index: int
    campaign_id: str
    campaign_fingerprint: str
    generator_bundles: int
    logical_records: int
    partition_count: int
    first_global_partition: int
    last_global_partition: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScalePlan:
    base_campaign_id: str
    base_campaign_fingerprint: str
    requested_logical_records: int
    planned_logical_records: int
    rounding_overage_records: int
    records_per_bundle: int
    epochs: tuple[ScaleEpoch, ...]
    partitions: tuple[ScalePartition, ...]
    policy: ScalePolicy
    generated_at: str
    no_permanent_total_addition_cap: bool = True

    @property
    def epoch_count(self) -> int:
        return len(self.epochs)

    @property
    def partition_count(self) -> int:
        return len(self.partitions)

    def to_dict(self, *, include_partitions: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "base_campaign_id": self.base_campaign_id,
            "base_campaign_fingerprint": self.base_campaign_fingerprint,
            "requested_logical_records": self.requested_logical_records,
            "planned_logical_records": self.planned_logical_records,
            "rounding_overage_records": self.rounding_overage_records,
            "records_per_bundle": self.records_per_bundle,
            "epoch_count": self.epoch_count,
            "partition_count": self.partition_count,
            "epochs": [epoch.to_dict() for epoch in self.epochs],
            "policy": asdict(self.policy),
            "generated_at": self.generated_at,
            "no_permanent_total_addition_cap": True,
            "oak_boundary": "Campaign scale is not scientific evidence density.",
        }
        if include_partitions:
            payload["partitions"] = [partition.to_dict() for partition in self.partitions]
        return payload


class ScalePlanner:
    """Plan arbitrary finite workloads as deterministic epochs and partitions."""

    def __init__(self, base: CampaignSpec, policy: ScalePolicy | None = None):
        self.base = base
        self.policy = policy or ScalePolicy()

    def plan(self, target_logical_records: int) -> ScalePlan:
        target = _positive("target_logical_records", int(target_logical_records))
        records_per_bundle = self.base.records_per_bundle
        target_bundles = math.ceil(target / records_per_bundle)
        planned_records = target_bundles * records_per_bundle
        remaining = target_bundles
        epoch_index = 0
        global_partition = 0
        epochs: list[ScaleEpoch] = []
        partitions: list[ScalePartition] = []

        while remaining:
            bundles = min(self.base.generator_count, remaining)
            epoch_records = bundles * records_per_bundle
            partition_count = max(
                1,
                math.ceil(epoch_records / self.policy.target_records_per_partition),
            )
            base_size, remainder = divmod(bundles, partition_count)
            cursor = 0
            first_partition = global_partition
            epoch = epoch_spec(self.base, epoch_index)
            for local_index in range(partition_count):
                size = base_size + int(local_index < remainder)
                stop = cursor + size
                partitions.append(
                    ScalePartition(
                        global_partition_index=global_partition,
                        epoch_index=epoch_index,
                        epoch_partition_index=local_index,
                        epoch_partition_count=partition_count,
                        generator_start=cursor,
                        generator_stop=stop,
                        generator_bundles=size,
                        logical_records=size * records_per_bundle,
                        suggested_shards=math.ceil(size / self.policy.bundles_per_shard),
                    )
                )
                cursor = stop
                global_partition += 1
            epochs.append(
                ScaleEpoch(
                    epoch_index=epoch_index,
                    campaign_id=epoch.campaign_id,
                    campaign_fingerprint=epoch.fingerprint,
                    generator_bundles=bundles,
                    logical_records=epoch_records,
                    partition_count=partition_count,
                    first_global_partition=first_partition,
                    last_global_partition=global_partition - 1,
                )
            )
            remaining -= bundles
            epoch_index += 1

        return ScalePlan(
            base_campaign_id=self.base.campaign_id,
            base_campaign_fingerprint=self.base.fingerprint,
            requested_logical_records=target,
            planned_logical_records=planned_records,
            rounding_overage_records=planned_records - target,
            records_per_bundle=records_per_bundle,
            epochs=tuple(epochs),
            partitions=tuple(partitions),
            policy=self.policy,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def write(self, plan: ScalePlan, output: str | Path) -> None:
        _atomic_json(Path(output), plan.to_dict(include_partitions=True))


@dataclass(frozen=True, slots=True)
class ValidationPolicy:
    sample_ppm: int = 10_000
    exhaustive_risks: tuple[str, ...] = ScalePolicy().exhaustive_risks
    error_example_limit: int = 1_000

    def __post_init__(self) -> None:
        if not 0 <= self.sample_ppm <= 1_000_000:
            raise ValueError("sample_ppm must be between 0 and 1,000,000")
        if self.error_example_limit < 0:
            raise ValueError("error_example_limit cannot be negative")


def _sampled(spec: CampaignSpec, epoch_index: int, generator_index: int, ppm: int) -> bool:
    if ppm == 0:
        return False
    token = int(_sha256(f"{spec.fingerprint}:{epoch_index}:{generator_index}")[:16], 16)
    return token % 1_000_000 < ppm


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


@dataclass(frozen=True, slots=True)
class ValidationReport:
    status: str
    epoch_index: int
    generator_start: int
    generator_stop: int
    generator_bundles_checked: int
    logical_records_checked: int
    deep_validations: int
    exhaustive_risk_validations: int
    sampled_validations: int
    risk_histogram: Mapping[str, int]
    error_count: int
    error_examples: tuple[str, ...]
    sha256: str
    completed_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["risk_histogram"] = dict(self.risk_histogram)
        return payload


def validate_epoch_range(
    base: CampaignSpec,
    epoch_index: int,
    *,
    start: int = 0,
    stop: int | None = None,
    policy: ValidationPolicy | None = None,
) -> ValidationReport:
    """Validate every bundle structurally and deep-check samples plus all risky bundles."""
    validation = policy or ValidationPolicy()
    spec = epoch_spec(base, epoch_index)
    upper = spec.generator_count if stop is None else stop
    if not 0 <= start <= upper <= spec.generator_count:
        raise ValueError("range must satisfy 0 <= start <= stop <= generator_count")
    digest = hashlib.sha256()
    errors: list[str] = []
    error_count = 0
    logical_records = 0
    deep_count = 0
    risk_deep = 0
    sampled_deep = 0
    risks: Counter[str] = Counter()

    def record_error(message: str) -> None:
        nonlocal error_count
        error_count += 1
        if len(errors) < validation.error_example_limit:
            errors.append(message)

    for generator_index in range(start, upper):
        bundle = list(
            iter_epoch_bundles(
                base,
                epoch_index,
                start=generator_index,
                stop=generator_index + 1,
            )
        )
        expected_count = base.records_per_bundle
        if len(bundle) != expected_count:
            record_error(
                f"bundle {generator_index}: expected {expected_count} records, got {len(bundle)}"
            )
            continue
        generator = bundle[0]
        if generator.get("kind") != "generator_candidate":
            record_error(f"bundle {generator_index}: first record is not generator_candidate")
            continue
        payload = generator.get("payload", {})
        risk = str(payload.get("risk", "unknown"))
        risks[risk] += 1
        expected_benchmarks = tuple(str(value) for value in payload.get("benchmark_ids", ()))
        actual_benchmarks = tuple(str(record.get("addition_id")) for record in bundle[1:])
        if expected_benchmarks != actual_benchmarks:
            record_error(f"bundle {generator_index}: benchmark link mismatch")
        if len(set(record.get("addition_id") for record in bundle)) != len(bundle):
            record_error(f"bundle {generator_index}: duplicate IDs inside bundle")
        for record in bundle:
            digest.update((_canonical_json(record) + "\n").encode("utf-8"))
            logical_records += 1

        is_risk = risk in validation.exhaustive_risks
        is_sample = _sampled(spec, epoch_index, generator_index, validation.sample_ppm)
        if not (is_risk or is_sample):
            continue
        deep_count += 1
        risk_deep += int(is_risk)
        sampled_deep += int(is_sample and not is_risk)
        generator_id = str(generator.get("addition_id"))
        if not generator.get("provenance"):
            record_error(f"bundle {generator_index}: missing generator provenance")
        if not payload.get("oak_gate"):
            record_error(f"bundle {generator_index}: missing OAK gate")
        for benchmark in bundle[1:]:
            benchmark_payload = benchmark.get("payload", {})
            if benchmark_payload.get("generator_id") != generator_id:
                record_error(f"bundle {generator_index}: benchmark generator_id mismatch")
            parameters = benchmark_payload.get("parameters", {})
            if not all(_finite_number(value) for value in parameters.values()):
                record_error(f"bundle {generator_index}: non-finite benchmark parameter")
            if benchmark_payload.get("expected", {}).get("finite") is not True:
                record_error(f"bundle {generator_index}: finite-output invariant missing")
            if not benchmark.get("provenance"):
                record_error(f"bundle {generator_index}: missing benchmark provenance")

    return ValidationReport(
        status="valid" if error_count == 0 else "invalid",
        epoch_index=epoch_index,
        generator_start=start,
        generator_stop=upper,
        generator_bundles_checked=upper - start,
        logical_records_checked=logical_records,
        deep_validations=deep_count,
        exhaustive_risk_validations=risk_deep,
        sampled_validations=sampled_deep,
        risk_histogram=dict(sorted(risks.items())),
        error_count=error_count,
        error_examples=tuple(errors),
        sha256=digest.hexdigest(),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


@dataclass(frozen=True, slots=True)
class FrontierObservation:
    requested_logical_records: int
    processed_logical_records: int
    success: bool
    quality_score: float
    pressure: Mapping[str, float]
    elapsed_seconds: float
    bytes_written: int = 0
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _positive("requested_logical_records", self.requested_logical_records)
        if self.processed_logical_records < 0:
            raise ValueError("processed_logical_records cannot be negative")
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("quality_score must be between 0 and 1")
        if self.elapsed_seconds < 0 or self.bytes_written < 0:
            raise ValueError("elapsed_seconds and bytes_written cannot be negative")
        if any(value < 0 for value in self.pressure.values()):
            raise ValueError("pressure values cannot be negative")

    @property
    def peak_pressure(self) -> float:
        return max(self.pressure.values(), default=0.0)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "FrontierObservation":
        pressure = raw.get("pressure", {})
        if not isinstance(pressure, Mapping):
            raise ValueError("pressure must be an object")
        notes = raw.get("notes", ())
        if isinstance(notes, str):
            notes = (notes,)
        return cls(
            requested_logical_records=int(raw["requested_logical_records"]),
            processed_logical_records=int(raw["processed_logical_records"]),
            success=bool(raw["success"]),
            quality_score=float(raw["quality_score"]),
            pressure={str(key): float(value) for key, value in pressure.items()},
            elapsed_seconds=float(raw.get("elapsed_seconds", 0.0)),
            bytes_written=int(raw.get("bytes_written", 0)),
            notes=tuple(str(value) for value in notes),
        )


@dataclass(frozen=True, slots=True)
class FrontierPolicy:
    quality_floor: float = 0.99
    pressure_soft: float = 0.70
    pressure_hard: float = 1.00
    stable_growth: float = 4.0
    cautious_growth: float = 1.5
    recovery_factor: float = 0.5

    def __post_init__(self) -> None:
        if not 0 <= self.quality_floor <= 1:
            raise ValueError("quality_floor must be between 0 and 1")
        if not 0 <= self.pressure_soft < self.pressure_hard:
            raise ValueError("pressure thresholds must satisfy 0 <= soft < hard")
        if self.stable_growth <= 1 or self.cautious_growth <= 1:
            raise ValueError("growth factors must exceed 1")
        if not 0 < self.recovery_factor < 1:
            raise ValueError("recovery_factor must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class FrontierDecision:
    event_type: str
    previous_requested_records: int
    processed_records: int
    next_requested_records: int
    growth_factor: float
    peak_pressure: float
    limiting_dimensions: tuple[str, ...]
    quality_score: float
    reason: str
    timestamp: str
    no_permanent_total_addition_cap: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decide_next_frontier(
    observation: FrontierObservation,
    *,
    records_per_bundle: int,
    policy: FrontierPolicy | None = None,
) -> FrontierDecision:
    control = policy or FrontierPolicy()
    _positive("records_per_bundle", records_per_bundle)
    healthy = (
        observation.success
        and observation.quality_score >= control.quality_floor
        and observation.peak_pressure < control.pressure_hard
    )
    if healthy:
        factor = (
            control.stable_growth
            if observation.peak_pressure < control.pressure_soft
            else control.cautious_growth
        )
        basis = max(observation.processed_logical_records, observation.requested_logical_records)
        next_records = max(basis + records_per_bundle, math.ceil(basis * factor))
        event_type = "M+_breakthrough"
        reason = "healthy frontier; expand the next finite workload"
    else:
        factor = control.recovery_factor
        basis = observation.processed_logical_records or observation.requested_logical_records
        next_records = max(records_per_bundle, math.floor(basis * factor))
        event_type = "M-_saturation"
        reason = "quality, pressure, or execution frontier requires redesign and replay"
    next_records = math.ceil(next_records / records_per_bundle) * records_per_bundle
    limiting = tuple(
        sorted(
            name
            for name, value in observation.pressure.items()
            if value >= control.pressure_hard
        )
    )
    if observation.quality_score < control.quality_floor:
        limiting += ("quality",)
    if not observation.success:
        limiting += ("execution",)
    return FrontierDecision(
        event_type=event_type,
        previous_requested_records=observation.requested_logical_records,
        processed_records=observation.processed_logical_records,
        next_requested_records=next_records,
        growth_factor=factor,
        peak_pressure=observation.peak_pressure,
        limiting_dimensions=tuple(dict.fromkeys(limiting or ("none",))),
        quality_score=observation.quality_score,
        reason=reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


class FrontierLedger:
    """Append-only M+/M- frontier memory."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, decision: FrontierDecision) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_json(decision.to_dict()) + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def write_partition_matrix(plan: ScalePlan, path: str | Path) -> None:
    """Write a GitHub-Actions-compatible matrix without embedding record payloads."""
    include = [
        {
            "global_partition_index": partition.global_partition_index,
            "epoch_index": partition.epoch_index,
            "generator_start": partition.generator_start,
            "generator_stop": partition.generator_stop,
            "logical_records": partition.logical_records,
        }
        for partition in plan.partitions
    ]
    _atomic_json(Path(path), {"include": include})
