"""Parallel validation and indexing for Ω-NARUTO frontier scale corpora.

The v2 validator intentionally validates a single logical stream. This module
adds a shard-parallel proof path for larger finite experiments. Every record is
recomputed from its global ordinal. Each shard's compressed and logical hashes
are verified independently, then the manifest Merkle root is rebuilt in shard
order.

SHA-256 of one concatenated logical stream is not composable from independent
worker digests. The parallel report therefore states explicitly that the global
stream hash was not recomputed. The per-shard logical hashes and Merkle root are
fully recomputed. This distinction is an OAK invariant, not an implementation
footnote.
"""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from hashlib import sha256
import gzip
import json
from pathlib import Path
from time import monotonic
from typing import Iterable, Sequence
import zlib

from .frontier import CorpusAxes, default_axes, record_from_ordinal
from .frontier_scale import ScaleShardReceipt


@dataclass(frozen=True)
class ParallelFinding:
    code: str
    severity: str
    message: str
    path: str | None = None
    line_number: int | None = None
    partition_id: int | None = None


@dataclass(frozen=True)
class ShardValidationProof:
    partition_id: int
    path: str
    first_ordinal: int
    last_ordinal: int
    observed_records: int
    observed_next_ordinal: int
    compressed_bytes: int
    uncompressed_bytes: int
    compressed_sha256: str
    logical_sha256: str
    valid: bool
    findings: tuple[ParallelFinding, ...]


@dataclass(frozen=True)
class ParallelValidationReport:
    schema: str
    valid: bool
    workers: int
    manifest_records: int
    observed_records: int
    manifest_shards: int
    observed_shards: int
    start_ordinal: int
    expected_next_ordinal: int
    observed_next_ordinal: int
    compressed_bytes: int
    uncompressed_bytes: int
    merkle_root_sha256: str
    manifest_merkle_root_sha256: str
    all_record_fields_recomputed: bool
    global_stream_sha256_recomputed: bool
    manifest_logical_corpus_sha256: str
    elapsed_seconds: float
    records_per_second: float
    findings: tuple[ParallelFinding, ...]
    shard_proofs: tuple[ShardValidationProof, ...]
    non_claim: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["findings"] = [asdict(item) for item in self.findings]
        payload["shard_proofs"] = [asdict(item) for item in self.shard_proofs]
        return payload


@dataclass(frozen=True)
class ShardIndexPartial:
    partition_id: int
    indexed_records: int
    counts_by_epoch: dict[str, int]
    counts_by_operator: dict[str, int]
    counts_by_domain: dict[str, int]
    counts_by_epistemic_state: dict[str, int]
    counts_by_evidence_mode: dict[str, int]
    counts_by_perturbation: dict[str, int]
    counts_by_gate_profile: dict[str, int]
    counts_by_oak_action: dict[str, int]
    mminus_records: int
    blocked_records: int
    human_review_records: int
    locally_ranked_records: int
    covered_local_ordinals: bytes


@dataclass(frozen=True)
class ParallelScaleIndex:
    schema: str
    workers: int
    indexed_records: int
    indexed_shards: int
    start_ordinal: int
    next_ordinal: int
    axis_cardinality: int
    covered_local_combinations: int
    local_coverage_fraction: float
    completed_epochs: int
    partial_epoch_records: int
    repeated_axis_realizations: int
    counts_by_epoch: dict[str, int]
    counts_by_operator: dict[str, int]
    counts_by_domain: dict[str, int]
    counts_by_epistemic_state: dict[str, int]
    counts_by_evidence_mode: dict[str, int]
    counts_by_perturbation: dict[str, int]
    counts_by_gate_profile: dict[str, int]
    counts_by_oak_action: dict[str, int]
    mminus_records: int
    blocked_records: int
    human_review_records: int
    locally_ranked_records: int
    mminus_fraction: float
    blocked_fraction: float
    elapsed_seconds: float
    records_per_second: float
    samples: tuple[dict[str, object], ...]
    non_claim: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["samples"] = list(self.samples)
        return payload


def _load_manifest(output_dir: Path) -> dict[str, object]:
    path = output_dir / "scale-manifest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("shards"), list):
        raise ValueError("manifest shards must be a list")
    return payload


def _ordered(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _limited_append(
    findings: list[ParallelFinding],
    finding: ParallelFinding,
    *,
    limit: int,
) -> None:
    if len(findings) < limit:
        findings.append(finding)


def _validate_shard_job(
    output_dir_text: str,
    receipt_payload: dict[str, object],
    axes: CorpusAxes,
    max_findings: int,
) -> ShardValidationProof:
    receipt = ScaleShardReceipt(**receipt_payload)
    output_dir = Path(output_dir_text)
    path = output_dir / receipt.path
    findings: list[ParallelFinding] = []
    if not path.exists():
        finding = ParallelFinding(
            "PARALLEL_MISSING_SHARD",
            "P0",
            "declared shard is missing",
            str(path),
            partition_id=receipt.partition_id,
        )
        return ShardValidationProof(
            receipt.partition_id,
            receipt.path,
            receipt.first_ordinal,
            receipt.last_ordinal,
            0,
            receipt.first_ordinal,
            0,
            0,
            sha256(b"").hexdigest(),
            sha256(b"").hexdigest(),
            False,
            (finding,),
        )

    encoded = path.read_bytes()
    compressed_hash = sha256(encoded).hexdigest()
    if compressed_hash != receipt.compressed_sha256:
        _limited_append(
            findings,
            ParallelFinding(
                "PARALLEL_COMPRESSED_HASH_MISMATCH",
                "P0",
                f"expected {receipt.compressed_sha256}, observed {compressed_hash}",
                str(path),
                partition_id=receipt.partition_id,
            ),
            limit=max_findings,
        )
    if len(encoded) != receipt.compressed_bytes:
        _limited_append(
            findings,
            ParallelFinding(
                "PARALLEL_COMPRESSED_BYTES_MISMATCH",
                "P1",
                f"expected {receipt.compressed_bytes}, observed {len(encoded)}",
                str(path),
                partition_id=receipt.partition_id,
            ),
            limit=max_findings,
        )

    logical_digest = sha256()
    observed_records = 0
    uncompressed_bytes = 0
    expected_ordinal = receipt.first_ordinal
    try:
        with gzip.open(path, "rb") as handle:
            for line_number, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                observed_records += 1
                uncompressed_bytes += len(raw)
                logical_digest.update(raw)
                try:
                    record = json.loads(raw)
                except (json.JSONDecodeError, UnicodeDecodeError) as error:
                    _limited_append(
                        findings,
                        ParallelFinding(
                            "PARALLEL_INVALID_JSON",
                            "P0",
                            str(error),
                            str(path),
                            line_number,
                            receipt.partition_id,
                        ),
                        limit=max_findings,
                    )
                    expected_ordinal += 1
                    continue

                if record.get("ordinal") != expected_ordinal:
                    _limited_append(
                        findings,
                        ParallelFinding(
                            "PARALLEL_ORDINAL_MISMATCH",
                            "P0",
                            f"expected {expected_ordinal}, observed {record.get('ordinal')}",
                            str(path),
                            line_number,
                            receipt.partition_id,
                        ),
                        limit=max_findings,
                    )
                expected = record_from_ordinal(expected_ordinal, axes)
                for field in (
                    "ordinal",
                    "epoch",
                    "local_ordinal",
                    "record_id",
                    "operator",
                    "domain",
                    "epistemic_state",
                    "evidence_mode",
                    "perturbation",
                    "gate_profile",
                    "hypothesis",
                    "expected_oak_action",
                    "non_claim",
                ):
                    if record.get(field) != getattr(expected, field):
                        _limited_append(
                            findings,
                            ParallelFinding(
                                "PARALLEL_DETERMINISTIC_FIELD_MISMATCH",
                                "P0",
                                f"field {field} differs from deterministic projection",
                                str(path),
                                line_number,
                                receipt.partition_id,
                            ),
                            limit=max_findings,
                        )
                        break
                expected_ordinal += 1
    except (OSError, EOFError, UnicodeDecodeError, zlib.error) as error:
        _limited_append(
            findings,
            ParallelFinding(
                "PARALLEL_GZIP_ERROR",
                "P0",
                str(error),
                str(path),
                partition_id=receipt.partition_id,
            ),
            limit=max_findings,
        )

    logical_hash = logical_digest.hexdigest()
    if logical_hash != receipt.logical_sha256:
        _limited_append(
            findings,
            ParallelFinding(
                "PARALLEL_LOGICAL_HASH_MISMATCH",
                "P0",
                f"expected {receipt.logical_sha256}, observed {logical_hash}",
                str(path),
                partition_id=receipt.partition_id,
            ),
            limit=max_findings,
        )
    if observed_records != receipt.record_count:
        _limited_append(
            findings,
            ParallelFinding(
                "PARALLEL_SHARD_RECORD_COUNT_MISMATCH",
                "P0",
                f"expected {receipt.record_count}, observed {observed_records}",
                str(path),
                partition_id=receipt.partition_id,
            ),
            limit=max_findings,
        )
    if uncompressed_bytes != receipt.uncompressed_bytes:
        _limited_append(
            findings,
            ParallelFinding(
                "PARALLEL_UNCOMPRESSED_BYTES_MISMATCH",
                "P1",
                f"expected {receipt.uncompressed_bytes}, observed {uncompressed_bytes}",
                str(path),
                partition_id=receipt.partition_id,
            ),
            limit=max_findings,
        )
    if expected_ordinal != receipt.last_ordinal + 1:
        _limited_append(
            findings,
            ParallelFinding(
                "PARALLEL_SHARD_NEXT_ORDINAL_MISMATCH",
                "P0",
                f"expected {receipt.last_ordinal + 1}, observed {expected_ordinal}",
                str(path),
                partition_id=receipt.partition_id,
            ),
            limit=max_findings,
        )

    return ShardValidationProof(
        partition_id=receipt.partition_id,
        path=receipt.path,
        first_ordinal=receipt.first_ordinal,
        last_ordinal=receipt.last_ordinal,
        observed_records=observed_records,
        observed_next_ordinal=expected_ordinal,
        compressed_bytes=len(encoded),
        uncompressed_bytes=uncompressed_bytes,
        compressed_sha256=compressed_hash,
        logical_sha256=logical_hash,
        valid=not any(item.severity == "P0" for item in findings),
        findings=tuple(findings),
    )


def validate_scale_corpus_parallel(
    output_dir: Path,
    *,
    workers: int = 4,
    axes: CorpusAxes | None = None,
    max_findings: int = 200,
) -> ParallelValidationReport:
    """Validate every shard and record in parallel, then verify the Merkle root."""

    if workers <= 0:
        raise ValueError("workers must be positive")
    if max_findings <= 0:
        raise ValueError("max_findings must be positive")
    axes = axes or default_axes()
    manifest = _load_manifest(output_dir)
    receipts = sorted(
        (dict(item) for item in manifest["shards"]),
        key=lambda item: int(item["partition_id"]),
    )
    started = monotonic()
    per_shard_limit = max(1, max_findings // max(1, len(receipts)))
    if workers == 1 or len(receipts) <= 1:
        proofs = [
            _validate_shard_job(str(output_dir), item, axes, per_shard_limit)
            for item in receipts
        ]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            proofs = list(
                executor.map(
                    _validate_shard_job,
                    [str(output_dir)] * len(receipts),
                    receipts,
                    [axes] * len(receipts),
                    [per_shard_limit] * len(receipts),
                )
            )
    proofs.sort(key=lambda item: item.partition_id)

    findings: list[ParallelFinding] = []
    expected_first = int(manifest.get("start_ordinal", 0))
    merkle_digest = sha256()
    for expected_partition, proof in enumerate(proofs):
        if proof.partition_id != expected_partition:
            _limited_append(
                findings,
                ParallelFinding(
                    "PARALLEL_PARTITION_SEQUENCE_MISMATCH",
                    "P0",
                    f"expected partition {expected_partition}, observed {proof.partition_id}",
                    proof.path,
                    partition_id=proof.partition_id,
                ),
                limit=max_findings,
            )
        if proof.first_ordinal != expected_first:
            _limited_append(
                findings,
                ParallelFinding(
                    "PARALLEL_SHARD_RANGE_GAP",
                    "P0",
                    f"expected first ordinal {expected_first}, observed {proof.first_ordinal}",
                    proof.path,
                    partition_id=proof.partition_id,
                ),
                limit=max_findings,
            )
        expected_first = proof.last_ordinal + 1
        try:
            merkle_digest.update(bytes.fromhex(proof.logical_sha256))
        except ValueError:
            _limited_append(
                findings,
                ParallelFinding(
                    "PARALLEL_INVALID_LOGICAL_HASH",
                    "P0",
                    "logical shard hash is not valid hexadecimal SHA-256",
                    proof.path,
                    partition_id=proof.partition_id,
                ),
                limit=max_findings,
            )
        for finding in proof.findings:
            _limited_append(findings, finding, limit=max_findings)

    observed_records = sum(item.observed_records for item in proofs)
    compressed_bytes = sum(item.compressed_bytes for item in proofs)
    uncompressed_bytes = sum(item.uncompressed_bytes for item in proofs)
    manifest_records = int(manifest.get("written_records", 0))
    expected_next = int(manifest.get("next_ordinal", 0))
    observed_next = expected_first
    merkle_root = merkle_digest.hexdigest()
    manifest_merkle = str(manifest.get("merkle_root_sha256", ""))

    checks = (
        (
            observed_records == manifest_records,
            "PARALLEL_TOTAL_RECORD_COUNT_MISMATCH",
            f"expected {manifest_records}, observed {observed_records}",
        ),
        (
            len(proofs) == int(manifest.get("shard_count", 0)),
            "PARALLEL_TOTAL_SHARD_COUNT_MISMATCH",
            f"expected {manifest.get('shard_count')}, observed {len(proofs)}",
        ),
        (
            observed_next == expected_next,
            "PARALLEL_FINAL_ORDINAL_MISMATCH",
            f"expected {expected_next}, observed {observed_next}",
        ),
        (
            compressed_bytes == int(manifest.get("compressed_bytes", 0)),
            "PARALLEL_TOTAL_COMPRESSED_BYTES_MISMATCH",
            f"expected {manifest.get('compressed_bytes')}, observed {compressed_bytes}",
        ),
        (
            uncompressed_bytes == int(manifest.get("uncompressed_bytes", 0)),
            "PARALLEL_TOTAL_UNCOMPRESSED_BYTES_MISMATCH",
            f"expected {manifest.get('uncompressed_bytes')}, observed {uncompressed_bytes}",
        ),
        (
            merkle_root == manifest_merkle,
            "PARALLEL_MERKLE_ROOT_MISMATCH",
            f"expected {manifest_merkle}, observed {merkle_root}",
        ),
    )
    for passed, code, message in checks:
        if not passed:
            _limited_append(
                findings,
                ParallelFinding(code, "P0", message),
                limit=max_findings,
            )

    elapsed = monotonic() - started
    return ParallelValidationReport(
        schema="omega_naruto_frontier.parallel_validation.v3",
        valid=not any(item.severity == "P0" for item in findings),
        workers=workers,
        manifest_records=manifest_records,
        observed_records=observed_records,
        manifest_shards=int(manifest.get("shard_count", 0)),
        observed_shards=len(proofs),
        start_ordinal=int(manifest.get("start_ordinal", 0)),
        expected_next_ordinal=expected_next,
        observed_next_ordinal=observed_next,
        compressed_bytes=compressed_bytes,
        uncompressed_bytes=uncompressed_bytes,
        merkle_root_sha256=merkle_root,
        manifest_merkle_root_sha256=manifest_merkle,
        all_record_fields_recomputed=True,
        global_stream_sha256_recomputed=False,
        manifest_logical_corpus_sha256=str(manifest.get("logical_corpus_sha256", "")),
        elapsed_seconds=round(elapsed, 6),
        records_per_second=round(observed_records / elapsed, 3) if elapsed else 0.0,
        findings=tuple(findings),
        shard_proofs=tuple(proofs),
        non_claim=(
            "Parallel validation proves tested shard integrity and deterministic "
            "record projection. It does not establish scientific truth or useful novelty."
        ),
    )


def _index_shard_job(
    output_dir_text: str,
    receipt_payload: dict[str, object],
    cardinality: int,
) -> ShardIndexPartial:
    receipt = ScaleShardReceipt(**receipt_payload)
    output_dir = Path(output_dir_text)
    counters = [Counter() for _ in range(8)]
    covered = bytearray(cardinality)
    indexed = 0
    mminus = blocked = human_review = locally_ranked = 0
    with gzip.open(output_dir / receipt.path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            indexed += 1
            values = (
                str(record["epoch"]),
                str(record["operator"]),
                str(record["domain"]),
                str(record["epistemic_state"]),
                str(record["evidence_mode"]),
                str(record["perturbation"]),
                str(record["gate_profile"]),
                str(record["expected_oak_action"]),
            )
            for counter, value in zip(counters, values):
                counter[value] += 1
            covered[int(record["local_ordinal"])] = 1
            action = values[-1]
            if "MMINUS" in action:
                mminus += 1
            if action.startswith("BLOCK_"):
                blocked += 1
            if "HUMAN_REVIEW" in action:
                human_review += 1
            if action == "RANK_LOCALLY_WITHOUT_CERTIFICATION":
                locally_ranked += 1
    ordered = [_ordered(counter) for counter in counters]
    return ShardIndexPartial(
        partition_id=receipt.partition_id,
        indexed_records=indexed,
        counts_by_epoch=ordered[0],
        counts_by_operator=ordered[1],
        counts_by_domain=ordered[2],
        counts_by_epistemic_state=ordered[3],
        counts_by_evidence_mode=ordered[4],
        counts_by_perturbation=ordered[5],
        counts_by_gate_profile=ordered[6],
        counts_by_oak_action=ordered[7],
        mminus_records=mminus,
        blocked_records=blocked,
        human_review_records=human_review,
        locally_ranked_records=locally_ranked,
        covered_local_ordinals=bytes(covered),
    )


def _merge_counter_dicts(partials: Iterable[dict[str, int]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for partial in partials:
        counter.update(partial)
    return _ordered(counter)


def build_scale_index_parallel(
    output_dir: Path,
    *,
    workers: int = 4,
    sample_limit: int = 128,
    axes: CorpusAxes | None = None,
) -> ParallelScaleIndex:
    """Build an exact aggregate index using independent shard workers."""

    if workers <= 0:
        raise ValueError("workers must be positive")
    if sample_limit < 0:
        raise ValueError("sample_limit must be non-negative")
    axes = axes or default_axes()
    manifest = _load_manifest(output_dir)
    receipts = sorted(
        (dict(item) for item in manifest["shards"]),
        key=lambda item: int(item["partition_id"]),
    )
    started = monotonic()
    if workers == 1 or len(receipts) <= 1:
        partials = [
            _index_shard_job(str(output_dir), item, axes.cardinality)
            for item in receipts
        ]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            partials = list(
                executor.map(
                    _index_shard_job,
                    [str(output_dir)] * len(receipts),
                    receipts,
                    [axes.cardinality] * len(receipts),
                )
            )
    partials.sort(key=lambda item: item.partition_id)

    coverage = bytearray(axes.cardinality)
    for partial in partials:
        for index, value in enumerate(partial.covered_local_ordinals):
            if value:
                coverage[index] = 1
    indexed = sum(item.indexed_records for item in partials)
    start = int(manifest.get("start_ordinal", 0))
    next_ordinal = int(manifest.get("next_ordinal", start + indexed))
    coverage_count = sum(coverage)

    samples: list[dict[str, object]] = []
    if sample_limit and indexed:
        stride = max(1, indexed // sample_limit)
        for offset in range(0, indexed, stride):
            if len(samples) >= sample_limit:
                break
            record = record_from_ordinal(start + offset, axes)
            samples.append(
                {
                    "ordinal": record.ordinal,
                    "record_id": record.record_id,
                    "epoch": record.epoch,
                    "operator": record.operator,
                    "domain": record.domain,
                    "expected_oak_action": record.expected_oak_action,
                }
            )

    elapsed = monotonic() - started
    mminus = sum(item.mminus_records for item in partials)
    blocked = sum(item.blocked_records for item in partials)
    human_review = sum(item.human_review_records for item in partials)
    locally_ranked = sum(item.locally_ranked_records for item in partials)
    return ParallelScaleIndex(
        schema="omega_naruto_frontier.parallel_index.v3",
        workers=workers,
        indexed_records=indexed,
        indexed_shards=len(partials),
        start_ordinal=start,
        next_ordinal=next_ordinal,
        axis_cardinality=axes.cardinality,
        covered_local_combinations=coverage_count,
        local_coverage_fraction=(coverage_count / axes.cardinality if axes.cardinality else 0.0),
        completed_epochs=next_ordinal // axes.cardinality,
        partial_epoch_records=next_ordinal % axes.cardinality,
        repeated_axis_realizations=max(0, indexed - coverage_count),
        counts_by_epoch=_merge_counter_dicts(item.counts_by_epoch for item in partials),
        counts_by_operator=_merge_counter_dicts(item.counts_by_operator for item in partials),
        counts_by_domain=_merge_counter_dicts(item.counts_by_domain for item in partials),
        counts_by_epistemic_state=_merge_counter_dicts(
            item.counts_by_epistemic_state for item in partials
        ),
        counts_by_evidence_mode=_merge_counter_dicts(
            item.counts_by_evidence_mode for item in partials
        ),
        counts_by_perturbation=_merge_counter_dicts(
            item.counts_by_perturbation for item in partials
        ),
        counts_by_gate_profile=_merge_counter_dicts(
            item.counts_by_gate_profile for item in partials
        ),
        counts_by_oak_action=_merge_counter_dicts(
            item.counts_by_oak_action for item in partials
        ),
        mminus_records=mminus,
        blocked_records=blocked,
        human_review_records=human_review,
        locally_ranked_records=locally_ranked,
        mminus_fraction=(mminus / indexed if indexed else 0.0),
        blocked_fraction=(blocked / indexed if indexed else 0.0),
        elapsed_seconds=round(elapsed, 6),
        records_per_second=round(indexed / elapsed, 3) if elapsed else 0.0,
        samples=tuple(samples),
        non_claim=(
            "Parallel index counts describe generated fixtures and deterministic "
            "routing only; they do not measure truth, novelty, or market value."
        ),
    )


def write_parallel_validation(
    output_dir: Path,
    *,
    destination: Path,
    workers: int = 4,
) -> ParallelValidationReport:
    report = validate_scale_corpus_parallel(output_dir, workers=workers)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def write_parallel_index(
    output_dir: Path,
    *,
    destination: Path,
    workers: int = 4,
    sample_limit: int = 128,
) -> ParallelScaleIndex:
    index = build_scale_index_parallel(
        output_dir,
        workers=workers,
        sample_limit=sample_limit,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(index.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return index
