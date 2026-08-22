"""Low-friction runtime/resource instrumentation for Ω-COMPUTE-PHYSICS-T∞.

R0.1 intentionally measures only resources available from the Python standard
library. ``peak_python_bytes`` is tracemalloc-observed Python allocation peak;
it is not total process RSS/VRAM. Future machine adapters can add perf, RAPL,
NVML, psutil, eBPF or cluster telemetry without changing the ResourceSample
contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import platform
import statistics
import time
import tracemalloc
from typing import Any, Callable, Mapping, Sequence

from .atlas import ResourceSample


@dataclass
class ProfileResult:
    """Aggregated result of repeated measurements."""

    sample: ResourceSample
    repetitions: tuple[Mapping[str, float], ...]
    output: Any

    @property
    def resources(self) -> Mapping[str, float]:
        return self.sample.resources


def machine_fingerprint() -> dict[str, Any]:
    """Return a dependency-free, provenance-oriented machine fingerprint."""

    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "logical_cpu_count": os.cpu_count(),
    }


def _percentile(values: Sequence[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


def _one_measurement(function: Callable[..., Any], args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> tuple[Any, dict[str, float]]:
    tracemalloc.start()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    try:
        output = function(*args, **dict(kwargs))
        cpu_time = time.process_time() - cpu_start
        wall_time = time.perf_counter() - wall_start
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return output, {
        "wall_time_s": wall_time,
        "cpu_time_s": cpu_time,
        "peak_python_bytes": float(peak),
        "final_python_bytes": float(current),
    }


def profile_call(
    function: Callable[..., Any],
    *args: Any,
    variables: Mapping[str, float],
    repeats: int = 3,
    warmups: int = 1,
    metadata: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ProfileResult:
    """Measure one function and return a ResourceSample.

    The caller supplies the scientific/algorithmic state vector explicitly in
    R0.1. This avoids pretending that arbitrary Python object ``len`` values are
    always the correct complexity variables. Auto-variable extraction belongs
    to a later, separately testable layer.
    """

    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    if warmups < 0:
        raise ValueError("warmups must be >= 0")

    for _ in range(warmups):
        function(*args, **kwargs)

    measurements: list[dict[str, float]] = []
    output: Any = None
    for _ in range(repeats):
        output, measured = _one_measurement(function, args, kwargs)
        measurements.append(measured)

    wall = [m["wall_time_s"] for m in measurements]
    cpu = [m["cpu_time_s"] for m in measurements]
    peaks = [m["peak_python_bytes"] for m in measurements]
    finals = [m["final_python_bytes"] for m in measurements]

    resources = {
        "wall_time_s": statistics.median(wall),
        "wall_time_p95_s": _percentile(wall, 0.95),
        "cpu_time_s": statistics.median(cpu),
        "peak_python_bytes": statistics.median(peaks),
        "final_python_bytes": statistics.median(finals),
    }
    sample_metadata = {
        "function": getattr(function, "__qualname__", getattr(function, "__name__", repr(function))),
        "module": getattr(function, "__module__", None),
        "repeats": repeats,
        "warmups": warmups,
        "machine": machine_fingerprint(),
        "measurement_semantics": {
            "peak_python_bytes": "tracemalloc Python allocation peak, not total RSS/VRAM",
            "wall_time_s": "median time.perf_counter over repetitions",
            "cpu_time_s": "median time.process_time over repetitions",
        },
    }
    sample_metadata.update(dict(metadata or {}))
    sample = ResourceSample(
        variables={key: float(value) for key, value in variables.items()},
        resources=resources,
        metadata=sample_metadata,
    )
    return ProfileResult(sample=sample, repetitions=tuple(measurements), output=output)


@dataclass
class PipelineProfile:
    stages: tuple[tuple[str, ProfileResult], ...]
    resources: Mapping[str, float]
    output: Any

    def samples(self) -> list[ResourceSample]:
        return [result.sample for _, result in self.stages]


def profile_pipeline(
    stages: Sequence[tuple[str, Callable[[Any], Any]]],
    initial_value: Any,
    *,
    variables: Mapping[str, float],
    repeats_per_stage: int = 1,
    warmups_per_stage: int = 0,
) -> PipelineProfile:
    """Profile a sequential data pipeline stage-by-stage.

    R0.1 composes sequential stages. DAG critical-path/resource-contention
    composition is represented in the theory/schema but intentionally deferred
    until its scheduler semantics can be validated independently.
    """

    current = initial_value
    profiled: list[tuple[str, ProfileResult]] = []
    for name, stage in stages:
        result = profile_call(
            stage,
            current,
            variables=variables,
            repeats=repeats_per_stage,
            warmups=warmups_per_stage,
            metadata={"pipeline_stage": name},
        )
        current = result.output
        profiled.append((name, result))

    total_wall = sum(result.resources["wall_time_s"] for _, result in profiled)
    total_cpu = sum(result.resources["cpu_time_s"] for _, result in profiled)
    peak_python = max((result.resources["peak_python_bytes"] for _, result in profiled), default=0.0)
    return PipelineProfile(
        stages=tuple(profiled),
        resources={
            "wall_time_s": total_wall,
            "cpu_time_s": total_cpu,
            "peak_python_bytes": peak_python,
        },
        output=current,
    )
