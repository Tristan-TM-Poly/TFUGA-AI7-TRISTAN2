"""Unbounded-by-design streaming corpus frontier for Ω-NARUTO-HMAGFM.

No permanent total-record ceiling is encoded. Each execution is finite and
resource-bounded, while global ordinals continue across deterministic epochs.
Records are lazy, sharded, hashed, checkpointed, and resumable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from time import monotonic
from typing import Iterator, Mapping, Sequence


@dataclass(frozen=True)
class CorpusAxes:
    operators: tuple[str, ...]
    domains: tuple[str, ...]
    epistemic_states: tuple[str, ...]
    evidence_modes: tuple[str, ...]
    perturbations: tuple[str, ...]
    gate_profiles: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, values in asdict(self).items():
            if not values:
                raise ValueError(f"axis {name} cannot be empty")
            if len(values) != len(set(values)):
                raise ValueError(f"axis {name} contains duplicates")

    @property
    def cardinality(self) -> int:
        total = 1
        for values in asdict(self).values():
            total *= len(values)
        return total

    @property
    def ordered_axes(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        return (
            ("operator", self.operators),
            ("domain", self.domains),
            ("epistemic_state", self.epistemic_states),
            ("evidence_mode", self.evidence_modes),
            ("perturbation", self.perturbations),
            ("gate_profile", self.gate_profiles),
        )


@dataclass(frozen=True)
class FrontierBudget:
    requested_records: int | None = None
    available_bytes: int | None = None
    estimated_bytes_per_record: int = 512
    minimum_experiment_records: int = 25_000
    growth_factor: float = 2.0

    def __post_init__(self) -> None:
        if self.requested_records is not None and self.requested_records < 0:
            raise ValueError("requested_records must be non-negative")
        if self.available_bytes is not None and self.available_bytes < 0:
            raise ValueError("available_bytes must be non-negative")
        if self.estimated_bytes_per_record <= 0:
            raise ValueError("estimated_bytes_per_record must be positive")
        if self.minimum_experiment_records <= 0:
            raise ValueError("minimum_experiment_records must be positive")
        if self.growth_factor <= 1.0:
            raise ValueError("growth_factor must exceed 1")

    def resolve_target(self, *, previous_success: int | None = None) -> int:
        """Resolve one finite run target without creating an architecture cap."""

        if self.requested_records is not None:
            return self.requested_records
        candidates = [self.minimum_experiment_records]
        if previous_success is not None and previous_success > 0:
            candidates.append(max(previous_success + 1, int(previous_success * self.growth_factor)))
        if self.available_bytes is not None:
            candidates.append(self.available_bytes // self.estimated_bytes_per_record)
        return max(0, min(candidates) if self.available_bytes is not None else max(candidates))


@dataclass(frozen=True)
class CorpusRecord:
    ordinal: int
    epoch: int
    local_ordinal: int
    record_id: str
    operator: str
    domain: str
    epistemic_state: str
    evidence_mode: str
    perturbation: str
    gate_profile: str
    hypothesis: str
    expected_oak_action: str
    non_claim: str

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class ShardReceipt:
    path: str
    first_ordinal: int
    last_ordinal: int
    record_count: int
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class CorpusManifest:
    schema: str
    target_records: int
    written_records: int
    start_ordinal: int
    next_ordinal: int
    axis_cardinality: int
    completed_epochs: int
    elapsed_seconds: float
    shards: tuple[ShardReceipt, ...]
    corpus_sha256: str
    complete: bool
    non_claim: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["shards"] = [asdict(item) for item in self.shards]
        return payload


@dataclass(frozen=True)
class FrontierCheckpoint:
    schema: str
    next_ordinal: int
    written_records: int
    shard_index: int
    corpus_sha256: str

    @classmethod
    def load(cls, path: Path) -> "FrontierCheckpoint | None":
        if not path.exists():
            return None
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    def write_atomic(self, path: Path) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)


def default_axes() -> CorpusAxes:
    return CorpusAxes(
        operators=(
            "kage_bunshin",
            "rasengan_refinement",
            "sage_sensor_fusion",
            "byakugan_observability",
            "sharingan_prediction",
            "genjutsu_red_team",
            "seal_permission_gate",
            "village_federation",
            "biju_sandbox",
            "talk_no_jutsu_resolution",
            "mminus_residue",
            "oak_merge",
        ),
        domains=(
            "software",
            "spectroscopy",
            "materials",
            "energy",
            "education",
            "documentation",
            "game_engine",
            "company_operations",
        ),
        epistemic_states=(
            "F0_FICTION",
            "H2_HYPOTHESIS",
            "D3_DEFINITION",
            "S4_SIMULATION",
            "P5_PROTOTYPE",
            "B6_BENCHMARK",
            "E7_EVIDENCE",
        ),
        evidence_modes=(
            "none",
            "single_artifact",
            "multi_artifact",
            "counterevidence_present",
        ),
        perturbations=(
            "baseline",
            "confidence_down",
            "uncertainty_up",
            "evidence_removed",
            "risk_up",
            "cost_up",
        ),
        gate_profiles=(
            "public_safe",
            "human_review_pending",
            "privacy_block",
            "ip_block",
        ),
    )


def decode_ordinal(ordinal: int, axes: CorpusAxes) -> Mapping[str, str]:
    """Decode any global ordinal by wrapping through deterministic epochs."""

    if ordinal < 0:
        raise ValueError("ordinal must be non-negative")
    _, remainder = divmod(ordinal, axes.cardinality)
    decoded: dict[str, str] = {}
    ordered = axes.ordered_axes
    for name, values in reversed(ordered):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    return {name: decoded[name] for name, _ in ordered}


def _expected_action(fields: Mapping[str, str]) -> str:
    gate = fields["gate_profile"]
    evidence = fields["evidence_mode"]
    if gate.endswith("block"):
        return "BLOCK_AND_RETAIN_MMINUS"
    if evidence == "none":
        return "REJECT_UNSUPPORTED_AND_RETAIN_MMINUS"
    if gate == "human_review_pending":
        return "WARN_REQUIRE_HUMAN_REVIEW"
    if fields["perturbation"] == "risk_up":
        return "RECOMPUTE_GATES_BEFORE_SELECTION"
    return "RANK_LOCALLY_WITHOUT_CERTIFICATION"


def record_from_ordinal(ordinal: int, axes: CorpusAxes) -> CorpusRecord:
    if ordinal < 0:
        raise ValueError("ordinal must be non-negative")
    epoch, local_ordinal = divmod(ordinal, axes.cardinality)
    fields = decode_ordinal(ordinal, axes)
    canonical = "|".join(
        [f"epoch={epoch}", f"local_ordinal={local_ordinal}"]
        + [f"{key}={value}" for key, value in fields.items()]
    )
    record_id = "naruto-" + sha256(canonical.encode("utf-8")).hexdigest()[:24]
    hypothesis = (
        f"Epoch {epoch}: evaluate {fields['operator']} in {fields['domain']} at "
        f"{fields['epistemic_state']} with {fields['evidence_mode']}, "
        f"{fields['perturbation']}, and {fields['gate_profile']}."
    )
    return CorpusRecord(
        ordinal=ordinal,
        epoch=epoch,
        local_ordinal=local_ordinal,
        record_id=record_id,
        operator=fields["operator"],
        domain=fields["domain"],
        epistemic_state=fields["epistemic_state"],
        evidence_mode=fields["evidence_mode"],
        perturbation=fields["perturbation"],
        gate_profile=fields["gate_profile"],
        hypothesis=hypothesis,
        expected_oak_action=_expected_action(fields),
        non_claim="Generated scenario is a test fixture, not evidence or physical validation.",
    )


def iter_records(
    axes: CorpusAxes,
    *,
    start_ordinal: int = 0,
    record_count: int | None = None,
) -> Iterator[CorpusRecord]:
    if start_ordinal < 0:
        raise ValueError("start_ordinal must be non-negative")
    count = axes.cardinality if record_count is None else max(0, record_count)
    for ordinal in range(start_ordinal, start_ordinal + count):
        yield record_from_ordinal(ordinal, axes)


def _write_shard(path: Path, lines: Sequence[str]) -> ShardReceipt:
    rendered = "\n".join(lines) + "\n"
    encoded = rendered.encode("utf-8")
    path.write_bytes(encoded)
    first = json.loads(lines[0])["ordinal"]
    last = json.loads(lines[-1])["ordinal"]
    return ShardReceipt(
        path=path.name,
        first_ordinal=first,
        last_ordinal=last,
        record_count=len(lines),
        byte_count=len(encoded),
        sha256=sha256(encoded).hexdigest(),
    )


def _load_existing_receipts(output_dir: Path) -> tuple[ShardReceipt, ...]:
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        return ()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return tuple(ShardReceipt(**item) for item in payload.get("shards", []))


def _digest_existing(output_dir: Path, receipts: Sequence[ShardReceipt]) -> "sha256":
    digest = sha256()
    for receipt in receipts:
        digest.update((output_dir / receipt.path).read_bytes())
    return digest


def write_corpus(
    output_dir: Path,
    *,
    axes: CorpusAxes | None = None,
    budget: FrontierBudget | None = None,
    shard_records: int = 5_000,
    resume: bool = False,
) -> CorpusManifest:
    if shard_records <= 0:
        raise ValueError("shard_records must be positive")
    axes = axes or default_axes()
    budget = budget or FrontierBudget()
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.json"
    checkpoint = FrontierCheckpoint.load(checkpoint_path) if resume else None
    existing_receipts = _load_existing_receipts(output_dir) if checkpoint else ()
    start = checkpoint.next_ordinal if checkpoint else 0
    previous = checkpoint.written_records if checkpoint else None
    run_target = budget.resolve_target(previous_success=previous)
    total_target = start + run_target
    start_time = monotonic()
    receipts = list(existing_receipts)
    corpus_digest = _digest_existing(output_dir, existing_receipts)
    buffer: list[str] = []
    written_this_run = 0
    shard_index = checkpoint.shard_index if checkpoint else 0

    for record in iter_records(axes, start_ordinal=start, record_count=run_target):
        line = record.to_json_line()
        buffer.append(line)
        corpus_digest.update((line + "\n").encode("utf-8"))
        written_this_run += 1
        if len(buffer) >= shard_records:
            receipts.append(
                _write_shard(output_dir / f"corpus-{shard_index:06d}.jsonl", buffer)
            )
            shard_index += 1
            buffer = []
            FrontierCheckpoint(
                schema="omega_naruto_frontier.checkpoint.v1",
                next_ordinal=start + written_this_run,
                written_records=start + written_this_run,
                shard_index=shard_index,
                corpus_sha256=corpus_digest.hexdigest(),
            ).write_atomic(checkpoint_path)

    if buffer:
        receipts.append(
            _write_shard(output_dir / f"corpus-{shard_index:06d}.jsonl", buffer)
        )
        shard_index += 1

    total_written = start + written_this_run
    manifest = CorpusManifest(
        schema="omega_naruto_frontier.manifest.v1",
        target_records=total_target,
        written_records=total_written,
        start_ordinal=0,
        next_ordinal=total_written,
        axis_cardinality=axes.cardinality,
        completed_epochs=total_written // axes.cardinality,
        elapsed_seconds=round(monotonic() - start_time, 6),
        shards=tuple(receipts),
        corpus_sha256=corpus_digest.hexdigest(),
        complete=total_written == total_target,
        non_claim=(
            "Corpus scale measures generated test coverage, not scientific truth, "
            "product quality, or universal validity."
        ),
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    FrontierCheckpoint(
        schema="omega_naruto_frontier.checkpoint.v1",
        next_ordinal=total_written,
        written_records=total_written,
        shard_index=shard_index,
        corpus_sha256=manifest.corpus_sha256,
    ).write_atomic(checkpoint_path)
    return manifest
