from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .genome import SolidGenome
from .models import BondClass, Dimensionality, OrderClass, PropertyDomain


@dataclass(frozen=True, slots=True)
class OntologyTag:
    namespace: str
    value: str
    confidence: float
    rationale: str

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("Ontology confidence must be within [0, 1]")

    @property
    def key(self) -> str:
        return f"{self.namespace}:{self.value}"


FAMILY_ALIASES: Mapping[str, str] = {
    "metal": "metal_alloy",
    "alloy": "metal_alloy",
    "ceramic": "ceramic",
    "glass": "glass",
    "polymer": "polymer",
    "composite": "composite",
    "semiconductor": "semiconductor",
    "granular": "granular",
    "biological": "biological_solid",
    "architected": "architected_material",
    "2d": "two_dimensional_material",
}


FUNCTION_KEYWORDS: Mapping[str, PropertyDomain] = {
    "young": PropertyDomain.MECHANICAL,
    "strength": PropertyDomain.MECHANICAL,
    "toughness": PropertyDomain.MECHANICAL,
    "hardness": PropertyDomain.MECHANICAL,
    "density": PropertyDomain.GEOMETRIC,
    "thermal": PropertyDomain.THERMAL,
    "conductivity": PropertyDomain.ELECTRICAL,
    "resistivity": PropertyDomain.ELECTRICAL,
    "permittivity": PropertyDomain.ELECTRICAL,
    "magnet": PropertyDomain.MAGNETIC,
    "band_gap": PropertyDomain.OPTICAL,
    "refractive": PropertyDomain.OPTICAL,
    "corrosion": PropertyDomain.CHEMICAL,
    "diffusivity": PropertyDomain.CHEMICAL,
    "ionic": PropertyDomain.IONIC,
    "acoustic": PropertyDomain.ACOUSTIC,
    "biocompat": PropertyDomain.BIOLOGICAL,
    "cost": PropertyDomain.ECONOMIC,
    "fatigue": PropertyDomain.DURABILITY,
}


def canonical_family(value: str) -> str:
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    for token, canonical in FAMILY_ALIASES.items():
        if token in key:
            return canonical
    return key or "unclassified"


def classify(genome: SolidGenome) -> tuple[OntologyTag, ...]:
    tags: list[OntologyTag] = []
    tags.append(
        OntologyTag(
            "family",
            canonical_family(genome.family),
            0.95,
            "Declared material family normalized through the Ω-SOLID ontology.",
        )
    )
    tags.append(
        OntologyTag(
            "order",
            genome.order.value,
            1.0,
            "Explicit structural-order field.",
        )
    )
    tags.append(
        OntologyTag(
            "dimensionality",
            genome.dimensionality.value,
            1.0,
            "Explicit effective-dimensionality field.",
        )
    )

    for bond in genome.bonds:
        if bond.weight > 0:
            tags.append(
                OntologyTag(
                    "bond",
                    bond.kind.value,
                    min(1.0, max(0.0, bond.weight)),
                    f"Bond-mixture weight {bond.weight:.3f}.",
                )
            )

    for record in genome.properties:
        tags.append(
            OntologyTag(
                "function",
                record.domain.value,
                0.9,
                f"Property '{record.name}' is explicitly assigned to this domain.",
            )
        )

    if genome.interfaces:
        tags.append(
            OntologyTag(
                "architecture",
                "interface_dominated_candidate",
                min(1.0, 0.45 + 0.08 * len(genome.interfaces)),
                "One or more explicit interfaces are represented.",
            )
        )
    if genome.defects:
        criticality = max(defect.criticality for defect in genome.defects)
        tags.append(
            OntologyTag(
                "defect_regime",
                "defect_sensitive" if criticality >= 0.5 else "defect_described",
                0.65 + 0.35 * criticality,
                "Defect records and their maximum criticality are available.",
            )
        )
    if genome.geometry.get("porosity", 0):
        tags.append(
            OntologyTag(
                "architecture",
                "porous",
                0.95,
                "A nonzero porosity is explicitly declared.",
            )
        )
    if genome.order is OrderClass.HIERARCHICAL:
        tags.append(
            OntologyTag(
                "architecture",
                "multiscale_hierarchical",
                0.95,
                "The genome declares a hierarchical organization.",
            )
        )
    if genome.dimensionality is Dimensionality.TWO_D:
        tags.append(
            OntologyTag(
                "confinement",
                "two_dimensional",
                1.0,
                "The genome declares effective two-dimensional confinement.",
            )
        )

    deduplicated: dict[str, OntologyTag] = {}
    for tag in tags:
        previous = deduplicated.get(tag.key)
        if previous is None or tag.confidence > previous.confidence:
            deduplicated[tag.key] = tag
    return tuple(deduplicated[key] for key in sorted(deduplicated))


def index_by_tag(genomes: Iterable[SolidGenome]) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    for genome in genomes:
        for tag in classify(genome):
            index.setdefault(tag.key, []).append(genome.identifier)
    return {key: tuple(sorted(set(values))) for key, values in sorted(index.items())}


def bond_vector(genome: SolidGenome) -> dict[BondClass, float]:
    vector = {kind: 0.0 for kind in BondClass}
    for contribution in genome.bonds:
        vector[contribution.kind] += contribution.weight
    return vector
