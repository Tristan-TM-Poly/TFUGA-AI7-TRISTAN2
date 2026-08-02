"""Deterministic, compressed, resumable scale engine for Ω-NARUTO frontier corpora.

This module has no permanent record ceiling. Each invocation is finite and
explicitly bounded by ``target_records``. Global ordinals can start anywhere,
so consecutive runs may continue into arbitrarily many deterministic epochs.

The engine writes independent gzip shards with atomic receipt sidecars. Shards
may be generated sequentially or by multiple local worker processes. Final
validation is streaming and does not retain every record identifier in memory.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from hashlib import sha256
import gzip
import io
import json
from pathlib import Path
from time import monotonic
from typing import Iterable, Iterator, Sequence

from .frontier import CorpusAxes, default_axes, record_from_ordinal


@dataclass(frozen=True)
class ScalePartition:
    partition_id: int
    first_ordinal: int
    record_count: int

    @property
    def last_ordinal(self) -> int:
        return self.first_ordinal + self.record_count - 1


@dataclass(frozen=True)
class ScalePlan:
    schema: str
    start_ordinal: int
    target_records: int
    shard_records: int
    partitions: tuple[ScalePartition, ...]

    @property
    def next_ordinal(self) -> int:
        return self.start_ordinal + self.target_records

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "start_ordinal": self.start_ordinal,
            "target_records": self.target_records,
            "next_ordinal": self.next_ordinal,
            "shard_records": self.shard_records,
            "partition_count": len(self.partitions),
            "partitions": [asdict(item) | {"last_ordinal": item.last_ordinal} for item in self.partitions],
        }


@dataclass(frozen=True)
class ScaleShardReceipt:
    schema: str
    partition_id: int
    path: str
    receipt_path: str
    first_ordinal: int
    last_ordinal: int
    record_count: int
    compressed_bytes: int
    uncompressed_bytes: int
    compressed_sha256: str
    logical_sha256: str
    compression: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ScaleManifest:
    schema: str
    start_ordinal: int
    target_records: int
    written_records: int
    next_ordinal: int
    shard_records: int
    shard_count: int
    worker_count: int
    compression: str
    compression_level: int
    axis_cardinality: int
    completed_epochs_before: int
    completed_epochs_after: int
    partial_epoch_records_after: int
    compressed_bytes: int
    uncompressed_bytes: int
    compression_ratio: float
    logical_corpus_sha256: str
    merkle_root_sha256: str
    elapsed_seconds: float
    records_per_second: float
    resumed_shards: int
    generated_shards: int
    shards: tuple[ScaleShardReceipt, ...]
    complete: bool
    non_claim: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["shards"] = [item.to_dict() for item in self.shards]
        return payload


@dataclass(frozen=True)
class ScaleValidationFinding:
    code: str
    severity: str
    message: str
    path: str | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class ScaleValidationReport:
    schema: str
    valid: bool
    manifest_records: int
    observed_records: int
    observed_shards: int
    expected_next_ordinal: int
    observed_next_ordinal: int
    compressed_bytes: int
    uncompressed_bytes: int
    logical_corpus_sha256: str
    merkle_root_sha256: str
    findings: tuple[ScaleValidationFinding, ...]
    non_claim: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["findings"] = [asdict(item) for item in self.findings]
        return payload


def plan_scale_run(
    *,
    target_records: int,
    shard_records: int,
    start_ordinal: int = 0,
) -> ScalePlan:
    """Partition one finite run without encoding a permanent total limit."""

    if target_records < 0:
        raise ValueError("target_records must be non-negative")
    if shard_records <= 0:
        raise ValueError("shard_records must be positive")
    if start_ordinal < 0:
        raise ValueError("start_ordinal must be non-negative")

    partitions: list[ScalePartition] = []
    remaining = target_records
    first = start_ordinal
    partition_id = 0
    while remaining:
        count = min(shard_records, remaining)
        partitions.append(ScalePartition(partition_id, first, count))
        first += count
        remaining -= count
        partition_id += 1

    return ScalePlan(
        schema="omega_naruto_frontier.scale_plan.v2",
        start_ordinal=start_ordinal,
        target_records=target_records,
        shard_records=shard_records,
        partitions=tuple(partitions),
    )


def _axes_fingerprint(axes: CorpusAxes) -> str:
    payload = json.dumps(
        {name: list(values) for name, values in axes.ordered_axes},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _gzip_bytes(raw: bytes, *, compression_level: int) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        fileobj=buffer,
        compresslevel=compression_level,
        mtime=0,
    ) as handle:
        handle.write(raw)
    return buffer.getvalue()


def _partition_names(partition: ScalePartition) -> tuple[str, str]:
    stem = f"scale-{partition.first_ordinal:015d}-{partition.last_ordinal:015d}"
    return f"{stem}.jsonl.gz", f"{stem}.receipt.json"


def _write_atomic(path: Path, payload: bytes) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    _write_atomic(path, rendered)


def _render_partition(partition: ScalePartition, axes: CorpusAxes) -> bytes:
    lines = [
        record_from_ordinal(ordinal, axes).to_json_line()
        for ordinal in range(partition.first_ordinal, partition.first_ordinal + partition.record_count)
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _generate_partition_job(
    output_dir_text: str,
    partition: ScalePartition,
    axes: CorpusAxes,
    compression_level: int,
) -> ScaleShardReceipt:
    output_dir = Path(output_dir_text)
    data_name, receipt_name = _partition_names(partition)
    raw = _render_partition(partition, axes)
    encoded = _gzip_bytes(raw, compression_level=compression_level)
    data_path = output_dir / data_name
    receipt_path = output_dir / receipt_name
    _write_atomic(data_path, encoded)
    receipt = ScaleShardReceipt(
        schema="omega_naruto_frontier.scale_shard_receipt.v2",
        partition_id=partition.partition_id,
        path=data_name,
        receipt_path=receipt_name,
        first_ordinal=partition.first_ordinal,
        last_ordinal=partition.last_ordinal,
        record_count=partition.record_count,
        compressed_bytes=len(encoded),
        uncompressed_bytes=len(raw),
        compressed_sha256=sha256(encoded).hexdigest(),
        logical_sha256=sha256(raw).hexdigest(),
        compression="gzip",
    )
    _write_json_atomic(receipt_path, receipt.to_dict())
    return receipt


def _read_receipt(path: Path) -> ScaleShardReceipt:
    return ScaleShardReceipt(**json.loads(path.read_text(encoding="utf-8")))


def _receipt_matches_partition(
    output_dir: Path,
    partition: ScalePartition,
    receipt: ScaleShardReceipt,
) -> bool:
    expected_data, expected_receipt = _partition_names(partition)
    if (
        receipt.partition_id != partition.partition_id
        or receipt.path != expected_data
        or receipt.receipt_path != expected_receipt
        or receipt.first_ordinal != partition.first_ordinal
        or receipt.last_ordinal != partition.last_ordinal
        or receipt.record_count != partition.record_count
        or receipt.compression != "gzip"
    ):
        return False
    data_path = output_dir / receipt.path
    if not data_path.exists():
        return False
    encoded = data_path.read_bytes()
    if len(encoded) != receipt.compressed_bytes:
        return False
    if sha256(encoded).hexdigest() != receipt.compressed_sha256:
        return False
    try:
        raw = gzip.decompress(encoded)
    except (OSError, EOFError):
        return False
    return (
        len(raw) == receipt.uncompressed_bytes
        and sha256(raw).hexdigest() == receipt.logical_sha256
    )


def _load_resumable_receipt(
    output_dir: Path,
    partition: ScalePartition,
) -> ScaleShardReceipt | None:
    _, receipt_name = _partition_names(partition)
    receipt_path = output_dir / receipt_name
    if not receipt_path.exists():
        return None
    try:
        receipt = _read_receipt(receipt_path)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return receipt if _receipt_matches_partition(output_dir, partition, receipt) else None


def _stream_logical_bytes(
    output_dir: Path,
    receipts: Sequence[ScaleShardReceipt],
) -> Iterator[bytes]:
    for receipt in receipts:
        encoded = (output_dir / receipt.path).read_bytes()
        yield gzip.decompress(encoded)


def _logical_corpus_hash(output_dir: Path, receipts: Sequence[ScaleShardReceipt]) -> str:
    digest = sha256()
    for raw in _stream_logical_bytes(output_dir, receipts):
        digest.update(raw)
    return digest.hexdigest()


def _merkle_root(receipts: Sequence[ScaleShardReceipt]) -> str:
    digest = sha256()
    for receipt in receipts:
        digest.update(bytes.fromhex(receipt.logical_sha256))
    return digest.hexdigest()


def _write_scale_config(
    output_dir: Path,
    *,
    plan: ScalePlan,
    axes: CorpusAxes,
    compression_level: int,
) -> None:
    config = {
        "schema": "omega_naruto_frontier.scale_config.v2",
        "plan": plan.to_dict(),
        "axes_sha256": _axes_fingerprint(axes),
        "compression": "gzip",
        "compression_level": compression_level,
    }
    config_path = output_dir / "scale-config.json"
    if config_path.exists():
        current = json.loads(config_path.read_text(encoding="utf-8"))
        if current != config:
            raise ValueError("existing scale-config.json does not match requested run")
    else:
        _write_json_atomic(config_path, config)


def write_scale_corpus(
    output_dir: Path,
    *,
    target_records: int,
    shard_records: int = 25_000,
    start_ordinal: int = 0,
    workers: int = 1,
    compression_level: int = 6,
    resume: bool = True,
    axes: CorpusAxes | None = None,
) -> ScaleManifest:
    """Generate a deterministic compressed corpus, optionally in parallel."""

    if workers <= 0:
        raise ValueError("workers must be positive")
    if not 0 <= compression_level <= 9:
        raise ValueError("compression_level must be in [0, 9]")

    axes = axes or default_axes()
    plan = plan_scale_run(
        target_records=target_records,
        shard_records=shard_records,
        start_ordinal=start_ordinal,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_scale_config(
        output_dir,
        plan=plan,
        axes=axes,
        compression_level=compression_level,
    )

    started = monotonic()
    receipts_by_id: dict[int, ScaleShardReceipt] = {}
    missing: list[ScalePartition] = []

    for partition in plan.partitions:
        receipt = _load_resumable_receipt(output_dir, partition) if resume else None
        if receipt is None:
            missing.append(partition)
        else:
            receipts_by_id[partition.partition_id] = receipt

    resumed_shards = len(receipts_by_id)
    if workers == 1 or len(missing) <= 1:
        generated = [
            _generate_partition_job(str(output_dir), partition, axes, compression_level)
            for partition in missing
        ]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            generated = list(
                executor.map(
                    _generate_partition_job,
                    [str(output_dir)] * len(missing),
                    missing,
                    [axes] * len(missing),
                    [compression_level] * len(missing),
                )
            )

    for receipt in generated:
        receipts_by_id[receipt.partition_id] = receipt

    receipts = tuple(receipts_by_id[index] for index in range(len(plan.partitions)))
    written_records = sum(item.record_count for item in receipts)
    compressed_bytes = sum(item.compressed_bytes for item in receipts)
    uncompressed_bytes = sum(item.uncompressed_bytes for item in receipts)
    elapsed = monotonic() - started
    next_ordinal = start_ordinal + written_records
    cardinality = axes.cardinality

    manifest = ScaleManifest(
        schema="omega_naruto_frontier.scale_manifest.v2",
        start_ordinal=start_ordinal,
        target_records=target_records,
        written_records=written_records,
        next_ordinal=next_ordinal,
        shard_records=shard_records,
        shard_count=len(receipts),
        worker_count=workers,
        compression="gzip",
        compression_level=compression_level,
        axis_cardinality=cardinality,
        completed_epochs_before=start_ordinal // cardinality,
        completed_epochs_after=next_ordinal // cardinality,
        partial_epoch_records_after=next_ordinal % cardinality,
        compressed_bytes=compressed_bytes,
        uncompressed_bytes=uncompressed_bytes,
        compression_ratio=(uncompressed_bytes / compressed_bytes if compressed_bytes else 1.0),
        logical_corpus_sha256=_logical_corpus_hash(output_dir, receipts),
        merkle_root_sha256=_merkle_root(receipts),
        elapsed_seconds=round(elapsed, 6),
        records_per_second=round(written_records / elapsed, 3) if elapsed else 0.0,
        resumed_shards=resumed_shards,
        generated_shards=len(generated),
        shards=receipts,
        complete=written_records == target_records,
        non_claim=(
            "Scale, compression, throughput, and integrity measure generated test "
            "capacity only; they do not establish scientific truth or useful coverage."
        ),
    )
    _write_json_atomic(output_dir / "scale-manifest.json", manifest.to_dict())
    return manifest


def _append_finding(
    findings: list[ScaleValidationFinding],
    finding: ScaleValidationFinding,
    *,
    max_findings: int,
) -> None:
    if len(findings) < max_findings:
        findings.append(finding)


def _iter_gzip_lines(path: Path) -> Iterator[tuple[int, bytes]]:
    with gzip.open(path, "rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if raw.strip():
                yield line_number, raw


def validate_scale_corpus(
    output_dir: Path,
    *,
    axes: CorpusAxes | None = None,
    max_findings: int = 100,
) -> ScaleValidationReport:
    """Validate scale corpus integrity in streaming O(1)-record memory."""

    if max_findings <= 0:
        raise ValueError("max_findings must be positive")
    axes = axes or default_axes()
    manifest_path = output_dir / "scale-manifest.json"
    if not manifest_path.exists():
        finding = ScaleValidationFinding(
            "MISSING_SCALE_MANIFEST",
            "P0",
            "scale-manifest.json is required",
            str(manifest_path),
        )
        return ScaleValidationReport(
            schema="omega_naruto_frontier.scale_validation.v2",
            valid=False,
            manifest_records=0,
            observed_records=0,
            observed_shards=0,
            expected_next_ordinal=0,
            observed_next_ordinal=0,
            compressed_bytes=0,
            uncompressed_bytes=0,
            logical_corpus_sha256=sha256(b"").hexdigest(),
            merkle_root_sha256=sha256(b"").hexdigest(),
            findings=(finding,),
            non_claim="Integrity validation does not establish scientific truth.",
        )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = ScaleManifest(
        **{key: value for key, value in payload.items() if key != "shards"},
        shards=tuple(ScaleShardReceipt(**item) for item in payload.get("shards", [])),
    )
    findings: list[ScaleValidationFinding] = []
    observed_records = 0
    observed_shards = 0
    compressed_bytes = 0
    uncompressed_bytes = 0
    expected_ordinal = manifest.start_ordinal
    corpus_digest = sha256()
    merkle_digest = sha256()

    for receipt in sorted(manifest.shards, key=lambda item: item.partition_id):
        path = output_dir / receipt.path
        if not path.exists():
            _append_finding(
                findings,
                ScaleValidationFinding("MISSING_SCALE_SHARD", "P0", "declared shard is missing", str(path)),
                max_findings=max_findings,
            )
            continue
        observed_shards += 1
        encoded = path.read_bytes()
        compressed_bytes += len(encoded)
        observed_compressed_hash = sha256(encoded).hexdigest()
        if observed_compressed_hash != receipt.compressed_sha256:
            _append_finding(
                findings,
                ScaleValidationFinding(
                    "SCALE_COMPRESSED_HASH_MISMATCH",
                    "P0",
                    f"expected {receipt.compressed_sha256}, observed {observed_compressed_hash}",
                    str(path),
                ),
                max_findings=max_findings,
            )
        if len(encoded) != receipt.compressed_bytes:
            _append_finding(
                findings,
                ScaleValidationFinding(
                    "SCALE_COMPRESSED_BYTES_MISMATCH",
                    "P1",
                    f"expected {receipt.compressed_bytes}, observed {len(encoded)}",
                    str(path),
                ),
                max_findings=max_findings,
            )

        shard_digest = sha256()
        shard_count = 0
        try:
            for line_number, raw in _iter_gzip_lines(path):
                shard_count += 1
                observed_records += 1
                uncompressed_bytes += len(raw)
                shard_digest.update(raw)
                corpus_digest.update(raw)
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError as error:
                    _append_finding(
                        findings,
                        ScaleValidationFinding(
                            "SCALE_INVALID_JSON",
                            "P0",
                            str(error),
                            str(path),
                            line_number,
                        ),
                        max_findings=max_findings,
                    )
                    expected_ordinal += 1
                    continue

                ordinal = record.get("ordinal")
                if ordinal != expected_ordinal:
                    _append_finding(
                        findings,
                        ScaleValidationFinding(
                            "SCALE_ORDINAL_GAP",
                            "P0",
                            f"expected ordinal {expected_ordinal}, observed {ordinal}",
                            str(path),
                            line_number,
                        ),
                        max_findings=max_findings,
                    )
                expected_record = record_from_ordinal(expected_ordinal, axes)
                if record.get("record_id") != expected_record.record_id:
                    _append_finding(
                        findings,
                        ScaleValidationFinding(
                            "SCALE_RECORD_ID_MISMATCH",
                            "P0",
                            "record_id does not match deterministic ordinal projection",
                            str(path),
                            line_number,
                        ),
                        max_findings=max_findings,
                    )
                for field in (
                    "epoch",
                    "local_ordinal",
                    "operator",
                    "domain",
                    "epistemic_state",
                    "evidence_mode",
                    "perturbation",
                    "gate_profile",
                    "expected_oak_action",
                ):
                    if record.get(field) != getattr(expected_record, field):
                        _append_finding(
                            findings,
                            ScaleValidationFinding(
                                "SCALE_DETERMINISTIC_FIELD_MISMATCH",
                                "P0",
                                f"field {field} differs from deterministic projection",
                                str(path),
                                line_number,
                            ),
                            max_findings=max_findings,
                        )
                        break
                expected_ordinal += 1
        except (OSError, EOFError) as error:
            _append_finding(
                findings,
                ScaleValidationFinding("SCALE_GZIP_ERROR", "P0", str(error), str(path)),
                max_findings=max_findings,
            )
            continue

        shard_logical_hash = shard_digest.hexdigest()
        merkle_digest.update(bytes.fromhex(shard_logical_hash))
        if shard_logical_hash != receipt.logical_sha256:
            _append_finding(
                findings,
                ScaleValidationFinding(
                    "SCALE_LOGICAL_HASH_MISMATCH",
                    "P0",
                    f"expected {receipt.logical_sha256}, observed {shard_logical_hash}",
                    str(path),
                ),
                max_findings=max_findings,
            )
        if shard_count != receipt.record_count:
            _append_finding(
                findings,
                ScaleValidationFinding(
                    "SCALE_SHARD_COUNT_MISMATCH",
                    "P0",
                    f"expected {receipt.record_count}, observed {shard_count}",
                    str(path),
                ),
                max_findings=max_findings,
            )

    logical_hash = corpus_digest.hexdigest()
    merkle_root = merkle_digest.hexdigest()
    expected_next = manifest.start_ordinal + manifest.written_records
    if observed_records != manifest.written_records:
        _append_finding(
            findings,
            ScaleValidationFinding(
                "SCALE_MANIFEST_COUNT_MISMATCH",
                "P0",
                f"expected {manifest.written_records}, observed {observed_records}",
            ),
            max_findings=max_findings,
        )
    if expected_ordinal != expected_next:
        _append_finding(
            findings,
            ScaleValidationFinding(
                "SCALE_NEXT_ORDINAL_MISMATCH",
                "P0",
                f"expected final ordinal {expected_next}, observed {expected_ordinal}",
            ),
            max_findings=max_findings,
        )
    if logical_hash != manifest.logical_corpus_sha256:
        _append_finding(
            findings,
            ScaleValidationFinding(
                "SCALE_CORPUS_HASH_MISMATCH",
                "P0",
                f"expected {manifest.logical_corpus_sha256}, observed {logical_hash}",
            ),
            max_findings=max_findings,
        )
    if merkle_root != manifest.merkle_root_sha256:
        _append_finding(
            findings,
            ScaleValidationFinding(
                "SCALE_MERKLE_ROOT_MISMATCH",
                "P0",
                f"expected {manifest.merkle_root_sha256}, observed {merkle_root}",
            ),
            max_findings=max_findings,
        )
    if compressed_bytes != manifest.compressed_bytes:
        _append_finding(
            findings,
            ScaleValidationFinding(
                "SCALE_TOTAL_COMPRESSED_BYTES_MISMATCH",
                "P1",
                f"expected {manifest.compressed_bytes}, observed {compressed_bytes}",
            ),
            max_findings=max_findings,
        )
    if uncompressed_bytes != manifest.uncompressed_bytes:
        _append_finding(
            findings,
            ScaleValidationFinding(
                "SCALE_TOTAL_UNCOMPRESSED_BYTES_MISMATCH",
                "P1",
                f"expected {manifest.uncompressed_bytes}, observed {uncompressed_bytes}",
            ),
            max_findings=max_findings,
        )

    return ScaleValidationReport(
        schema="omega_naruto_frontier.scale_validation.v2",
        valid=not any(item.severity == "P0" for item in findings),
        manifest_records=manifest.written_records,
        observed_records=observed_records,
        observed_shards=observed_shards,
        expected_next_ordinal=expected_next,
        observed_next_ordinal=expected_ordinal,
        compressed_bytes=compressed_bytes,
        uncompressed_bytes=uncompressed_bytes,
        logical_corpus_sha256=logical_hash,
        merkle_root_sha256=merkle_root,
        findings=tuple(findings),
        non_claim="Integrity validation does not establish scientific truth or useful coverage.",
    )
