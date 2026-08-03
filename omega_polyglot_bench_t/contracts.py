"""Typed contracts shared by the Ω-POLYGLOT-BENCH-T runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class BackendMeasurement:
    backend: str
    available: bool
    correct: bool
    cold_ns: int | None
    median_ns: int | None
    p95_ns: int | None
    mean_ns: float | None
    max_abs_error: float | None
    repetitions: int
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass(frozen=True)
class BenchmarkReport:
    algorithm: str
    size: int
    scalar: float
    seed: int
    warmups: int
    repetitions: int
    includes_ffi_conversion: bool
    measurements: tuple[BackendMeasurement, ...] = field(default_factory=tuple)
    selected_backend: str | None = None
    status: str = "OAK_SOFTWARE_BENCHMARK_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "size": self.size,
            "scalar": self.scalar,
            "seed": self.seed,
            "warmups": self.warmups,
            "repetitions": self.repetitions,
            "includes_ffi_conversion": self.includes_ffi_conversion,
            "measurements": [item.to_dict() for item in self.measurements],
            "selected_backend": self.selected_backend,
            "status": self.status,
        }
