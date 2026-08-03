"""Mathematical type system for Ω-VLA-T∞³ R0.3-OMEGA.

The implementation is intentionally conservative: it rejects ambiguous or
incompatible operations rather than silently coercing them.  It models finite
shapes and unit dimensions; it does not claim to formalize every mathematical
structure used in analysis or geometry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from fractions import Fraction
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


class TypeSystemError(ValueError):
    """Raised when a mathematical type relation is invalid or undecidable."""


class ScalarSystem(str, Enum):
    BOOLEAN = "B"
    NATURAL = "N"
    INTEGER = "Z"
    RATIONAL = "Q"
    REAL = "R"
    COMPLEX = "C"
    QUATERNION = "H"
    OCTONION = "O"
    SEDENION = "S"
    FINITE_FIELD = "GF"
    INTERVAL_REAL = "IR"


_SCALAR_EMBEDDING_RANK: dict[ScalarSystem, int] = {
    ScalarSystem.BOOLEAN: 0,
    ScalarSystem.NATURAL: 1,
    ScalarSystem.INTEGER: 2,
    ScalarSystem.RATIONAL: 3,
    ScalarSystem.REAL: 4,
    ScalarSystem.COMPLEX: 5,
}


class StructureKind(str, Enum):
    SCALAR = "scalar"
    VECTOR = "vector"
    COVECTOR = "covector"
    MATRIX = "matrix"
    TENSOR = "tensor"
    LINEAR_OPERATOR = "linear_operator"
    AFFINE_OPERATOR = "affine_operator"
    NONLINEAR_MAP = "nonlinear_map"
    FIELD = "field"
    DIFFERENTIAL_FORM = "differential_form"
    MANIFOLD = "manifold"
    GRAPH = "graph"
    CHAIN_COMPLEX = "chain_complex"
    EQUATION = "equation"
    PROPOSITION = "proposition"
    PROOF_TARGET = "proof_target"
    RESIDUAL = "residual"


class Variance(str, Enum):
    INVARIANT = "invariant"
    CONTRAVARIANT = "contravariant"
    COVARIANT = "covariant"
    MIXED = "mixed"
    NOT_APPLICABLE = "not_applicable"


class Regularity(str, Enum):
    UNKNOWN = "unknown"
    DISCRETE = "discrete"
    MEASURABLE = "measurable"
    L2 = "L2"
    SOBOLEV_H1 = "H1"
    CONTINUOUS = "C0"
    C1 = "C1"
    C2 = "C2"
    SMOOTH = "Cinf"
    ANALYTIC = "analytic"


_REGULARITY_RANK: dict[Regularity, int] = {
    Regularity.UNKNOWN: -1,
    Regularity.DISCRETE: 0,
    Regularity.MEASURABLE: 1,
    Regularity.L2: 2,
    Regularity.SOBOLEV_H1: 3,
    Regularity.CONTINUOUS: 4,
    Regularity.C1: 5,
    Regularity.C2: 6,
    Regularity.SMOOTH: 7,
    Regularity.ANALYTIC: 8,
}


@dataclass(frozen=True, order=True)
class Dimension:
    """One finite or symbolic dimension."""

    value: int | str

    def __post_init__(self) -> None:
        if isinstance(self.value, int):
            if self.value < 0:
                raise TypeSystemError("finite dimensions cannot be negative")
        elif not self.value.strip():
            raise TypeSystemError("symbolic dimensions cannot be empty")

    @property
    def concrete(self) -> bool:
        return isinstance(self.value, int)

    def compatible_with(self, other: "Dimension") -> bool:
        return self.value == other.value

    def multiply(self, other: "Dimension") -> "Dimension":
        if self.concrete and other.concrete:
            return Dimension(int(self.value) * int(other.value))
        return Dimension(f"({self.value}*{other.value})")

    def to_json_value(self) -> int | str:
        return self.value


@dataclass(frozen=True)
class Shape:
    """Tensor shape.  Scalars have rank zero and shape ()."""

    dimensions: tuple[Dimension, ...] = ()

    @classmethod
    def of(cls, *dimensions: int | str | Dimension) -> "Shape":
        return cls(tuple(d if isinstance(d, Dimension) else Dimension(d) for d in dimensions))

    @property
    def rank(self) -> int:
        return len(self.dimensions)

    @property
    def scalar(self) -> bool:
        return not self.dimensions

    @property
    def concrete_size(self) -> int | None:
        result = 1
        for dimension in self.dimensions:
            if not dimension.concrete:
                return None
            result *= int(dimension.value)
        return result

    def compatible_with(self, other: "Shape") -> bool:
        return self.dimensions == other.dimensions

    def tensor(self, other: "Shape") -> "Shape":
        return Shape(self.dimensions + other.dimensions)

    def matrix_domain(self) -> Dimension:
        if self.rank != 2:
            raise TypeSystemError("a matrix shape must have rank two")
        return self.dimensions[1]

    def matrix_codomain(self) -> Dimension:
        if self.rank != 2:
            raise TypeSystemError("a matrix shape must have rank two")
        return self.dimensions[0]

    def to_dict(self) -> list[int | str]:
        return [dimension.to_json_value() for dimension in self.dimensions]


_BASE_UNITS = ("L", "M", "T", "I", "Theta", "N", "J")


@dataclass(frozen=True)
class UnitDimension:
    """SI base-dimension exponents using exact rational arithmetic.

    Order: length, mass, time, electric current, temperature, amount, luminous
    intensity.  Scale factors are deliberately excluded; this object checks
    dimensions, not unit conversion.
    """

    exponents: tuple[Fraction, ...] = (Fraction(0),) * 7

    def __post_init__(self) -> None:
        normalized = tuple(Fraction(value) for value in self.exponents)
        if len(normalized) != 7:
            raise TypeSystemError("unit dimensions require seven SI exponents")
        object.__setattr__(self, "exponents", normalized)

    @classmethod
    def dimensionless(cls) -> "UnitDimension":
        return cls()

    @classmethod
    def base(cls, symbol: str) -> "UnitDimension":
        try:
            index = _BASE_UNITS.index(symbol)
        except ValueError as exc:
            raise TypeSystemError(f"unknown SI base dimension: {symbol}") from exc
        values = [Fraction(0)] * 7
        values[index] = Fraction(1)
        return cls(tuple(values))

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, int | float | str | Fraction]) -> "UnitDimension":
        values = [Fraction(0)] * 7
        for symbol, exponent in mapping.items():
            try:
                index = _BASE_UNITS.index(symbol)
            except ValueError as exc:
                raise TypeSystemError(f"unknown SI base dimension: {symbol}") from exc
            values[index] = Fraction(exponent)
        return cls(tuple(values))

    def __mul__(self, other: "UnitDimension") -> "UnitDimension":
        return UnitDimension(tuple(a + b for a, b in zip(self.exponents, other.exponents)))

    def __truediv__(self, other: "UnitDimension") -> "UnitDimension":
        return UnitDimension(tuple(a - b for a, b in zip(self.exponents, other.exponents)))

    def power(self, exponent: int | Fraction) -> "UnitDimension":
        factor = Fraction(exponent)
        return UnitDimension(tuple(factor * value for value in self.exponents))

    @property
    def is_dimensionless(self) -> bool:
        return all(value == 0 for value in self.exponents)

    def to_dict(self) -> dict[str, str]:
        return {
            symbol: str(exponent)
            for symbol, exponent in zip(_BASE_UNITS, self.exponents)
            if exponent != 0
        }

    def __str__(self) -> str:
        if self.is_dimensionless:
            return "1"
        return " ".join(
            symbol if exponent == 1 else f"{symbol}^{exponent}"
            for symbol, exponent in zip(_BASE_UNITS, self.exponents)
            if exponent != 0
        )


@dataclass(frozen=True)
class UncertaintySpec:
    model: str = "none"
    parameters: tuple[tuple[str, str], ...] = ()

    @classmethod
    def covariance(cls, reference: str) -> "UncertaintySpec":
        return cls("covariance", (("reference", reference),))

    def to_dict(self) -> dict[str, Any]:
        return {"model": self.model, "parameters": dict(self.parameters)}


@dataclass(frozen=True)
class MathType:
    """A serializable conservative type for VLA-IR nodes."""

    structure: StructureKind
    scalar_system: ScalarSystem = ScalarSystem.REAL
    shape: Shape = field(default_factory=Shape)
    units: UnitDimension = field(default_factory=UnitDimension.dimensionless)
    variance: tuple[Variance, ...] = ()
    regularity: Regularity = Regularity.UNKNOWN
    support: str = "global"
    uncertainty: UncertaintySpec = field(default_factory=UncertaintySpec)
    domain_id: str | None = None
    codomain_id: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.variance and len(self.variance) != self.shape.rank:
            raise TypeSystemError("variance annotations must match tensor rank")
        if self.structure == StructureKind.SCALAR and not self.shape.scalar:
            raise TypeSystemError("scalar types must have rank-zero shape")
        if self.structure in {StructureKind.MATRIX, StructureKind.LINEAR_OPERATOR} and self.shape.rank != 2:
            raise TypeSystemError("matrix and finite linear-operator types require rank-two shape")
        if self.structure == StructureKind.VECTOR and self.shape.rank != 1:
            raise TypeSystemError("vector types require rank-one shape")
        if self.structure == StructureKind.COVECTOR and self.shape.rank != 1:
            raise TypeSystemError("covector types require rank-one shape")
        if not self.support.strip():
            raise TypeSystemError("support cannot be empty")

    @classmethod
    def scalar(cls, scalar_system: ScalarSystem = ScalarSystem.REAL, units: UnitDimension | None = None) -> "MathType":
        return cls(
            structure=StructureKind.SCALAR,
            scalar_system=scalar_system,
            units=units or UnitDimension.dimensionless(),
        )

    @classmethod
    def vector(
        cls,
        dimension: int | str,
        *,
        scalar_system: ScalarSystem = ScalarSystem.REAL,
        units: UnitDimension | None = None,
        variance: Variance = Variance.CONTRAVARIANT,
        space_id: str | None = None,
    ) -> "MathType":
        return cls(
            structure=StructureKind.VECTOR,
            scalar_system=scalar_system,
            shape=Shape.of(dimension),
            units=units or UnitDimension.dimensionless(),
            variance=(variance,),
            codomain_id=space_id,
        )

    @classmethod
    def linear_operator(
        cls,
        codomain_dimension: int | str,
        domain_dimension: int | str,
        *,
        scalar_system: ScalarSystem = ScalarSystem.REAL,
        units: UnitDimension | None = None,
        domain_id: str | None = None,
        codomain_id: str | None = None,
    ) -> "MathType":
        return cls(
            structure=StructureKind.LINEAR_OPERATOR,
            scalar_system=scalar_system,
            shape=Shape.of(codomain_dimension, domain_dimension),
            units=units or UnitDimension.dimensionless(),
            variance=(Variance.CONTRAVARIANT, Variance.COVARIANT),
            domain_id=domain_id,
            codomain_id=codomain_id,
        )

    @property
    def rank(self) -> int:
        return self.shape.rank

    def require_same_additive_type(self, other: "MathType") -> None:
        if self.structure != other.structure:
            raise TypeSystemError(f"cannot add {self.structure.value} and {other.structure.value}")
        if not self.shape.compatible_with(other.shape):
            raise TypeSystemError(f"shape mismatch for addition: {self.shape} vs {other.shape}")
        if self.units != other.units:
            raise TypeSystemError(f"unit mismatch for addition: {self.units} vs {other.units}")
        common_scalar_system(self.scalar_system, other.scalar_system)
        if self.domain_id != other.domain_id or self.codomain_id != other.codomain_id:
            raise TypeSystemError("domain/codomain identities differ for addition")

    def additive_result(self, other: "MathType") -> "MathType":
        self.require_same_additive_type(other)
        return self.with_scalar(common_scalar_system(self.scalar_system, other.scalar_system))

    def compose_result(self, inner: "MathType") -> "MathType":
        if self.structure != StructureKind.LINEAR_OPERATOR or inner.structure != StructureKind.LINEAR_OPERATOR:
            raise TypeSystemError("composition currently requires two finite linear operators")
        if not self.shape.matrix_domain().compatible_with(inner.shape.matrix_codomain()):
            raise TypeSystemError("operator composition has incompatible finite dimensions")
        if self.domain_id is not None and inner.codomain_id is not None and self.domain_id != inner.codomain_id:
            raise TypeSystemError("operator composition has incompatible named spaces")
        scalar = common_scalar_system(self.scalar_system, inner.scalar_system)
        return MathType.linear_operator(
            self.shape.matrix_codomain().value,
            inner.shape.matrix_domain().value,
            scalar_system=scalar,
            units=self.units * inner.units,
            domain_id=inner.domain_id,
            codomain_id=self.codomain_id,
        )

    def adjoint_result(self) -> "MathType":
        if self.structure != StructureKind.LINEAR_OPERATOR:
            raise TypeSystemError("adjoint currently requires a finite linear operator")
        return MathType.linear_operator(
            self.shape.matrix_domain().value,
            self.shape.matrix_codomain().value,
            scalar_system=self.scalar_system,
            units=self.units,
            domain_id=self.codomain_id,
            codomain_id=self.domain_id,
        )

    def tensor_result(self, other: "MathType") -> "MathType":
        scalar = common_scalar_system(self.scalar_system, other.scalar_system)
        if self.structure == StructureKind.LINEAR_OPERATOR and other.structure == StructureKind.LINEAR_OPERATOR:
            return MathType.linear_operator(
                self.shape.matrix_codomain().multiply(other.shape.matrix_codomain()).value,
                self.shape.matrix_domain().multiply(other.shape.matrix_domain()).value,
                scalar_system=scalar,
                units=self.units * other.units,
                domain_id=_combined_space_id(self.domain_id, other.domain_id, "tensor"),
                codomain_id=_combined_space_id(self.codomain_id, other.codomain_id, "tensor"),
            )
        return MathType(
            structure=StructureKind.TENSOR,
            scalar_system=scalar,
            shape=self.shape.tensor(other.shape),
            units=self.units * other.units,
            variance=self.variance + other.variance,
            regularity=min_regularity(self.regularity, other.regularity),
            support=f"({self.support})x({other.support})",
            uncertainty=UncertaintySpec("composed"),
        )

    def with_scalar(self, scalar_system: ScalarSystem) -> "MathType":
        data = self.to_dict()
        data["scalar_system"] = scalar_system.value
        return math_type_from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure": self.structure.value,
            "scalar_system": self.scalar_system.value,
            "shape": self.shape.to_dict(),
            "units": self.units.to_dict(),
            "variance": [value.value for value in self.variance],
            "regularity": self.regularity.value,
            "support": self.support,
            "uncertainty": self.uncertainty.to_dict(),
            "domain_id": self.domain_id,
            "codomain_id": self.codomain_id,
            "tags": list(self.tags),
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _combined_space_id(left: str | None, right: str | None, operation: str) -> str | None:
    if left is None and right is None:
        return None
    return f"{operation}({left or '?'},{right or '?'})"


def common_scalar_system(left: ScalarSystem, right: ScalarSystem) -> ScalarSystem:
    if left == right:
        return left
    if left in _SCALAR_EMBEDDING_RANK and right in _SCALAR_EMBEDDING_RANK:
        return max((left, right), key=lambda value: _SCALAR_EMBEDDING_RANK[value])
    raise TypeSystemError(
        f"no implicit scalar embedding declared between {left.value} and {right.value}"
    )


def min_regularity(left: Regularity, right: Regularity) -> Regularity:
    return min((left, right), key=lambda value: _REGULARITY_RANK[value])


def math_type_from_dict(payload: Mapping[str, Any]) -> MathType:
    uncertainty_payload = payload.get("uncertainty", {"model": "none", "parameters": {}})
    parameters = tuple(sorted((str(k), str(v)) for k, v in uncertainty_payload.get("parameters", {}).items()))
    return MathType(
        structure=StructureKind(payload["structure"]),
        scalar_system=ScalarSystem(payload.get("scalar_system", "R")),
        shape=Shape.of(*payload.get("shape", [])),
        units=UnitDimension.from_mapping(payload.get("units", {})),
        variance=tuple(Variance(value) for value in payload.get("variance", [])),
        regularity=Regularity(payload.get("regularity", "unknown")),
        support=str(payload.get("support", "global")),
        uncertainty=UncertaintySpec(str(uncertainty_payload.get("model", "none")), parameters),
        domain_id=payload.get("domain_id"),
        codomain_id=payload.get("codomain_id"),
        tags=tuple(str(value) for value in payload.get("tags", [])),
    )


def assert_unique_type_ids(types: Iterable[tuple[str, MathType]]) -> None:
    seen: set[str] = set()
    for identifier, _ in types:
        if identifier in seen:
            raise TypeSystemError(f"duplicate type identifier: {identifier}")
        seen.add(identifier)
