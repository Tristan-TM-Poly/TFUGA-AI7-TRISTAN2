import json
from pathlib import Path

import pytest

from omega_naruto_hmagfm.frontier import (
    CorpusAxes,
    FrontierBudget,
    decode_ordinal,
    default_axes,
    iter_records,
    record_from_ordinal,
    write_corpus,
)
from omega_naruto_hmagfm.frontier_validation import validate_frontier


def test_default_projection_exceeds_tens_of_thousands() -> None:
    axes = default_axes()
    assert axes.cardinality == 64_512
    assert axes.cardinality > 50_000


def test_mixed_radix_decode_covers_first_and_last_records() -> None:
    axes = default_axes()
    first = decode_ordinal(0, axes)
    last = decode_ordinal(axes.cardinality - 1, axes)
    assert first["operator"] == axes.operators[0]
    assert first["gate_profile"] == axes.gate_profiles[0]
    assert last["operator"] == axes.operators[-1]
    assert last["gate_profile"] == axes.gate_profiles[-1]


def test_record_ids_are_deterministic_and_unique_for_large_slice() -> None:
    axes = default_axes()
    records = tuple(iter_records(axes, start_ordinal=10_000, record_count=10_000))
    identifiers = [record.record_id for record in records]
    assert len(identifiers) == 10_000
    assert len(set(identifiers)) == 10_000
    assert record_from_ordinal(10_000, axes) == records[0]


def test_frontier_budget_has_no_permanent_total_cap() -> None:
    assert FrontierBudget(requested_records=10).resolve_target() == 10
    assert FrontierBudget(requested_records=100_000).resolve_target() == 100_000
    assert FrontierBudget(requested_records=1_000_000).resolve_target() == 1_000_000


def test_adaptive_target_doubles_previous_success_without_byte_pressure() -> None:
    budget = FrontierBudget(requested_records=None, minimum_experiment_records=25_000)
    assert budget.resolve_target(previous_success=None) == 25_000
    assert budget.resolve_target(previous_success=25_000) == 50_000
    assert budget.resolve_target(previous_success=50_000) == 100_000


def test_byte_budget_applies_backpressure_without_becoming_a_permanent_cap() -> None:
    budget = FrontierBudget(
        requested_records=None,
        available_bytes=5_120_000,
        estimated_bytes_per_record=512,
        minimum_experiment_records=25_000,
    )
    assert budget.resolve_target(previous_success=50_000) == 10_000


def test_axes_reject_empty_or_duplicate_dimensions() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        CorpusAxes((), ("d",), ("s",), ("e",), ("p",), ("g",))
    with pytest.raises(ValueError, match="duplicates"):
        CorpusAxes(("a", "a"), ("d",), ("s",), ("e",), ("p",), ("g",))


def test_sharded_generation_and_streaming_validation(tmp_path: Path) -> None:
    manifest = write_corpus(
        tmp_path,
        budget=FrontierBudget(requested_records=12_345),
        shard_records=5_000,
    )
    assert manifest.complete
    assert manifest.written_records == 12_345
    assert len(manifest.shards) == 3
    assert [item.record_count for item in manifest.shards] == [5_000, 5_000, 2_345]

    report = validate_frontier(tmp_path)
    assert report.valid
    assert report.observed_records == 12_345
    assert report.unique_record_ids == 12_345
    assert report.findings == ()


def test_validator_detects_tampered_shard(tmp_path: Path) -> None:
    manifest = write_corpus(
        tmp_path,
        budget=FrontierBudget(requested_records=100),
        shard_records=50,
    )
    first = tmp_path / manifest.shards[0].path
    lines = first.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    payload["record_id"] = "tampered"
    lines[0] = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    first.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = validate_frontier(tmp_path)
    codes = {item.code for item in report.findings}
    assert not report.valid
    assert "SHARD_HASH_MISMATCH" in codes
    assert "CORPUS_HASH_MISMATCH" in codes


def test_generation_target_is_bounded_by_current_axis_projection(tmp_path: Path) -> None:
    axes = default_axes()
    manifest = write_corpus(
        tmp_path,
        axes=axes,
        budget=FrontierBudget(requested_records=1_000_000),
        shard_records=20_000,
    )
    assert manifest.target_records == axes.cardinality
    assert manifest.written_records == 64_512
    assert manifest.complete
