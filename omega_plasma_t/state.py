"""Typed, serializable state objects for Ω-PLASMA-T∞."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import json

@dataclass(frozen=True)
class SpeciesState:
    name: str
    charge_state: float
    mass_kg: float
    density_m3: float
    temperature_ev: float
    collision_frequency_hz: float = 0.0
    drift_speed_m_s: float = 0.0
    neutral: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors=[]
        if not self.name.strip(): errors.append("species name must be non-empty")
        if self.mass_kg <= 0: errors.append(f"{self.name}: mass_kg must be positive")
        if self.density_m3 < 0: errors.append(f"{self.name}: density_m3 must be non-negative")
        if self.temperature_ev < 0: errors.append(f"{self.name}: temperature_ev must be non-negative")
        if self.collision_frequency_hz < 0: errors.append(f"{self.name}: collision frequency must be non-negative")
        if self.neutral and self.charge_state != 0: errors.append(f"{self.name}: neutral species must have charge_state=0")
        return errors

@dataclass(frozen=True)
class GeometryState:
    characteristic_length_m: float
    dimensionality: int = 1
    boundary_type: str = "periodic"
    surface_present: bool = False
    open_field_lines: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors=[]
        if self.characteristic_length_m <= 0: errors.append("characteristic_length_m must be positive")
        if self.dimensionality not in (0,1,2,3): errors.append("dimensionality must be 0, 1, 2, or 3")
        if self.boundary_type not in {"periodic","absorbing","conducting","dielectric","open","mixed"}:
            errors.append(f"unsupported boundary_type: {self.boundary_type}")
        return errors

@dataclass(frozen=True)
class PlasmaState:
    species: tuple[SpeciesState, ...]
    geometry: GeometryState
    magnetic_field_t: float = 0.0
    electric_field_v_m: float = 0.0
    ionization_fraction: float | None = None
    pressure_pa: float | None = None
    radiation_energy_density_j_m3: float = 0.0
    relativistic_bulk_gamma: float = 1.0
    requested_observables: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors=[]
        if not self.species: errors.append("at least one species is required")
        for s in self.species: errors.extend(s.validate())
        errors.extend(self.geometry.validate())
        if self.magnetic_field_t < 0: errors.append("magnetic_field_t is a magnitude and must be non-negative")
        if self.ionization_fraction is not None and not 0 <= self.ionization_fraction <= 1:
            errors.append("ionization_fraction must be in [0,1]")
        if self.pressure_pa is not None and self.pressure_pa < 0: errors.append("pressure_pa must be non-negative")
        if self.radiation_energy_density_j_m3 < 0: errors.append("radiation energy density must be non-negative")
        if self.relativistic_bulk_gamma < 1: errors.append("relativistic_bulk_gamma must be >= 1")
        return errors

    def charged_species(self) -> tuple[SpeciesState,...]:
        return tuple(s for s in self.species if not s.neutral and s.charge_state != 0 and s.density_m3 > 0)

    def neutral_species(self) -> tuple[SpeciesState,...]:
        return tuple(s for s in self.species if s.neutral or s.charge_state == 0)

    def electron(self) -> SpeciesState | None:
        for s in self.species:
            if s.name.lower() in {"e", "e-", "electron", "electrons"} or s.charge_state < 0:
                return s
        return None

    def ion_species(self) -> tuple[SpeciesState,...]:
        return tuple(s for s in self.species if s.charge_state > 0 and not s.neutral)

    def to_dict(self) -> dict[str, Any]: return asdict(self)
    def to_json(self, *, indent:int=2) -> str: return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlasmaState":
        species=tuple(SpeciesState(**x) for x in data["species"])
        geometry=GeometryState(**data["geometry"])
        rest={k:v for k,v in data.items() if k not in {"species","geometry"}}
        for key in ("requested_observables","tags"):
            if key in rest: rest[key]=tuple(rest[key])
        return cls(species=species, geometry=geometry, **rest)
