"""Typed objects for inverse electromagnetic-source synthesis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


PROTOTYPE_TIERS = (
    "simulation_only",
    "low_power_benchtop",
    "certified_module",
    "institutional_facility",
)


@dataclass(frozen=True)
class SpectrumTarget:
    """Multidimensional target emitted field or photon distribution.

    The object intentionally stores requirements rather than construction
    instructions.  ``max_prototype_tier`` is a hard routing constraint used by
    the SafetyGate.
    """

    center_frequency_hz: float
    bandwidth_hz: float = 0.0
    power_w: float = 1e-3
    polarization: str = "unspecified"
    coherence: str = "unspecified"
    beam_geometry: str = "unspecified"
    temporal_profile: str = "continuous"
    modulation_bandwidth_hz: float = 0.0
    environment: str = "simulation"
    intended_use: str = "research"
    max_prototype_tier: str = "low_power_benchtop"
    allow_radiating_output: bool = False
    jurisdiction: str = "unspecified"
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.center_frequency_hz <= 0:
            raise ValueError("center_frequency_hz must be positive")
        if self.bandwidth_hz < 0:
            raise ValueError("bandwidth_hz must be non-negative")
        if self.power_w <= 0:
            raise ValueError("power_w must be positive")
        if self.modulation_bandwidth_hz < 0:
            raise ValueError("modulation_bandwidth_hz must be non-negative")
        if self.max_prototype_tier not in PROTOTYPE_TIERS:
            raise ValueError(
                "max_prototype_tier must be one of " + ", ".join(PROTOTYPE_TIERS)
            )

    @property
    def fractional_bandwidth(self) -> float:
        return self.bandwidth_hz / self.center_frequency_hz

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SpectrumTarget":
        values = dict(payload)
        values["notes"] = tuple(values.get("notes", ()))
        return cls(**values)


@dataclass(frozen=True)
class Mechanism:
    mechanism_id: str
    label: str
    min_frequency_hz: float
    max_frequency_hz: float
    spectral_character: str
    coherence_capabilities: tuple[str, ...]
    device_families: tuple[str, ...]
    conversion_paths: tuple[str, ...]
    simulation_models: tuple[str, ...]
    metrology_families: tuple[str, ...]
    hazards: tuple[str, ...]
    minimum_prototype_tier: str
    evidence_status: str = "established_physics"
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.min_frequency_hz <= 0:
            raise ValueError("mechanism minimum frequency must be positive")
        if self.max_frequency_hz <= self.min_frequency_hz:
            raise ValueError("mechanism frequency interval must be increasing")
        if self.minimum_prototype_tier not in PROTOTYPE_TIERS:
            raise ValueError("invalid mechanism prototype tier")

    def supports(self, frequency_hz: float) -> bool:
        return self.min_frequency_hz <= frequency_hz <= self.max_frequency_hz

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MechanismCandidate:
    mechanism_id: str
    label: str
    score: float
    status: str
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    required_prototype_tier: str
    proposed_devices: tuple[str, ...]
    simulation_models: tuple[str, ...]
    metrology_families: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourcePlan:
    target: SpectrumTarget
    spectral_region: str
    wavelength_m: float
    photon_energy_ev: float
    ionizing_candidate: bool
    recommended: tuple[MechanismCandidate, ...]
    conditional: tuple[MechanismCandidate, ...]
    rejected: tuple[MechanismCandidate, ...]
    architecture_blocks: tuple[str, ...]
    metrology_plan: tuple[str, ...]
    safety_status: str
    safety_reasons: tuple[str, ...]
    required_controls: tuple[str, ...]
    assumptions: tuple[str, ...]
    epistemic_status: str = "engineering_hypothesis_pending_simulation"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["target"] = self.target.to_dict()
        return result
