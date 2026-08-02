import json
from pathlib import Path

from omega_naruto_hmagfm.frontier_index import build_scale_index
from omega_naruto_hmagfm.frontier_ledger import build_run_ledger
from omega_naruto_hmagfm.frontier_parallel import (
    build_scale_index_parallel,
    validate_scale_corpus_parallel,
)
from omega_naruto_hmagfm.frontier_scale import write_scale_corpus
from omega_naruto_hmagfm.scale_v3_cli import main


def make_run(
    root: Path,
    name: str,
    *,
    start: int,
    target: int,
    workers: int = 2,
) -> Path:
    output = root / name
    manifest = write_scale_corpus(
        output,
        start_ordinal=start,
        target_records=target,
        shard_records=100,
        workers=workers,
        compression_level=6,
    )
    assert manifest.complete
    return output


def test_parallel_validation_recomputes_every_record_and_merkle(tmp_path: Path) -> None:
    output = make_run(tmp_path, "parallel-valid", start=0, target=500)
    report = validate_scale_corpus_parallel(output, workers=2)

    assert report.valid
    assert report.observed_records == 500
    assert report.observed_shards == 5
    assert report.observed_next_ordinal == 500
    assert report.all_record_fields_recomputed is True
    assert report.global_stream_sha256_recomputed is False
    assert report.merkle_root_sha256 == report.manifest_merkle_root_sha256
    assert report.findings == ()
    assert all(item.valid for item in report.shard_proofs)


def test_parallel_index_matches_sequential_exact_counts(tmp_path: Path) -> None:
    output = make_run(tmp_path, "parallel-index", start=0, target=1_000)
    sequential = build_scale_index(output, sample_limit=16)
    parallel = build_scale_index_parallel(output, workers=2, sample_limit=16)

    assert parallel.indexed_records == sequential.indexed_records == 1_000
    assert parallel.indexed_shards == sequential.indexed_shards == 10
    assert parallel.counts_by_epoch == sequential.counts_by_epoch
    assert parallel.counts_by_operator == sequential.counts_by_operator
    assert parallel.counts_by_domain == sequential.counts_by_domain
    assert parallel.counts_by_oak_action == sequential.counts_by_oak_action
    assert parallel.mminus_records == sequential.mminus_records
    assert parallel.blocked_records == sequential.blocked_records
    assert parallel.human_review_records == sequential.human_review_records
    assert parallel.locally_ranked_records == sequential.locally_ranked_records
    assert parallel.covered_local_combinations == sequential.covered_local_combinations


def test_parallel_validation_converts_corruption_to_p0_finding(tmp_path: Path) -> None:
    output = make_run(tmp_path, "parallel-corrupt", start=0, target=200)
    manifest = json.loads((output / "scale-manifest.json").read_text(encoding="utf-8"))
    shard = output / manifest["shards"][0]["path"]
    encoded = bytearray(shard.read_bytes())
    encoded[len(encoded) // 2] ^= 0xFF
    shard.write_bytes(bytes(encoded))

    report = validate_scale_corpus_parallel(output, workers=2)

    assert not report.valid
    codes = {item.code for item in report.findings}
    assert "PARALLEL_COMPRESSED_HASH_MISMATCH" in codes
    assert codes.intersection(
        {
            "PARALLEL_GZIP_ERROR",
            "PARALLEL_LOGICAL_HASH_MISMATCH",
            "PARALLEL_MERKLE_ROOT_MISMATCH",
        }
    )


def test_ledger_federates_contiguous_runs_deterministically(tmp_path: Path) -> None:
    first = make_run(tmp_path, "run-a", start=0, target=300)
    second = make_run(tmp_path, "run-b", start=300, target=200)
    manifests = (first / "scale-manifest.json", second / "scale-manifest.json")

    ledger = build_run_ledger(reversed(manifests))
    repeated = build_run_ledger(manifests)

    assert ledger.valid
    assert ledger.contiguous
    assert ledger.run_count == 2
    assert ledger.total_records == 500
    assert ledger.first_ordinal == 0
    assert ledger.next_ordinal == 500
    assert ledger.federation_root_sha256 == repeated.federation_root_sha256
    assert [item.start_ordinal for item in ledger.runs] == [0, 300]


def test_ledger_blocks_gap_when_contiguity_is_required(tmp_path: Path) -> None:
    first = make_run(tmp_path, "run-gap-a", start=0, target=100)
    second = make_run(tmp_path, "run-gap-b", start=150, target=100)

    strict = build_run_ledger(
        (first / "scale-manifest.json", second / "scale-manifest.json")
    )
    permissive = build_run_ledger(
        (first / "scale-manifest.json", second / "scale-manifest.json"),
        require_contiguous=False,
    )

    assert not strict.valid
    assert not strict.contiguous
    assert "LEDGER_RANGE_GAP" in {item.code for item in strict.findings}
    assert permissive.valid
    assert not permissive.contiguous


def test_v3_cli_writes_parallel_reports_and_ledger(tmp_path: Path, capsys) -> None:
    output = make_run(tmp_path, "cli-run", start=0, target=200)
    validation_path = tmp_path / "parallel-validation.json"
    index_path = tmp_path / "parallel-index.json"
    ledger_path = tmp_path / "ledger.json"

    assert main(
        (
            "parallel-validate",
            "--output-dir",
            str(output),
            "--destination",
            str(validation_path),
            "--workers",
            "2",
        )
    ) == 0
    capsys.readouterr()
    assert main(
        (
            "parallel-index",
            "--output-dir",
            str(output),
            "--destination",
            str(index_path),
            "--workers",
            "2",
        )
    ) == 0
    capsys.readouterr()
    assert main(
        (
            "ledger",
            "--manifest",
            str(output / "scale-manifest.json"),
            "--destination",
            str(ledger_path),
        )
    ) == 0
    capsys.readouterr()

    assert json.loads(validation_path.read_text(encoding="utf-8"))["valid"] is True
    assert json.loads(index_path.read_text(encoding="utf-8"))["indexed_records"] == 200
    assert json.loads(ledger_path.read_text(encoding="utf-8"))["total_records"] == 200
