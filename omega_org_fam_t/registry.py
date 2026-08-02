"""Versioned, fingerprinted registry for the Ω-ORG-FAM-T ultra address space."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from .vocabularies import (ELECTRONIC_CLASSES, ENVIRONMENTS, FUNCTIONAL_FAMILIES,
                           REACTION_ARCHETYPES, SKELETONS, STEREO_CLASSES)

ISOTOPE_PROFILES = ("natural_abundance", "deuterium_enriched", "carbon13_enriched", "heteroatom_isotope_enriched")
PROTONATION_STATES = ("neutral", "cationic", "anionic", "zwitterionic", "protonated", "deprotonated", "multiply_charged", "unspecified_charge_state")
CONFORMER_CLASSES = ("rigid", "single_rotor", "few_rotors", "flexible_chain", "ring_pucker", "folded", "extended", "conformational_ensemble")
SOLVENT_CLASSES = ("vacuum_or_gas", "nonpolar_aprotic", "polar_aprotic", "polar_protic", "aqueous", "ionic_liquid", "supercritical", "heterogeneous_interface")
TEMPERATURE_REGIMES = ("cryogenic", "low", "ambient", "moderate", "high", "very_high", "phase_transition_window", "unspecified_temperature")
PRESSURE_REGIMES = ("low_pressure", "ambient_pressure", "high_pressure", "extreme_pressure")

@dataclass(frozen=True, slots=True)
class AxisSpec:
    name: str
    values: tuple[str, ...]
    provenance: str = "omega_org_fam_t_curated_r02"
    status: str = "controlled_vocabulary"

    def __post_init__(self) -> None:
        if not self.name or not self.values:
            raise ValueError("axis name and values are required")
        if len(set(self.values)) != len(self.values):
            raise ValueError(f"duplicate values in axis {self.name}")

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "values": list(self.values), "provenance": self.provenance, "status": self.status}

@dataclass(frozen=True, slots=True)
class OrganicRegistry:
    version: str
    axes: tuple[AxisSpec, ...]

    def __post_init__(self) -> None:
        names = [axis.name for axis in self.axes]
        if len(set(names)) != len(names):
            raise ValueError("axis names must be unique")

    @property
    def radices(self) -> tuple[int, ...]:
        return tuple(len(axis.values) for axis in self.axes)

    @property
    def family_space_size(self) -> int:
        return math.prod(self.radices)

    @property
    def linked_object_space_size(self) -> int:
        return self.family_space_size * 4

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {"version": self.version, "axes": [axis.to_dict() for axis in self.axes]}

    def dump(self, path: Path) -> None:
        path.write_text(json.dumps({**self.to_dict(), "fingerprint": self.fingerprint}, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "OrganicRegistry":
        axes_raw = raw.get("axes")
        if not isinstance(axes_raw, list):
            raise ValueError("axes must be a list")
        axes = tuple(AxisSpec(name=str(a["name"]), values=tuple(str(v) for v in a["values"]), provenance=str(a.get("provenance", "external_registry")), status=str(a.get("status", "controlled_vocabulary"))) for a in axes_raw if isinstance(a, dict))
        return cls(version=str(raw.get("version", "external")), axes=axes)

    @classmethod
    def load(cls, path: Path) -> "OrganicRegistry":
        return cls.from_mapping(json.loads(path.read_text(encoding="utf-8")))


def default_ultra_registry() -> OrganicRegistry:
    return OrganicRegistry("R0.2-ultra", (
        AxisSpec("skeleton", tuple(SKELETONS)),
        AxisSpec("functional_family", tuple(FUNCTIONAL_FAMILIES)),
        AxisSpec("electronic_class", tuple(ELECTRONIC_CLASSES)),
        AxisSpec("reaction_archetype", tuple(REACTION_ARCHETYPES)),
        AxisSpec("stereo_class", tuple(STEREO_CLASSES)),
        AxisSpec("environment", tuple(ENVIRONMENTS)),
        AxisSpec("isotope_profile", ISOTOPE_PROFILES),
        AxisSpec("protonation_state", PROTONATION_STATES),
        AxisSpec("conformer_class", CONFORMER_CLASSES),
        AxisSpec("solvent_class", SOLVENT_CLASSES),
        AxisSpec("temperature_regime", TEMPERATURE_REGIMES),
        AxisSpec("pressure_regime", PRESSURE_REGIMES),
    ))
