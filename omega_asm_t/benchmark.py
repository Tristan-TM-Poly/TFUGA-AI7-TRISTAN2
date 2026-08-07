from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import os
import platform
import statistics
import sys
from typing import Iterable


@dataclass(frozen=True)
class BenchmarkStats:
    """Distribution summary for observational timing samples.

    Timing is evidence about one execution context, not a universal performance
    claim.  The robust median/MAD pair is kept alongside mean/stdev so noisy
    runners do not silently look more precise than they are.
    """

    count: int
    minimum: float
    median: float
    mean: float
    maximum: float
    stdev: float
    mad: float
    p05: float
    p95: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _percentile(sorted_values: list[float], probability: float) -> float:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    if not sorted_values:
        raise ValueError("at least one sample is required")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = probability * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def summarize_samples(samples: Iterable[float]) -> BenchmarkStats:
    values = [float(value) for value in samples]
    if not values:
        raise ValueError("at least one timing sample is required")
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("timing samples must be finite and non-negative")

    ordered = sorted(values)
    median = statistics.median(ordered)
    absolute_deviations = [abs(value - median) for value in ordered]
    return BenchmarkStats(
        count=len(ordered),
        minimum=ordered[0],
        median=median,
        mean=statistics.fmean(ordered),
        maximum=ordered[-1],
        stdev=statistics.stdev(ordered) if len(ordered) > 1 else 0.0,
        mad=statistics.median(absolute_deviations),
        p05=_percentile(ordered, 0.05),
        p95=_percentile(ordered, 0.95),
    )


def relative_ratio(numerator: BenchmarkStats, denominator: BenchmarkStats) -> float | None:
    """Return median(numerator)/median(denominator), if well-defined."""

    if denominator.median <= 0.0:
        return None
    return numerator.median / denominator.median


def _linux_cpu_model() -> str | None:
    path = "/proc/cpuinfo"
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                key, separator, value = line.partition(":")
                if separator and key.strip().lower() in {"model name", "hardware", "processor"}:
                    cleaned = value.strip()
                    if cleaned:
                        return cleaned
    except OSError:
        return None
    return None


def machine_manifest() -> dict[str, object]:
    """Collect a conservative, dependency-free execution-context manifest."""

    return {
        "architecture": platform.machine() or "unknown",
        "cpu_model": _linux_cpu_model() or platform.processor() or "unknown",
        "logical_cpus": os.cpu_count(),
        "operating_system": platform.system() or "unknown",
        "os_release": platform.release() or "unknown",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "byteorder": sys.byteorder,
        "timing_claim_scope": "observational_on_this_execution_context_only",
    }
