"""Virtual distributed frontier planning for Ω-GENERATOR-DISCOVERY R0.5.

R0.5 addresses plans that are too large to materialize as Python tuples or
GitHub Actions matrices. Every concrete run remains finite and resource
governed; no value in this module is a permanent total-addition ceiling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import math
from typing import Any, Iterator, Mapping, Sequence

FRONTIER_PROFILES: dict[str, int] = {
    "ten-billion": 10_000_000_000,
    "hundred-billion": 100_000_000_000,
    "trillion": 1_000_000_000_000,
    "ten-trillion": 10_000_000_000_000,
    "quadrillion": 1_000_000_000_000_000,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(value: str | bytes) -> str:
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _positive(name: str, value: int) -> int:
    value = int(value)
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def _utc(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return current.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class BaseCampaignShape:
    """Only the cardinality and identity required by the virtual planner."""

    campaign_id: str
    campaign_fingerprint: str
    generator_count: int
    records_per_bundle: int

    def __post_init__(self) -> None:
        if not self.campaign_id.strip() or not self.campaign_fingerprint.strip():
            raise ValueError("campaign identity cannot be empty")
        _positive("generator_count", self.generator_count)
        _positive("records_per_bundle", self.records_per_bundle)

    @property
    def logical_records_per_epoch(self) -> int:
        return self.generator_count * self.records_per_bundle

    @classmethod
    def from_campaign_spec(cls, spec: Any) -> "BaseCampaignShape":
        return cls(
            campaign_id=str(spec.campaign_id),
            campaign_fingerprint=str(spec.fingerprint),
            generator_count=int(spec.generator_count),
            records_per_bundle=int(spec.records_per_bundle),
        )


@dataclass(frozen=True, slots=True)
class VirtualFrontierPolicy:
    """Execution granularity, not a total campaign maximum."""

    target_records_per_partition: int = 250_000
    bundles_per_shard: int = 2_048
    max_partitions_per_wave: int = 256
    max_matrix_entries: int = 256
    lease_seconds: int = 3_600
    validation_sample_ppm: int = 10_000

    def __post_init__(self) -> None:
        for name in (
            "target_records_per_partition",
            "bundles_per_shard",
            "max_partitions_per_wave",
            "max_matrix_entries",
            "lease_seconds",
        ):
            _positive(name, getattr(self, name))
        if not 0 <= self.validation_sample_ppm <= 1_000_000:
            raise ValueError("validation_sample_ppm must be between 0 and 1,000,000")


@dataclass(frozen=True, slots=True)
class VirtualPartition:
    global_partition_index: int
    epoch_index: int
    epoch_partition_index: int
    epoch_partition_count: int
    generator_start: int
    generator_stop: int
    generator_bundles: int
    logical_records: int
    suggested_shards: int
    partition_key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VirtualEpoch:
    epoch_index: int
    generator_bundles: int
    logical_records: int
    partition_count: int
    first_global_partition: int
    last_global_partition: int
    campaign_id: str
    epoch_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VirtualFrontierPlan:
    """Analytical plan whose memory usage is independent of target scale."""

    shape: BaseCampaignShape
    policy: VirtualFrontierPolicy
    requested_logical_records: int
    planned_logical_records: int
    rounding_overage_records: int
    total_generator_bundles: int
    full_epochs: int
    tail_generator_bundles: int
    epoch_count: int
    bundles_per_partition: int
    full_epoch_partition_count: int
    tail_partition_count: int
    total_partition_count: int
    plan_fingerprint: str
    generated_at: str
    no_permanent_total_addition_cap: bool = True

    @classmethod
    def build(
        cls,
        shape: BaseCampaignShape,
        target_logical_records: int,
        policy: VirtualFrontierPolicy | None = None,
    ) -> "VirtualFrontierPlan":
        control = policy or VirtualFrontierPolicy()
        target = _positive("target_logical_records", target_logical_records)
        bundles = math.ceil(target / shape.records_per_bundle)
        planned = bundles * shape.records_per_bundle
        full_epochs, tail = divmod(bundles, shape.generator_count)
        epoch_count = full_epochs + int(tail > 0)
        bundles_per_partition = max(
            1, control.target_records_per_partition // shape.records_per_bundle
        )
        full_partitions = math.ceil(shape.generator_count / bundles_per_partition)
        tail_partitions = math.ceil(tail / bundles_per_partition) if tail else 0
        partition_count = full_epochs * full_partitions + tail_partitions
        definition = {
            "schema_version": "R0.5",
            "shape": asdict(shape),
            "policy": asdict(control),
            "requested_logical_records": target,
            "planned_logical_records": planned,
            "total_generator_bundles": bundles,
            "full_epochs": full_epochs,
            "tail_generator_bundles": tail,
            "bundles_per_partition": bundles_per_partition,
        }
        return cls(
            shape=shape,
            policy=control,
            requested_logical_records=target,
            planned_logical_records=planned,
            rounding_overage_records=planned - target,
            total_generator_bundles=bundles,
            full_epochs=full_epochs,
            tail_generator_bundles=tail,
            epoch_count=epoch_count,
            bundles_per_partition=bundles_per_partition,
            full_epoch_partition_count=full_partitions,
            tail_partition_count=tail_partitions,
            total_partition_count=partition_count,
            plan_fingerprint=sha256_hex(canonical_json(definition)),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "R0.5",
            "shape": asdict(self.shape),
            "policy": asdict(self.policy),
            "requested_logical_records": self.requested_logical_records,
            "planned_logical_records": self.planned_logical_records,
            "rounding_overage_records": self.rounding_overage_records,
            "total_generator_bundles": self.total_generator_bundles,
            "full_epochs": self.full_epochs,
            "tail_generator_bundles": self.tail_generator_bundles,
            "epoch_count": self.epoch_count,
            "bundles_per_partition": self.bundles_per_partition,
            "full_epoch_partition_count": self.full_epoch_partition_count,
            "tail_partition_count": self.tail_partition_count,
            "total_partition_count": self.total_partition_count,
            "plan_fingerprint": self.plan_fingerprint,
            "generated_at": self.generated_at,
            "no_permanent_total_addition_cap": True,
            "oak_boundary": (
                "Virtual cardinality is not emitted data, scientific evidence, "
                "novelty, patentability, safety, or market validation."
            ),
        }

    @property
    def full_partition_span(self) -> int:
        return self.full_epochs * self.full_epoch_partition_count

    def _epoch_bundles(self, epoch_index: int) -> int:
        if not 0 <= epoch_index < self.epoch_count:
            raise IndexError("epoch index outside plan")
        if epoch_index < self.full_epochs:
            return self.shape.generator_count
        return self.tail_generator_bundles

    def epoch_at(self, epoch_index: int) -> VirtualEpoch:
        bundles = self._epoch_bundles(epoch_index)
        partitions = (
            self.full_epoch_partition_count
            if epoch_index < self.full_epochs
            else self.tail_partition_count
        )
        first = epoch_index * self.full_epoch_partition_count
        fingerprint = sha256_hex(
            f"{self.shape.campaign_fingerprint}:R0.5:epoch:{epoch_index}"
        )
        return VirtualEpoch(
            epoch_index=epoch_index,
            generator_bundles=bundles,
            logical_records=bundles * self.shape.records_per_bundle,
            partition_count=partitions,
            first_global_partition=first,
            last_global_partition=first + partitions - 1,
            campaign_id=f"{self.shape.campaign_id}/frontier-epoch-{epoch_index:012d}",
            epoch_fingerprint=fingerprint,
        )

    def partition_at(self, global_partition_index: int) -> VirtualPartition:
        index = int(global_partition_index)
        if not 0 <= index < self.total_partition_count:
            raise IndexError("global partition index outside plan")
        if index < self.full_partition_span:
            epoch_index, local_index = divmod(
                index, self.full_epoch_partition_count
            )
            epoch_bundles = self.shape.generator_count
            epoch_partition_count = self.full_epoch_partition_count
        else:
            epoch_index = self.full_epochs
            local_index = index - self.full_partition_span
            epoch_bundles = self.tail_generator_bundles
            epoch_partition_count = self.tail_partition_count
        start = local_index * self.bundles_per_partition
        stop = min(start + self.bundles_per_partition, epoch_bundles)
        bundles = stop - start
        logical_records = bundles * self.shape.records_per_bundle
        key_seed = f"{self.plan_fingerprint}:{index}:{epoch_index}:{start}:{stop}"
        return VirtualPartition(
            global_partition_index=index,
            epoch_index=epoch_index,
            epoch_partition_index=local_index,
            epoch_partition_count=epoch_partition_count,
            generator_start=start,
            generator_stop=stop,
            generator_bundles=bundles,
            logical_records=logical_records,
            suggested_shards=math.ceil(bundles / self.policy.bundles_per_shard),
            partition_key=f"P-{index:015d}-{sha256_hex(key_seed)[:16]}",
        )

    def iter_partition_page(
        self, cursor: int = 0, limit: int | None = None
    ) -> Iterator[VirtualPartition]:
        start = int(cursor)
        if not 0 <= start <= self.total_partition_count:
            raise ValueError("cursor outside partition range")
        page_limit = self.policy.max_matrix_entries if limit is None else int(limit)
        _positive("limit", page_limit)
        stop = min(start + page_limit, self.total_partition_count)
        for index in range(start, stop):
            yield self.partition_at(index)

    def partition_page(
        self, cursor: int = 0, limit: int | None = None
    ) -> dict[str, Any]:
        entries = tuple(self.iter_partition_page(cursor, limit))
        next_cursor = (
            entries[-1].global_partition_index + 1
            if entries
            else self.total_partition_count
        )
        return {
            "plan_fingerprint": self.plan_fingerprint,
            "cursor": cursor,
            "count": len(entries),
            "next_cursor": next_cursor,
            "complete": next_cursor >= self.total_partition_count,
            "include": [entry.to_dict() for entry in entries],
        }

    def epoch_page(self, cursor: int = 0, limit: int = 128) -> dict[str, Any]:
        start, page_limit = int(cursor), _positive("limit", limit)
        if not 0 <= start <= self.epoch_count:
            raise ValueError("cursor outside epoch range")
        stop = min(start + page_limit, self.epoch_count)
        epochs = [self.epoch_at(index).to_dict() for index in range(start, stop)]
        return {
            "plan_fingerprint": self.plan_fingerprint,
            "cursor": start,
            "count": len(epochs),
            "next_cursor": stop,
            "complete": stop >= self.epoch_count,
            "epochs": epochs,
        }


def resolve_frontier_target(
    *, profile: str | None = None, target_records: int | None = None
) -> int:
    if (profile is None) == (target_records is None):
        raise ValueError("provide exactly one of profile or target_records")
    if target_records is not None:
        return _positive("target_records", target_records)
    assert profile is not None
    try:
        return FRONTIER_PROFILES[profile]
    except KeyError as exc:
        raise ValueError(f"unknown frontier profile: {profile}") from exc


@dataclass(frozen=True, slots=True)
class ResourceModel:
    bytes_per_record: int = 640
    nanoseconds_per_record: int = 25_000
    cost_microunits_per_record: int = 1
    records_per_api_call: int = 10_000
    records_per_file: int = 100_000
    records_per_commit: int = 2_000_000

    def __post_init__(self) -> None:
        for name in (
            "bytes_per_record",
            "nanoseconds_per_record",
            "cost_microunits_per_record",
            "records_per_api_call",
            "records_per_file",
            "records_per_commit",
        ):
            _positive(name, getattr(self, name))


@dataclass(frozen=True, slots=True)
class ResourceUsage:
    logical_records: int = 0
    bytes_written: int = 0
    nanoseconds: int = 0
    cost_microunits: int = 0
    api_calls: int = 0
    files: int = 0
    commits: int = 0

    @classmethod
    def estimate(cls, logical_records: int, model: ResourceModel) -> "ResourceUsage":
        records = max(0, int(logical_records))
        if records == 0:
            return cls()
        return cls(
            logical_records=records,
            bytes_written=records * model.bytes_per_record,
            nanoseconds=records * model.nanoseconds_per_record,
            cost_microunits=records * model.cost_microunits_per_record,
            api_calls=math.ceil(records / model.records_per_api_call),
            files=math.ceil(records / model.records_per_file),
            commits=math.ceil(records / model.records_per_commit),
        )

    def __add__(self, other: "ResourceUsage") -> "ResourceUsage":
        return ResourceUsage(
            logical_records=self.logical_records + other.logical_records,
            bytes_written=self.bytes_written + other.bytes_written,
            nanoseconds=self.nanoseconds + other.nanoseconds,
            cost_microunits=self.cost_microunits + other.cost_microunits,
            api_calls=self.api_calls + other.api_calls,
            files=self.files + other.files,
            commits=self.commits + other.commits,
        )

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BudgetEnvelope:
    max_logical_records: int
    max_bytes_written: int
    max_nanoseconds: int
    max_cost_microunits: int
    max_api_calls: int
    max_files: int
    max_commits: int

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            _positive(name, value)

    def violations(self, usage: ResourceUsage) -> tuple[str, ...]:
        mapping = {
            "logical_records": (usage.logical_records, self.max_logical_records),
            "bytes_written": (usage.bytes_written, self.max_bytes_written),
            "nanoseconds": (usage.nanoseconds, self.max_nanoseconds),
            "cost_microunits": (usage.cost_microunits, self.max_cost_microunits),
            "api_calls": (usage.api_calls, self.max_api_calls),
            "files": (usage.files, self.max_files),
            "commits": (usage.commits, self.max_commits),
        }
        return tuple(
            name for name, (actual, maximum) in mapping.items() if actual > maximum
        )

    def fits(self, usage: ResourceUsage) -> bool:
        return not self.violations(usage)


@dataclass(frozen=True, slots=True)
class WavePlan:
    status: str
    start_cursor: int
    next_cursor: int
    partition_count: int
    logical_records: int
    usage: ResourceUsage
    limiting_dimensions: tuple[str, ...]
    partitions: tuple[VirtualPartition, ...]

    def to_dict(self, *, include_partitions: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "start_cursor": self.start_cursor,
            "next_cursor": self.next_cursor,
            "partition_count": self.partition_count,
            "logical_records": self.logical_records,
            "usage": self.usage.to_dict(),
            "limiting_dimensions": list(self.limiting_dimensions),
        }
        if include_partitions:
            payload["partitions"] = [value.to_dict() for value in self.partitions]
        return payload


class AdaptiveWaveScheduler:
    """Select the largest contiguous page that fits all execution budgets."""

    def __init__(
        self,
        model: ResourceModel | None = None,
        max_partitions_per_wave: int = 256,
    ):
        self.model = model or ResourceModel()
        self.max_partitions_per_wave = _positive(
            "max_partitions_per_wave", max_partitions_per_wave
        )

    def schedule(
        self,
        plan: VirtualFrontierPlan,
        cursor: int,
        budget: BudgetEnvelope,
    ) -> WavePlan:
        start = int(cursor)
        if not 0 <= start <= plan.total_partition_count:
            raise ValueError("cursor outside partition range")
        selected: list[VirtualPartition] = []
        usage = ResourceUsage()
        limiting: tuple[str, ...] = ()
        for partition in plan.iter_partition_page(start, self.max_partitions_per_wave):
            candidate_usage = usage + ResourceUsage.estimate(
                partition.logical_records, self.model
            )
            violations = budget.violations(candidate_usage)
            if violations:
                limiting = violations
                break
            selected.append(partition)
            usage = candidate_usage
        next_cursor = start + len(selected)
        if start == plan.total_partition_count:
            status = "complete"
        elif selected:
            status = "scheduled"
        else:
            status = "blocked"
        return WavePlan(
            status=status,
            start_cursor=start,
            next_cursor=next_cursor,
            partition_count=len(selected),
            logical_records=usage.logical_records,
            usage=usage,
            limiting_dimensions=limiting,
            partitions=tuple(selected),
        )


class MerkleMountainRange:
    """Streaming Merkle accumulator requiring O(log n) hashes."""

    def __init__(self) -> None:
        self._peaks: list[bytes | None] = []
        self._leaf_count = 0

    @property
    def leaf_count(self) -> int:
        return self._leaf_count

    def append(self, value: bytes | str | Mapping[str, Any]) -> str:
        if isinstance(value, Mapping):
            raw = canonical_json(value).encode("utf-8")
        elif isinstance(value, str):
            raw = value.encode("utf-8")
        else:
            raw = bytes(value)
        node = hashlib.sha256(b"\x00" + raw).digest()
        height = 0
        while height < len(self._peaks) and self._peaks[height] is not None:
            left = self._peaks[height]
            assert left is not None
            node = hashlib.sha256(b"\x01" + left + node).digest()
            self._peaks[height] = None
            height += 1
        if height == len(self._peaks):
            self._peaks.append(node)
        else:
            self._peaks[height] = node
        self._leaf_count += 1
        return node.hex()

    @property
    def root(self) -> str:
        if self._leaf_count == 0:
            return hashlib.sha256(b"\x02empty").hexdigest()
        bag: bytes | None = None
        for height in range(len(self._peaks) - 1, -1, -1):
            peak = self._peaks[height]
            if peak is None:
                continue
            bag = peak if bag is None else hashlib.sha256(b"\x02" + peak + bag).digest()
        assert bag is not None
        return bag.hex()

    def receipt(self) -> dict[str, Any]:
        return {
            "algorithm": "sha256-mmr-v1",
            "leaf_count": self.leaf_count,
            "root": self.root,
            "peak_count": sum(value is not None for value in self._peaks),
        }


@dataclass(frozen=True, slots=True)
class WorkLease:
    plan_fingerprint: str
    partition_key: str
    worker_id: str
    issued_at: str
    expires_at: str
    token: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class LeaseAuthority:
    """Stateless signed leases; callers still persist claim state transactionally."""

    def __init__(self, secret: bytes | str):
        raw = secret.encode("utf-8") if isinstance(secret, str) else bytes(secret)
        if len(raw) < 16:
            raise ValueError("lease secret must be at least 16 bytes")
        self.secret = raw

    def _signature(self, payload: Mapping[str, Any]) -> str:
        return hmac.new(
            self.secret,
            canonical_json(payload).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def issue(
        self,
        plan_fingerprint: str,
        partition_key: str,
        worker_id: str,
        *,
        ttl_seconds: int,
        now: datetime | None = None,
    ) -> WorkLease:
        ttl = _positive("ttl_seconds", ttl_seconds)
        issued = _utc(now)
        expires = issued + timedelta(seconds=ttl)
        payload = {
            "plan_fingerprint": plan_fingerprint,
            "partition_key": partition_key,
            "worker_id": worker_id,
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
        }
        return WorkLease(**payload, token=self._signature(payload))

    def verify(
        self, lease: WorkLease | Mapping[str, Any], *, now: datetime | None = None
    ) -> bool:
        raw = lease.to_dict() if isinstance(lease, WorkLease) else dict(lease)
        token = str(raw.pop("token", ""))
        expected = self._signature(raw)
        if not hmac.compare_digest(token, expected):
            return False
        try:
            expires = datetime.fromisoformat(str(raw["expires_at"]))
        except (KeyError, ValueError):
            return False
        return _utc(now) < _utc(expires)


@dataclass(frozen=True, slots=True)
class PromotionEvidence:
    structural_validation: bool = False
    deterministic_reproduction: bool = False
    provenance_complete: bool = False
    negative_controls: bool = False
    baseline_comparison: bool = False
    uncertainty_quantified: bool = False
    real_data: bool = False
    independent_review: bool = False
    safety_review: bool = False


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    requested_level: str
    status: str
    missing_requirements: tuple[str, ...]
    warning: str
    decision_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["missing_requirements"] = list(self.missing_requirements)
        return payload


PROMOTION_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "candidate": (
        "structural_validation",
        "deterministic_reproduction",
        "provenance_complete",
    ),
    "validated_synthetic": (
        "structural_validation",
        "deterministic_reproduction",
        "provenance_complete",
        "negative_controls",
        "baseline_comparison",
        "uncertainty_quantified",
    ),
    "empirical": (
        "structural_validation",
        "deterministic_reproduction",
        "provenance_complete",
        "negative_controls",
        "baseline_comparison",
        "uncertainty_quantified",
        "real_data",
        "safety_review",
    ),
    "canon": (
        "structural_validation",
        "deterministic_reproduction",
        "provenance_complete",
        "negative_controls",
        "baseline_comparison",
        "uncertainty_quantified",
        "real_data",
        "independent_review",
        "safety_review",
    ),
}


def evaluate_promotion(
    requested_level: str, evidence: PromotionEvidence
) -> PromotionDecision:
    try:
        requirements = PROMOTION_REQUIREMENTS[requested_level]
    except KeyError as exc:
        raise ValueError(f"unknown promotion level: {requested_level}") from exc
    missing = tuple(name for name in requirements if not bool(getattr(evidence, name)))
    status = "promote" if not missing else "block"
    warning = (
        "Volume and Merkle integrity never substitute for empirical truth, "
        "novelty, safety, patentability, or market evidence."
    )
    fingerprint = sha256_hex(
        canonical_json(
            {
                "requested_level": requested_level,
                "evidence": asdict(evidence),
                "missing": missing,
                "status": status,
            }
        )
    )
    return PromotionDecision(
        requested_level=requested_level,
        status=status,
        missing_requirements=missing,
        warning=warning,
        decision_fingerprint=fingerprint,
    )


@dataclass(frozen=True, slots=True)
class FrontierReceipt:
    plan_fingerprint: str
    partition_key: str
    worker_id: str
    logical_records: int
    generator_bundles: int
    mmr_root: str
    leaf_count: int
    validation_status: str
    previous_receipt_hash: str
    completed_at: str
    receipt_hash: str

    @classmethod
    def create(
        cls,
        *,
        plan_fingerprint: str,
        partition_key: str,
        worker_id: str,
        logical_records: int,
        generator_bundles: int,
        mmr_root: str,
        leaf_count: int,
        validation_status: str,
        previous_receipt_hash: str = "",
        completed_at: datetime | None = None,
    ) -> "FrontierReceipt":
        completed = _utc(completed_at).isoformat()
        body = {
            "schema_version": "R0.5",
            "plan_fingerprint": plan_fingerprint,
            "partition_key": partition_key,
            "worker_id": worker_id,
            "logical_records": int(logical_records),
            "generator_bundles": int(generator_bundles),
            "mmr_root": mmr_root,
            "leaf_count": int(leaf_count),
            "validation_status": validation_status,
            "previous_receipt_hash": previous_receipt_hash,
            "completed_at": completed,
        }
        return cls(
            **{key: value for key, value in body.items() if key != "schema_version"},
            receipt_hash=sha256_hex(canonical_json(body)),
        )

    def verify(self) -> bool:
        recreated = FrontierReceipt.create(
            plan_fingerprint=self.plan_fingerprint,
            partition_key=self.partition_key,
            worker_id=self.worker_id,
            logical_records=self.logical_records,
            generator_bundles=self.generator_bundles,
            mmr_root=self.mmr_root,
            leaf_count=self.leaf_count,
            validation_status=self.validation_status,
            previous_receipt_hash=self.previous_receipt_hash,
            completed_at=datetime.fromisoformat(self.completed_at),
        )
        return hmac.compare_digest(self.receipt_hash, recreated.receipt_hash)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def receipt_chain_valid(receipts: Sequence[FrontierReceipt]) -> bool:
    previous = ""
    for receipt in receipts:
        if not receipt.verify() or receipt.previous_receipt_hash != previous:
            return False
        previous = receipt.receipt_hash
    return True
