from __future__ import annotations

from pathlib import Path

from omega_millennium_t.r10.benchmark import benchmark_scaling
from omega_millennium_t.r10.model import RuntimePolicy


def test_finite_benchmark_separates_structure_from_measurements(tmp_path: Path) -> None:
    result = benchmark_scaling(
        tmp_path / "benchmark",
        sizes=[500, 1500],
        policy=RuntimePolicy(batch_size=100, shard_target_bytes=16_384),
    )
    assert result["sizes"] == [500, 1500]
    assert len(result["structural_digest"]) == 64
    assert result["measurement_values_are_environment_dependent"] is True
    assert result["finite_benchmark_only"] is True
    assert result["bounded_memory_proven"] is False
    assert result["unlimited_capacity_claimed"] is False
    assert result["permanent_total_cell_cap"] is None
    assert all(run["complete"] is True for run in result["runs"])
    assert all(run["peak_python_bytes"] > 0 for run in result["runs"])
    assert all(run["elapsed_seconds"] >= 0 for run in result["runs"])
