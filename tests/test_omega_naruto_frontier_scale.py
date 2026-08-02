import json
from pathlib import Path

import pytest

from omega_naruto_hmagfm.frontier import default_axes
from omega_naruto_hmagfm.frontier_index import build_scale_index
from omega_naruto_hmagfm.frontier_scale import (
    plan_scale_run,
    validate_scale_corpus,
    write_scale_corpus,
)
from omega_naruto_hmagfm.scale_cli import main as scale_main


def test_scale_plan_has_contiguous_partitions_and_no_fixed_total_cap() -> None:
    plan = plan_scale_run(
        target_records=1_000_003,
        shard_records=25_000,
        start_ordinal=7_000_000,
    )

    assert plan.target_records == 1_000_003
    assert plan.next_ordinal == 8_000_003
    assert len(plan.partitions) == 41
    assert plan.partitions[0].first_ordinal == 7_000_000
    assert plan.partitions[-1].record_count == 3
    for left, right in zip(plan.partitions, plan.partitions[1:]):
        assert left.last_ordinal + 1 == right.first_ordinal


def test_parallel_and_sequential_runs_have_identical_logical_content(tmp_path: Path) -> None:
    sequential_dir = tmp_path / "sequential"
    parallel_dir = tmp_path / "parallel"

    sequential = write_scale_corpus(
        sequential_dir,
        target_records=2_048,
        shard_records=256,
        workers=1,
    )
    parallel = write_scale_corpus(
        parallel_dir,
        target_records=2_048,
        shard_records=256,
        workers=2,
    )

    assert sequential.logical_corpus_sha256 == parallel.logical_corpus_sha256
    assert sequential.merkle_root_sha256 == parallel.merkle_root_sha256
    assert sequential.compressed_bytes == parallel.compressed_bytes
    assert [item.logical_sha256 for item in sequential.shards] == [
        item.logical_sha256 for item in parallel.shards
    ]
    assert [item.compressed_sha256 for item in sequential.shards] == [
        item.compressed_sha256 for item in parallel.shards
    ]
    assert validate_scale_corpus(sequential_dir).valid
    assert validate_scale_corpus(parallel_dir).valid


def test_scale_resume_reuses_every_valid_shard(tmp_path: Path) -> None:
    output = tmp_path / "resume"
    first = write_scale_corpus(
        output,
        target_records=900,
        shard_records=300,
        workers=1,
    )
    second = write_scale_corpus(
        output,
        target_records=900,
        shard_records=300,
        workers=2,
        resume=True,
    )

    assert first.logical_corpus_sha256 == second.logical_corpus_sha256
    assert second.resumed_shards == 3
    assert second.generated_shards == 0
    assert second.records_per_second > 0
    assert validate_scale_corpus(output).valid


def test_scale_run_crosses_epoch_boundary_and_indexes_both_epochs(tmp_path: Path) -> None:
    axes = default_axes()
    start = axes.cardinality - 10
    output = tmp_path / "epochs"
    manifest = write_scale_corpus(
        output,
        target_records=100,
        shard_records=25,
        start_ordinal=start,
        workers=2,
    )
    report = validate_scale_corpus(output)
    index = build_scale_index(output, sample_limit=8)

    assert manifest.completed_epochs_before == 0
    assert manifest.completed_epochs_after == 1
    assert manifest.partial_epoch_records_after == 90
    assert report.valid
    assert report.observed_records == 100
    assert index.indexed_records == 100
    assert index.counts_by_epoch == {"0": 10, "1": 90}
    assert index.covered_local_combinations == 100
    assert sum(index.counts_by_oak_action.values()) == 100
    assert len(index.samples) == 8


def test_scale_validation_detects_compressed_tampering(tmp_path: Path) -> None:
    output = tmp_path / "tampered"
    manifest = write_scale_corpus(
        output,
        target_records=200,
        shard_records=100,
        workers=1,
    )
    shard = output / manifest.shards[0].path
    encoded = bytearray(shard.read_bytes())
    encoded[len(encoded) // 2] ^= 0x01
    shard.write_bytes(bytes(encoded))

    report = validate_scale_corpus(output)
    codes = {finding.code for finding in report.findings}
    assert not report.valid
    assert "SCALE_COMPRESSED_HASH_MISMATCH" in codes
    assert "SCALE_GZIP_ERROR" in codes or "SCALE_LOGICAL_HASH_MISMATCH" in codes


def test_scale_config_rejects_incompatible_resume(tmp_path: Path) -> None:
    output = tmp_path / "config"
    write_scale_corpus(output, target_records=100, shard_records=50)

    with pytest.raises(ValueError, match="scale-config"):
        write_scale_corpus(output, target_records=101, shard_records=50)


def test_scale_cli_generates_validates_and_indexes(tmp_path: Path, capsys) -> None:
    output = tmp_path / "cli"
    validation_path = tmp_path / "validation.json"
    index_path = tmp_path / "index.json"

    assert scale_main(
        (
            "generate",
            "--output-dir",
            str(output),
            "--target",
            "512",
            "--shard-records",
            "128",
            "--workers",
            "2",
        )
    ) == 0
    generation = json.loads(capsys.readouterr().out)
    assert generation["written_records"] == 512

    assert scale_main(
        (
            "validate",
            "--output-dir",
            str(output),
            "--report",
            str(validation_path),
        )
    ) == 0
    validation = json.loads(capsys.readouterr().out)
    assert validation["valid"] is True
    assert json.loads(validation_path.read_text(encoding="utf-8")) == validation

    assert scale_main(
        (
            "index",
            "--output-dir",
            str(output),
            "--destination",
            str(index_path),
            "--sample-limit",
            "4",
        )
    ) == 0
    index = json.loads(capsys.readouterr().out)
    assert index["indexed_records"] == 512
    assert len(index["samples"]) == 4
    assert json.loads(index_path.read_text(encoding="utf-8")) == index
