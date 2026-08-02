from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from typing import Callable

from .genome import SolidGenome
from .archetypes_crystalline import metallic_crystal, ionic_crystal, covalent_network, semiconductor_crystal
from .archetypes_disordered import amorphous_glass, amorphous_polymer, semicrystalline_polymer
from .archetypes_structured import fiber_composite, porous_ceramic, granular_solid
from .archetypes_advanced import two_dimensional_material, architected_lattice

_BUILDERS: dict[str, Callable[[], SolidGenome]] = {
    "metallic_crystal": metallic_crystal,
    "ionic_crystal": ionic_crystal,
    "covalent_network": covalent_network,
    "semiconductor_crystal": semiconductor_crystal,
    "amorphous_glass": amorphous_glass,
    "amorphous_polymer": amorphous_polymer,
    "semicrystalline_polymer": semicrystalline_polymer,
    "fiber_composite": fiber_composite,
    "porous_ceramic": porous_ceramic,
    "granular_solid": granular_solid,
    "two_dimensional_material": two_dimensional_material,
    "architected_lattice": architected_lattice,
}

ARCHETYPE_NAMES = tuple(_BUILDERS)

def build_archetype(name: str) -> SolidGenome:
    try:
        return _BUILDERS[name]()
    except KeyError as exc:
        raise KeyError(f"Unknown archetype {name!r}; choose from {ARCHETYPE_NAMES}") from exc

def iter_archetypes() -> Iterator[SolidGenome]:
    for name in ARCHETYPE_NAMES:
        yield build_archetype(name)

def clone_with_identifier(genome: SolidGenome, identifier: str, name: str | None = None) -> SolidGenome:
    return replace(genome, identifier=identifier, name=name or genome.name)
