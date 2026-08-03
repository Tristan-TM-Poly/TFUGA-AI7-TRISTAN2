"""Serializable contracts for R0.4 autotuning and workload campaigns."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CandidateMeasurement:
    algorithm: str
    backend: str
    profile: str
    variant: str
    size: int
    correct: bool
    median_ns: int | None
    mean_ns: float | None
    p95_ns: int | None
    setup_ns: int | None
    max_abs_error: float | None
    speedup_vs_python: float | None
    effective_gb_s: float | None
    features: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def candidate_id(self) -> str:
        return f"{self.backend}:{self.profile}:{self.variant}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidate_id"] = self.candidate_id
        payload["features"] = list(self.features)
        payload["notes"] = list(self.notes)
        return payload


@dataclass(frozen=True)
class SizeChampion:
    algorithm: str
    size: int
    candidate_id: str
    median_ns: int
    speedup_vs_python: float | None
    max_abs_error: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AutotuneReport:
    schema_version: str
    created_at_utc: str
    hardware: dict[str, Any]
    protocol: dict[str, Any]
    measurements: tuple[CandidateMeasurement, ...]
    champions: tuple[SizeChampion, ...]
    status: str = "OAK_SOFTWARE_AUTOTUNE_ONLY"
    claims: dict[str, bool] = field(default_factory=lambda: {
        "universal_language_winner": False,
        "scientific_validation": False,
        "energy_measured": False,
        "hardware_counter_bandwidth": False,
    })

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at_utc": self.created_at_utc,
            "hardware": self.hardware,
            "protocol": self.protocol,
            "measurements": [m.to_dict() for m in self.measurements],
            "champions": [c.to_dict() for c in self.champions],
            "status": self.status,
            "claims": self.claims,
        }
