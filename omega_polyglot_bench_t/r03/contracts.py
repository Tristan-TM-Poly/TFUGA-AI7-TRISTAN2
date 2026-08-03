"""Typed evidence contracts for Ω-POLYGLOT-BENCH-T R0.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModeMeasurement:
    backend: str
    mode: str
    available: bool
    correct: bool
    median_ns: int | None
    p95_ns: int | None
    mean_ns: float | None
    setup_ns: int | None
    max_abs_error: float | None
    speedup_vs_python: float | None
    effective_gib_per_s: float | None
    repetitions: int
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass(frozen=True)
class SizeBenchmark:
    size: int
    bytes_per_call: int
    python_median_ns: int
    measurements: tuple[ModeMeasurement, ...] = field(default_factory=tuple)
    best_correct_backend: str | None = None
    best_correct_mode: str | None = None
    best_speedup_vs_python: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "bytes_per_call": self.bytes_per_call,
            "python_median_ns": self.python_median_ns,
            "measurements": [item.to_dict() for item in self.measurements],
            "best_correct_backend": self.best_correct_backend,
            "best_correct_mode": self.best_correct_mode,
            "best_speedup_vs_python": self.best_speedup_vs_python,
        }


@dataclass(frozen=True)
class ThroughputReport:
    algorithm: str
    scalar: float
    seed: int
    warmups: int
    repetitions: int
    sizes: tuple[SizeBenchmark, ...]
    status: str = "OAK_LOCAL_SOFTWARE_BENCHMARK_ONLY"
    universal_language_winner_claimed: bool = False
    energy_measured: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "scalar": self.scalar,
            "seed": self.seed,
            "warmups": self.warmups,
            "repetitions": self.repetitions,
            "sizes": [item.to_dict() for item in self.sizes],
            "status": self.status,
            "universal_language_winner_claimed": self.universal_language_winner_claimed,
            "energy_measured": self.energy_measured,
        }
