from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import fmean
from typing import Any, Iterable, Mapping, Sequence

from .genome import SolidGenome
from .models import BondClass, DefectKind, EpistemicStatus, PropertyRecord


def _shannon_entropy(probabilities: Iterable[float]) -> float:
    values = [float(value) for value in probabilities if value > 0]
    total = sum(values)
    if total <= 0:
        return 0.0
    normalized = [value / total for value in values]
    return -sum(value * math.log(value) for value in normalized)


def normalized_entropy(probabilities: Iterable[float]) -> float:
    values = [float(value) for value in probabilities if value > 0]
    if len(values) <= 1:
        return 0.0
    return _shannon_entropy(values) / math.log(len(values))


def composition_entropy(genome: SolidGenome) -> float:
    return normalized_entropy(component.fraction for component in genome.composition)


def bond_hybridization(genome: SolidGenome) -> float:
    return normalized_entropy(contribution.weight for contribution in genome.bonds)


def phase_entropy(genome: SolidGenome) -> float:
    return normalized_entropy(phase.fraction for phase in genome.phases)


def defect_criticality(genome: SolidGenome) -> float:
    if not genome.defects:
        return 0.0
    weights: list[float] = []
    for defect in genome.defects:
        density_weight = 1.0
        if defect.density is not None:
            density_weight = 1.0 + math.log1p(abs(defect.density.value)) / 100.0
        weights.append(min(1.0, defect.criticality * density_weight))
    complement = 1.0
    for weight in weights:
        complement *= 1.0 - max(0.0, min(1.0, weight))
    return 1.0 - complement


def interface_complexity(genome: SolidGenome) -> float:
    if not genome.interfaces:
        return 0.0
    defect_count = sum(len(interface.defects) for interface in genome.interfaces)
    property_count = sum(len(interface.properties) for interface in genome.interfaces)
    raw = len(genome.interfaces) + 0.5 * defect_count + 0.25 * property_count
    return 1.0 - math.exp(-raw / 4.0)


def porosity(genome: SolidGenome) -> float:
    value = float(genome.geometry.get("porosity", 0.0))
    if not 0 <= value < 1:
        raise ValueError("Geometry porosity must be within [0, 1)")
    return value


def hierarchy_depth(genome: SolidGenome) -> int:
    explicit = genome.geometry.get("hierarchy_levels")
    if explicit is not None:
        return max(1, int(explicit))
    scales = genome.geometry.get("scales", [])
    if isinstance(scales, Sequence) and not isinstance(scales, (str, bytes)):
        return max(1, len(scales))
    return 1


def provenance_coverage(genome: SolidGenome) -> float:
    if not genome.properties:
        return 1.0 if genome.provenance else 0.0
    covered = 0
    for record in genome.properties:
        quantity = record.quantity
        if quantity.source and quantity.method:
            covered += 1
    return covered / len(genome.properties)


def uncertainty_coverage(genome: SolidGenome) -> float:
    if not genome.properties:
        return 0.0
    return sum(
        record.quantity.uncertainty is not None for record in genome.properties
    ) / len(genome.properties)


def measured_fraction(genome: SolidGenome) -> float:
    if not genome.properties:
        return 0.0
    acceptable = {
        EpistemicStatus.MEASURED,
        EpistemicStatus.INDEPENDENTLY_VALIDATED,
    }
    return sum(record.quantity.status in acceptable for record in genome.properties) / len(
        genome.properties
    )


def anisotropy_index_from_tensor(tensor: Sequence[Sequence[float]]) -> float:
    rows = [tuple(float(value) for value in row) for row in tensor]
    if not rows or any(len(row) != len(rows) for row in rows):
        raise ValueError("Tensor must be non-empty and square")
    diagonal = [abs(rows[index][index]) for index in range(len(rows))]
    mean = fmean(diagonal)
    if mean == 0:
        return 0.0
    spread = math.sqrt(fmean((value - mean) ** 2 for value in diagonal))
    off_diagonal = [
        abs(rows[i][j])
        for i in range(len(rows))
        for j in range(len(rows))
        if i != j
    ]
    coupling = fmean(off_diagonal) / mean if off_diagonal else 0.0
    return max(0.0, spread / mean + coupling)


def property_anisotropy(genome: SolidGenome) -> float:
    values: list[float] = []
    for record in genome.properties:
        if record.tensor is not None:
            values.append(anisotropy_index_from_tensor(record.tensor))
    return fmean(values) if values else 0.0


def property_status_distribution(genome: SolidGenome) -> dict[str, float]:
    counts: dict[str, int] = {}
    for record in genome.properties:
        status = record.quantity.status.value
        counts[status] = counts.get(status, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return {}
    return {key: counts[key] / total for key in sorted(counts)}


def defect_kind_distribution(genome: SolidGenome) -> dict[str, float]:
    counts = {kind.value: 0 for kind in DefectKind}
    for record in genome.defects:
        counts[record.kind.value] += 1
    total = sum(counts.values())
    if total == 0:
        return {}
    return {key: value / total for key, value in counts.items() if value}


def bond_distribution(genome: SolidGenome) -> dict[str, float]:
    vector = {kind.value: 0.0 for kind in BondClass}
    for record in genome.bonds:
        vector[record.kind.value] += record.weight
    return {key: value for key, value in vector.items() if value}


@dataclass(frozen=True, slots=True)
class CVCDSolidSignature:
    composition_entropy: float
    bond_hybridization: float
    phase_entropy: float
    defect_criticality: float
    interface_complexity: float
    porosity: float
    hierarchy_depth: int
    anisotropy: float
    provenance_coverage: float
    uncertainty_coverage: float
    measured_fraction: float
    property_count: int
    defect_count: int
    interface_count: int
    phase_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "composition_entropy": self.composition_entropy,
            "bond_hybridization": self.bond_hybridization,
            "phase_entropy": self.phase_entropy,
            "defect_criticality": self.defect_criticality,
            "interface_complexity": self.interface_complexity,
            "porosity": self.porosity,
            "hierarchy_depth": self.hierarchy_depth,
            "anisotropy": self.anisotropy,
            "provenance_coverage": self.provenance_coverage,
            "uncertainty_coverage": self.uncertainty_coverage,
            "measured_fraction": self.measured_fraction,
            "property_count": self.property_count,
            "defect_count": self.defect_count,
            "interface_count": self.interface_count,
            "phase_count": self.phase_count,
        }

    def vector(self) -> tuple[float, ...]:
        return (
            self.composition_entropy,
            self.bond_hybridization,
            self.phase_entropy,
            self.defect_criticality,
            self.interface_complexity,
            self.porosity,
            math.tanh(self.hierarchy_depth / 4.0),
            math.tanh(self.anisotropy),
            self.provenance_coverage,
            self.uncertainty_coverage,
            self.measured_fraction,
        )



def build_signature(genome: SolidGenome) -> CVCDSolidSignature:
    return CVCDSolidSignature(
        composition_entropy=composition_entropy(genome),
        bond_hybridization=bond_hybridization(genome),
        phase_entropy=phase_entropy(genome),
        defect_criticality=defect_criticality(genome),
        interface_complexity=interface_complexity(genome),
        porosity=porosity(genome),
        hierarchy_depth=hierarchy_depth(genome),
        anisotropy=property_anisotropy(genome),
        provenance_coverage=provenance_coverage(genome),
        uncertainty_coverage=uncertainty_coverage(genome),
        measured_fraction=measured_fraction(genome),
        property_count=len(genome.properties),
        defect_count=len(genome.defects),
        interface_count=len(genome.interfaces),
        phase_count=len(genome.phases),
    )


def signature_distance(
    left: CVCDSolidSignature,
    right: CVCDSolidSignature,
    *,
    weights: Sequence[float] | None = None,
) -> float:
    a = left.vector()
    b = right.vector()
    if len(a) != len(b):
        raise AssertionError("Signature vectors have incompatible dimensions")
    chosen = tuple(1.0 for _ in a) if weights is None else tuple(weights)
    if len(chosen) != len(a):
        raise ValueError("Weights must match signature vector length")
    if any(value < 0 for value in chosen):
        raise ValueError("Distance weights cannot be negative")
    denominator = sum(chosen)
    if denominator <= 0:
        return 0.0
    squared = sum(weight * (x - y) ** 2 for x, y, weight in zip(a, b, chosen))
    return math.sqrt(squared / denominator)


def compare_properties(
    left: SolidGenome, right: SolidGenome
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    left_map = left.property_map()
    right_map = right.property_map()
    for name in sorted(set(left_map) | set(right_map)):
        a = left_map.get(name)
        b = right_map.get(name)
        if a is None or b is None:
            result[name] = {
                "status": "missing_on_left" if a is None else "missing_on_right"
            }
            continue
        if a.quantity.unit != b.quantity.unit:
            result[name] = {
                "status": "unit_mismatch",
                "left_unit": a.quantity.unit,
                "right_unit": b.quantity.unit,
            }
            continue
        difference = b.quantity.value - a.quantity.value
        relative = None if a.quantity.value == 0 else difference / abs(a.quantity.value)
        result[name] = {
            "status": "comparable",
            "unit": a.quantity.unit,
            "difference": difference,
            "relative_difference": relative,
        }
    return result
