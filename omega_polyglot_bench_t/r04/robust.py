"""Repeated autotuning with robust aggregation across independent trials."""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .autotune import autotune, hardware_fingerprint


def _mad(values: list[int], center: float) -> float:
    return float(statistics.median(abs(value - center) for value in values)) if values else 0.0


def robust_autotune(
    *,
    trials: int = 5,
    sizes: tuple[int, ...] = (4096, 100_000, 1_000_000),
    backends: tuple[str, ...] = ("c", "cpp", "rust"),
    profiles: tuple[str, ...] = ("portable", "native", "openmp"),
    algorithms: tuple[str, ...] = ("affine", "affine_chain", "sum", "dot"),
    warmups: int = 3,
    repetitions: int = 15,
    tolerance: float = 1e-12,
    seed: int = 1729,
) -> dict[str, Any]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    reports = [
        autotune(
            sizes=sizes,
            backends=backends,
            profiles=profiles,
            algorithms=algorithms,
            warmups=warmups,
            repetitions=repetitions,
            tolerance=tolerance,
            seed=seed + trial * 1_000_003,
        )
        for trial in range(trials)
    ]
    grouped: dict[tuple[str, int, str], list[Any]] = defaultdict(list)
    for report in reports:
        for item in report.measurements:
            grouped[(item.algorithm, item.size, item.candidate_id)].append(item)

    aggregates: list[dict[str, Any]] = []
    for (algorithm, size, candidate_id), items in sorted(grouped.items()):
        correct_items = [item for item in items if item.correct and item.median_ns is not None]
        medians = [int(item.median_ns) for item in correct_items]
        robust_median = float(statistics.median(medians)) if medians else None
        speedups = [float(item.speedup_vs_python) for item in correct_items if item.speedup_vs_python is not None]
        aggregates.append({
            "algorithm": algorithm,
            "size": size,
            "candidate_id": candidate_id,
            "trials_observed": len(items),
            "trials_correct": len(correct_items),
            "success_rate": len(correct_items) / trials,
            "median_of_medians_ns": robust_median,
            "mad_ns": _mad(medians, robust_median or 0.0),
            "min_ns": min(medians) if medians else None,
            "max_ns": max(medians) if medians else None,
            "median_speedup_vs_python": float(statistics.median(speedups)) if speedups else None,
            "max_abs_error": max((float(item.max_abs_error or 0.0) for item in correct_items), default=None),
        })

    champions: list[dict[str, Any]] = []
    for algorithm in algorithms:
        for size in sizes:
            eligible = [
                item
                for item in aggregates
                if item["algorithm"] == algorithm
                and item["size"] == size
                and item["success_rate"] == 1.0
                and item["median_of_medians_ns"] is not None
            ]
            if eligible:
                champions.append(dict(min(eligible, key=lambda item: (item["median_of_medians_ns"], item["candidate_id"]))))

    return {
        "schema_version": "omega-polyglot-robust-v4",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "hardware": hardware_fingerprint(),
        "protocol": {
            "trials": trials,
            "sizes": list(sizes),
            "backends": list(backends),
            "profiles": list(profiles),
            "algorithms": list(algorithms),
            "warmups": warmups,
            "repetitions_per_trial": repetitions,
            "tolerance": tolerance,
            "seed_base": seed,
            "selection": "minimum median-of-medians among candidates correct in every trial",
        },
        "aggregates": aggregates,
        "champions": champions,
        "claims": {
            "universal_language_winner": False,
            "scientific_validation": False,
            "energy_measured": False,
        },
        "status": "OAK_REPEATED_SOFTWARE_AUTOTUNE_ONLY",
    }


def save_robust_report(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
