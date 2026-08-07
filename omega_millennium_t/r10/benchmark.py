from __future__ import annotations

import shutil
import time
import tracemalloc
from pathlib import Path
from typing import Any, Sequence

from .compiler import materialize_synthetic_campaign
from .model import RuntimePolicy, stable_digest, write_json


def benchmark_scaling(
    output_dir: str | Path,
    *,
    sizes: Sequence[int],
    policy: RuntimePolicy | None = None,
) -> dict[str, Any]:
    if not sizes or any(size < 1 for size in sizes):
        raise ValueError("benchmark sizes must be positive")
    runtime = policy or RuntimePolicy()
    root = Path(output_dir)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for size in sizes:
        run_dir = root / f"cells-{size}"
        tracemalloc.start()
        started = time.perf_counter()
        report = materialize_synthetic_campaign(
            run_dir,
            cell_count=size,
            policy=runtime,
        )
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rows.append(
            {
                "cell_count": size,
                "complete": report["complete"],
                "manifest_digest": report["manifest_digest"],
                "database_bytes": report["database_bytes"],
                "peak_python_bytes": peak,
                "elapsed_seconds": elapsed,
                "peak_python_bytes_per_cell": peak / size,
                "finite_benchmark_only": True,
            }
        )

    peak_values = [row["peak_python_bytes"] for row in rows]
    observed_peak_ratio = max(peak_values) / min(peak_values) if len(peak_values) > 1 else 1.0
    structural_view = {
        "sizes": list(sizes),
        "manifest_digests": [row["manifest_digest"] for row in rows],
        "complete": [row["complete"] for row in rows],
        "batch_size": runtime.batch_size,
        "shard_target_bytes": runtime.shard_target_bytes,
        "permanent_total_cell_cap": None,
    }
    result = {
        "schema": "omega-problem-stream-benchmark/10",
        "sizes": list(sizes),
        "runs": rows,
        "observed_peak_ratio": observed_peak_ratio,
        "batch_size": runtime.batch_size,
        "shard_target_bytes": runtime.shard_target_bytes,
        "structural_digest": stable_digest(structural_view),
        "measurement_values_are_environment_dependent": True,
        "finite_benchmark_only": True,
        "bounded_memory_proven": False,
        "unlimited_capacity_claimed": False,
        "permanent_total_cell_cap": None,
    }
    write_json(root / "benchmark.json", result)
    return result
