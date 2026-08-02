from __future__ import annotations

"""Typed scientific objects for Ω-PCT∞ R0.3 MAX.

The module deliberately separates physical values, epistemic status, provenance,
and machine validation.  A serializable object is not thereby a physical fact.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from fractions import Fraction
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


class EpistemicStatus(str, Enum):
    ESTABLISHED = "established"
    EFFECTIVE = "effective"
    CALCULATED = "calculated"
    SIMULATED = "simulated"
    RECONSTRUCTED = "reconstructed"
    HYPOTHETICAL = "hypothetical"
    EXCLUDED = "excluded"
    FALSIFIED = "falsified"
    EXPLORATORY = "exploratory"
    UNKNOWN = "unknown"


class OntologyLevel(str, Enum):
    FUNDAMENTAL = "fundamental"
    COMPOSITE = "composite"
    EFFECTIVE = "effective"
    COLLECTIVE = "collective"
    TOPOLOGICAL = "topological"
    GEOMETRIC = "geometric"
    HYPOTHETICAL = "hypothetical"


class FieldKind(str, Enum):
    SCALAR = "scalar"
    FERMION = "fermion"
    VECTOR = "vector"
    TENSOR = "tensor"
    GHOST = "ghost"
    AUXILIARY = "auxiliary"


class Chirality(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    VECTORLIKE = "vectorlike"
    NONE = "none"


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(frozen=True, slots=True)
class SourceRef:
    source_id: str
    version: str
    locator: str | None = None
    retrieved_at: str | None = None
    sha256: str | None = None
    license: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.source_id.strip():
            errors.append("source_id must be non-empty")
        if not self.version.strip():
            errors.append("source version must be non-empty")
        if self.sha256 is not None and (
            len(self.sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.sha256.lower())
        ):
            errors.append("source sha256 must contain 64 hexadecimal characters")
        return errors


@dataclass(frozen=True, slots=True)
class Uncertainty:
    statistical: float | None = None
    systematic: float | None = None
    theoretical: float | None = None
    numerical: float | None = None
    model: float | None = None
    provenance: float | None = None
    unknown_unknown: str | None = None

    def components(self) -> tuple[float, ...]:
        return tuple(
            value
            for value in (
                self.statistical,
                self.systematic,
                self.theoretical,
                self.numerical,
                self.model,
                self.provenance,
            )
            if value is not None
        )

    def quadrature(self) -> float | None:
        values = self.components()
        if not values:
            return None
        return sum(value * value for value in values) ** 0.5

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("statistical", self.statistical),
            ("systematic", self.systematic),
            ("theoretical", self.theoretical),
            ("numerical", self.numerical),
            ("model", self.model),
            ("provenance", self.provenance),
        ):
            if value is not None and value < 0:
                errors.append(f"uncertainty {name} must be non-negative")
        return errors


@dataclass(frozen=True, slots=True)
class Domain:
    energy_min_gev: float | None = None
    energy_max_gev: float | None = None
    temperature_min_k: float | None = None
    temperature_max_k: float | None = None
    medium: str | None = None
    assumptions: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if (
            self.energy_min_gev is not None
            and self.energy_max_gev is not None
            and self.energy_min_gev > self.energy_max_gev
        ):
            errors.append("energy_min_gev exceeds energy_max_gev")
        if (
            self.temperature_min_k is not None
            and self.temperature_max_k is not None
            and self.temperature_min_k > self.temperature_max_k
        ):
            errors.append("temperature_min_k exceeds temperature_max_k")
        return errors


@dataclass(frozen=True, slots=True)
class ScientificValue:
    value: float | int | str | bool
    unit: str | None
    status: EpistemicStatus
    source: SourceRef | None = None
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    domain: Domain = field(default_factory=Domain)

    def validate(self) -> list[str]:
        errors = self.uncertainty.validate() + self.domain.validate()
        if self.status is EpistemicStatus.ESTABLISHED and self.source is None:
            errors.append("established value requires provenance")
        if self.source is not None:
            errors.extend(self.source.validate())
        return errors


@dataclass(frozen=True, slots=True)
class GaugeCharge:
    group_id: str
    representation: str
    u1_charge: Fraction | None = None

    @classmethod
    def from_number(
        cls,
        group_id: str,
        representation: str,
        charge: int | float | str | Fraction | None = None,
    ) -> "GaugeCharge":
        parsed = None if charge is None else Fraction(str(charge))
        return cls(group_id=group_id, representation=representation, u1_charge=parsed)


@dataclass(frozen=True, slots=True)
class FieldSpec:
    id: str
    name: str
    kind: FieldKind
    lorentz_representation: str
    mass_dimension: Fraction
    ontology_level: OntologyLevel
    status: EpistemicStatus
    chirality: Chirality = Chirality.NONE
    gauge_charges: tuple[GaugeCharge, ...] = ()
    multiplicity: int = 1
    real_field: bool = False
    antiparticle_id: str | None = None
    source: SourceRef | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id or any(character.isspace() for character in self.id):
            errors.append("field id must be non-empty and contain no whitespace")
        if self.mass_dimension < 0:
            errors.append(f"field {self.id} has negative mass dimension")
        if self.multiplicity < 1:
            errors.append(f"field {self.id} multiplicity must be positive")
        groups = [charge.group_id for charge in self.gauge_charges]
        if len(groups) != len(set(groups)):
            errors.append(f"field {self.id} repeats a gauge group")
        if self.status is EpistemicStatus.ESTABLISHED and self.source is None:
            errors.append(f"established field {self.id} requires source")
        return errors

    def charge_for(self, group_id: str) -> Fraction:
        for charge in self.gauge_charges:
            if charge.group_id == group_id and charge.u1_charge is not None:
                return charge.u1_charge
        return Fraction(0)


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    id: str
    value: ScientificValue | None = None
    lower: float | None = None
    upper: float | None = None
    prior: str | None = None
    role: str = "free"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            errors.append(f"parameter {self.id} lower bound exceeds upper bound")
        if self.value is not None:
            errors.extend(self.value.validate())
            numeric = self.value.value
            if isinstance(numeric, (int, float)):
                if self.lower is not None and numeric < self.lower:
                    errors.append(f"parameter {self.id} is below its lower bound")
                if self.upper is not None and numeric > self.upper:
                    errors.append(f"parameter {self.id} is above its upper bound")
        return errors


@dataclass(frozen=True, slots=True)
class OperatorFactor:
    field_id: str
    multiplicity: int = 1
    conjugated: bool = False
    derivatives: int = 0
    tensor_role: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.multiplicity < 1:
            errors.append("operator factor multiplicity must be positive")
        if self.derivatives < 0:
            errors.append("operator factor derivative count must be non-negative")
        return errors


@dataclass(frozen=True, slots=True)
class OperatorSpec:
    id: str
    coefficient: str
    factors: tuple[OperatorFactor, ...]
    declared_dimension: Fraction | None = None
    hermitian: bool | None = None
    lorentz_scalar: bool | None = None
    status: EpistemicStatus = EpistemicStatus.HYPOTHETICAL
    tags: tuple[str, ...] = ()
    source: SourceRef | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("operator id is required")
        if not self.coefficient:
            errors.append(f"operator {self.id} coefficient is required")
        if not self.factors:
            errors.append(f"operator {self.id} requires at least one factor")
        for factor in self.factors:
            errors.extend(factor.validate())
        return errors


@dataclass(frozen=True, slots=True)
class FalsifierSpec:
    id: str
    statement: str
    observable: str | None = None
    threshold: str | None = None
    experiment: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("falsifier id is required")
        if not self.statement:
            errors.append(f"falsifier {self.id} statement is required")
        return errors


@dataclass(frozen=True, slots=True)
class TheorySpec:
    id: str
    name: str
    status: EpistemicStatus
    baseline: str | None
    gauge_groups: tuple[str, ...]
    fields: tuple[FieldSpec, ...]
    parameters: tuple[ParameterSpec, ...]
    operators: tuple[OperatorSpec, ...]
    falsifiers: tuple[FalsifierSpec, ...]
    domain: Domain = field(default_factory=Domain)
    source: SourceRef | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def field_map(self) -> dict[str, FieldSpec]:
        return {item.id: item for item in self.fields}

    def parameter_map(self) -> dict[str, ParameterSpec]:
        return {item.id: item for item in self.parameters}

    def validate_structure(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("theory id is required")
        for label, identifiers in (
            ("field", [item.id for item in self.fields]),
            ("parameter", [item.id for item in self.parameters]),
            ("operator", [item.id for item in self.operators]),
            ("falsifier", [item.id for item in self.falsifiers]),
        ):
            if len(identifiers) != len(set(identifiers)):
                errors.append(f"duplicate {label} identifiers")
        for item in self.fields:
            errors.extend(item.validate())
        for item in self.parameters:
            errors.extend(item.validate())
        for item in self.operators:
            errors.extend(item.validate())
        for item in self.falsifiers:
            errors.extend(item.validate())
        errors.extend(self.domain.validate())
        return errors


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    gate: str
    code: str
    severity: FindingSeverity
    message: str
    object_id: str | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    theory_id: str
    findings: tuple[ValidationFinding, ...]
    gate_results: Mapping[str, bool]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(self.gate_results.values()) and not any(
            finding.severity in {FindingSeverity.ERROR, FindingSeverity.FATAL}
            for finding in self.findings
        )

    def by_gate(self, gate: str) -> tuple[ValidationFinding, ...]:
        return tuple(finding for finding in self.findings if finding.gate == gate)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json_ready(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _json_ready(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def scientific_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def unique_by_id(items: Iterable[Any]) -> bool:
    identifiers = [item.id for item in items]
    return len(identifiers) == len(set(identifiers))
