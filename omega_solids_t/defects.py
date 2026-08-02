from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Iterable, Mapping

from .genome import SolidGenome
from .models import DefectKind, DefectRecord


@dataclass(frozen=True, slots=True)
class DefectInteraction:
    source: int
    target: int
    mechanism: str
    strength: float
    conditions: Mapping[str, Any] = field(default_factory=dict)
    evidence: str | None = None

    def __post_init__(self) -> None:
        if self.source < 0 or self.target < 0:
            raise ValueError("Defect interaction indices cannot be negative")
        if self.source == self.target:
            raise ValueError("Self-interactions are not represented as pair interactions")
        if not 0 <= self.strength <= 1:
            raise ValueError("Interaction strength must be within [0, 1]")
        if not self.mechanism.strip():
            raise ValueError("Interaction mechanism cannot be empty")


@dataclass(frozen=True, slots=True)
class DefectTensor:
    kind_distribution: Mapping[str, float]
    mean_criticality: float
    maximum_criticality: float
    mobile_fraction: float
    energetic_coverage: float
    density_coverage: float
    functional_fraction: float
    interaction_density: float
    cascade_risk: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind_distribution": dict(self.kind_distribution),
            "mean_criticality": self.mean_criticality,
            "maximum_criticality": self.maximum_criticality,
            "mobile_fraction": self.mobile_fraction,
            "energetic_coverage": self.energetic_coverage,
            "density_coverage": self.density_coverage,
            "functional_fraction": self.functional_fraction,
            "interaction_density": self.interaction_density,
            "cascade_risk": self.cascade_risk,
        }


class DefectInteractionGraph:
    def __init__(
        self,
        defects: Iterable[DefectRecord],
        interactions: Iterable[DefectInteraction] = (),
    ) -> None:
        self.defects = tuple(defects)
        self.interactions = tuple(interactions)
        for interaction in self.interactions:
            if interaction.source >= len(self.defects) or interaction.target >= len(self.defects):
                raise IndexError("Defect interaction references an unavailable defect")

    def adjacency(self) -> dict[int, tuple[DefectInteraction, ...]]:
        mapping: dict[int, list[DefectInteraction]] = {
            index: [] for index in range(len(self.defects))
        }
        for interaction in self.interactions:
            mapping[interaction.source].append(interaction)
            mapping[interaction.target].append(interaction)
        return {
            index: tuple(sorted(values, key=lambda item: (item.target, item.mechanism)))
            for index, values in mapping.items()
        }

    def local_amplification(self, index: int) -> float:
        if not 0 <= index < len(self.defects):
            raise IndexError(index)
        base = self.defects[index].criticality
        complement = 1.0 - base
        for interaction in self.adjacency()[index]:
            other_index = (
                interaction.target if interaction.source == index else interaction.source
            )
            other = self.defects[other_index]
            activation = interaction.strength * other.criticality
            complement *= 1.0 - max(0.0, min(1.0, activation))
        return 1.0 - complement

    def cascade_risk(self) -> float:
        if not self.defects:
            return 0.0
        amplified = [self.local_amplification(index) for index in range(len(self.defects))]
        return 1.0 - math.prod(1.0 - min(1.0, value) for value in amplified)

    def tensor(self) -> DefectTensor:
        count = len(self.defects)
        if count == 0:
            return DefectTensor({}, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        kind_counts: dict[str, int] = {}
        for record in self.defects:
            kind_counts[record.kind.value] = kind_counts.get(record.kind.value, 0) + 1
        possible_pairs = count * (count - 1) / 2
        unique_pairs = {
            tuple(sorted((interaction.source, interaction.target)))
            for interaction in self.interactions
        }
        return DefectTensor(
            kind_distribution={
                key: value / count for key, value in sorted(kind_counts.items())
            },
            mean_criticality=sum(record.criticality for record in self.defects) / count,
            maximum_criticality=max(record.criticality for record in self.defects),
            mobile_fraction=sum(record.mobility not in (None, 0) for record in self.defects) / count,
            energetic_coverage=sum(
                record.formation_energy is not None for record in self.defects
            )
            / count,
            density_coverage=sum(record.density is not None for record in self.defects) / count,
            functional_fraction=sum(bool(record.function) for record in self.defects) / count,
            interaction_density=(len(unique_pairs) / possible_pairs if possible_pairs else 0.0),
            cascade_risk=self.cascade_risk(),
        )

    @classmethod
    def infer(cls, genome: SolidGenome) -> "DefectInteractionGraph":
        interactions: list[DefectInteraction] = []
        for left_index, left in enumerate(genome.defects):
            for right_index in range(left_index + 1, len(genome.defects)):
                right = genome.defects[right_index]
                mechanism, strength = infer_pair_interaction(left, right)
                if strength > 0:
                    interactions.append(
                        DefectInteraction(
                            left_index,
                            right_index,
                            mechanism,
                            strength,
                            evidence="heuristic_candidate_requires_validation",
                        )
                    )
        return cls(genome.defects, interactions)


def infer_pair_interaction(left: DefectRecord, right: DefectRecord) -> tuple[str, float]:
    pair = frozenset((left.kind, right.kind))
    rules: dict[frozenset[DefectKind], tuple[str, float]] = {
        frozenset((DefectKind.DISLOCATION, DefectKind.GRAIN_BOUNDARY)): (
            "dislocation_boundary_absorption_or_pileup",
            0.65,
        ),
        frozenset((DefectKind.CRACK, DefectKind.PORE)): (
            "stress_concentration_coalescence",
            0.8,
        ),
        frozenset((DefectKind.CRACK, DefectKind.RESIDUAL_STRESS)): (
            "residual_stress_crack_driving_force",
            0.85,
        ),
        frozenset((DefectKind.INCLUSION, DefectKind.CRACK)): (
            "inclusion_debonding_or_crack_deflection",
            0.7,
        ),
        frozenset((DefectKind.VACANCY, DefectKind.INTERSTITIAL)): (
            "recombination_or_cluster_formation",
            0.6,
        ),
        frozenset((DefectKind.CHEMICAL_DISORDER, DefectKind.ELECTRONIC)): (
            "disorder_localization_or_trapping",
            0.55,
        ),
        frozenset((DefectKind.DELAMINATION, DefectKind.CRACK)): (
            "interfacial_crack_coupling",
            0.9,
        ),
    }
    if pair in rules:
        mechanism, base = rules[pair]
    elif left.kind == right.kind:
        mechanism, base = "same_kind_collective_interaction", 0.35
    else:
        mechanism, base = "unresolved_cross_defect_coupling", 0.1
    criticality_factor = math.sqrt(max(0.0, left.criticality * right.criticality))
    return mechanism, min(1.0, base * (0.5 + criticality_factor))
