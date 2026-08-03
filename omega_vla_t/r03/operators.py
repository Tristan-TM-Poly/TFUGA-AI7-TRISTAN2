"""Typed operator-expression universe for Ω-VLA-T∞³.

The grammar separates symbolic construction, type inference, simplification and
numerical evaluation. Generated expressions are software objects, not claims
that every formal operator exists on arbitrary infinite-dimensional spaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence

from .types import (
    MathType,
    ScalarSystem,
    StructureKind,
    TypeSystemError,
    UnitDimension,
    common_scalar_system,
)


class OperatorError(ValueError):
    pass


class OperatorKind(str, Enum):
    SYMBOL = "symbol"
    IDENTITY = "identity"
    ZERO = "zero"
    MATRIX_LITERAL = "matrix_literal"
    SUM = "sum"
    DIFFERENCE = "difference"
    COMPOSE = "compose"
    SCALAR_MULTIPLY = "scalar_multiply"
    ADJOINT = "adjoint"
    TRANSPOSE = "transpose"
    CONJUGATE = "conjugate"
    INVERSE = "inverse"
    PSEUDOINVERSE = "pseudoinverse"
    POWER = "power"
    EXPONENTIAL = "exponential"
    LOGARITHM = "logarithm"
    COMMUTATOR = "commutator"
    ANTICOMMUTATOR = "anticommutator"
    TENSOR_PRODUCT = "tensor_product"
    DIRECT_SUM = "direct_sum"
    KRONECKER_SUM = "kronecker_sum"
    LOW_RANK_UPDATE = "low_rank_update"
    PROJECTION = "projection"
    DERIVATIVE = "derivative"
    MULTIPLICATION = "multiplication"
    TRANSLATION = "translation"
    RESTRICTION = "restriction"
    EXTENSION = "extension"


@dataclass(frozen=True)
class OperatorProperty:
    name: str
    status: str = "declared"
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        allowed = {"declared", "tested", "proved", "refuted", "unknown"}
        if self.status not in allowed:
            raise OperatorError(f"invalid property status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "evidence": list(self.evidence)}


@dataclass(frozen=True)
class OperatorExpr:
    kind: OperatorKind
    operands: tuple["OperatorExpr", ...] = ()
    name: str = ""
    declared_type: MathType | None = None
    scalar_value: complex | float | int | None = None
    matrix_value: tuple[tuple[complex | float | int, ...], ...] = ()
    exponent: int | None = None
    attributes: tuple[tuple[str, Any], ...] = ()
    properties: tuple[OperatorProperty, ...] = ()

    def __post_init__(self) -> None:
        _validate_arity(self.kind, len(self.operands))
        if self.kind == OperatorKind.SYMBOL and (not self.name or self.declared_type is None):
            raise OperatorError("symbol operators require a name and declared type")
        if self.kind in {OperatorKind.IDENTITY, OperatorKind.ZERO} and self.declared_type is None:
            raise OperatorError(f"{self.kind.value} requires a declared type")
        if self.kind == OperatorKind.MATRIX_LITERAL:
            if not self.matrix_value or self.declared_type is None:
                raise OperatorError("matrix literals require values and a declared type")
            width = len(self.matrix_value[0])
            if width == 0 or any(len(row) != width for row in self.matrix_value):
                raise OperatorError("matrix literal must be rectangular and non-empty")
            if self.declared_type.shape.to_dict() != [len(self.matrix_value), width]:
                raise OperatorError("matrix literal shape disagrees with declared type")
        if self.kind == OperatorKind.SCALAR_MULTIPLY and self.scalar_value is None:
            raise OperatorError("scalar multiplication requires scalar_value")
        if self.kind == OperatorKind.POWER and self.exponent is None:
            raise OperatorError("power requires an integer exponent")
        keys = [key for key, _ in self.attributes]
        if len(keys) != len(set(keys)):
            raise OperatorError("operator attributes must have unique keys")

    @classmethod
    def symbol(
        cls,
        name: str,
        math_type: MathType,
        *,
        properties: Iterable[str] = (),
    ) -> "OperatorExpr":
        return cls(
            kind=OperatorKind.SYMBOL,
            name=name,
            declared_type=math_type,
            properties=tuple(
                OperatorProperty(value) for value in sorted(set(properties))
            ),
        )

    @classmethod
    def identity(cls, math_type: MathType, *, name: str = "I") -> "OperatorExpr":
        _require_square_operator(math_type)
        return cls(
            OperatorKind.IDENTITY,
            name=name,
            declared_type=math_type,
            properties=(OperatorProperty("identity", "proved"),),
        )

    @classmethod
    def zero(cls, math_type: MathType, *, name: str = "0") -> "OperatorExpr":
        return cls(
            OperatorKind.ZERO,
            name=name,
            declared_type=math_type,
            properties=(OperatorProperty("zero", "proved"),),
        )

    @classmethod
    def matrix(
        cls,
        values: Sequence[Sequence[complex | float | int]],
        *,
        name: str = "",
        scalar_system: ScalarSystem = ScalarSystem.REAL,
        domain_id: str | None = None,
        codomain_id: str | None = None,
        units: UnitDimension | None = None,
    ) -> "OperatorExpr":
        rows = tuple(tuple(value for value in row) for row in values)
        if not rows or not rows[0]:
            raise OperatorError("matrix literal cannot be empty")
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise OperatorError("matrix literal rows must have equal length")
        math_type = MathType.linear_operator(
            len(rows),
            width,
            scalar_system=scalar_system,
            units=units,
            domain_id=domain_id,
            codomain_id=codomain_id,
        )
        return cls(
            OperatorKind.MATRIX_LITERAL,
            name=name,
            declared_type=math_type,
            matrix_value=rows,
        )

    @classmethod
    def unary(
        cls,
        kind: OperatorKind,
        operand: "OperatorExpr",
        **kwargs: Any,
    ) -> "OperatorExpr":
        return cls(kind=kind, operands=(operand,), **kwargs)

    @classmethod
    def binary(
        cls,
        kind: OperatorKind,
        left: "OperatorExpr",
        right: "OperatorExpr",
        **kwargs: Any,
    ) -> "OperatorExpr":
        return cls(kind=kind, operands=(left, right), **kwargs)

    @classmethod
    def nary(
        cls,
        kind: OperatorKind,
        operands: Iterable["OperatorExpr"],
        **kwargs: Any,
    ) -> "OperatorExpr":
        return cls(kind=kind, operands=tuple(operands), **kwargs)

    def attribute_map(self) -> dict[str, Any]:
        return dict(self.attributes)

    def infer_type(self) -> MathType:
        if self.kind in {
            OperatorKind.SYMBOL,
            OperatorKind.IDENTITY,
            OperatorKind.ZERO,
            OperatorKind.MATRIX_LITERAL,
        }:
            assert self.declared_type is not None
            return self.declared_type

        if self.kind in {OperatorKind.SUM, OperatorKind.DIFFERENCE}:
            result = self.operands[0].infer_type()
            for operand in self.operands[1:]:
                result = result.additive_result(operand.infer_type())
            return result

        if self.kind == OperatorKind.COMPOSE:
            result = self.operands[-1].infer_type()
            for outer in reversed(self.operands[:-1]):
                result = outer.infer_type().compose_result(result)
            return result

        if self.kind == OperatorKind.SCALAR_MULTIPLY:
            return self.operands[0].infer_type()

        if self.kind in {OperatorKind.ADJOINT, OperatorKind.TRANSPOSE}:
            return self.operands[0].infer_type().adjoint_result()

        if self.kind == OperatorKind.CONJUGATE:
            return self.operands[0].infer_type()

        if self.kind in {OperatorKind.INVERSE, OperatorKind.PSEUDOINVERSE}:
            operand_type = self.operands[0].infer_type()
            _require_square_operator(operand_type)
            result = operand_type.adjoint_result()
            return MathType.linear_operator(
                result.shape.matrix_codomain().value,
                result.shape.matrix_domain().value,
                scalar_system=result.scalar_system,
                units=operand_type.units.power(-1),
                domain_id=result.domain_id,
                codomain_id=result.codomain_id,
            )

        if self.kind == OperatorKind.POWER:
            operand_type = self.operands[0].infer_type()
            _require_square_operator(operand_type)
            assert self.exponent is not None
            return MathType.linear_operator(
                operand_type.shape.matrix_codomain().value,
                operand_type.shape.matrix_domain().value,
                scalar_system=operand_type.scalar_system,
                units=operand_type.units.power(self.exponent),
                domain_id=operand_type.domain_id,
                codomain_id=operand_type.codomain_id,
            )

        if self.kind in {OperatorKind.EXPONENTIAL, OperatorKind.LOGARITHM}:
            operand_type = self.operands[0].infer_type()
            _require_square_operator(operand_type)
            if not operand_type.units.is_dimensionless:
                raise TypeSystemError(
                    f"{self.kind.value} requires a dimensionless operator"
                )
            return operand_type

        if self.kind in {OperatorKind.COMMUTATOR, OperatorKind.ANTICOMMUTATOR}:
            left = self.operands[0].infer_type()
            right = self.operands[1].infer_type()
            left.require_same_additive_type(right)
            _require_square_operator(left)
            return left.compose_result(right)

        if self.kind == OperatorKind.TENSOR_PRODUCT:
            result = self.operands[0].infer_type()
            for operand in self.operands[1:]:
                result = result.tensor_result(operand.infer_type())
            return result

        if self.kind == OperatorKind.DIRECT_SUM:
            types = [operand.infer_type() for operand in self.operands]
            if any(value.structure != StructureKind.LINEAR_OPERATOR for value in types):
                raise TypeSystemError("direct sum requires linear operators")
            scalar = types[0].scalar_system
            for value in types[1:]:
                scalar = common_scalar_system(scalar, value.scalar_system)
            codomain = _dimension_sum(
                [value.shape.matrix_codomain().value for value in types]
            )
            domain = _dimension_sum(
                [value.shape.matrix_domain().value for value in types]
            )
            units = types[0].units
            if any(value.units != units for value in types[1:]):
                raise TypeSystemError(
                    "direct-sum blocks must share operator units"
                )
            return MathType.linear_operator(
                codomain,
                domain,
                scalar_system=scalar,
                units=units,
            )

        if self.kind == OperatorKind.KRONECKER_SUM:
            left = self.operands[0].infer_type()
            right = self.operands[1].infer_type()
            _require_square_operator(left)
            _require_square_operator(right)
            if left.units != right.units:
                raise TypeSystemError(
                    "Kronecker-sum operands must share units"
                )
            scalar = common_scalar_system(
                left.scalar_system,
                right.scalar_system,
            )
            dimension = left.shape.matrix_codomain().multiply(
                right.shape.matrix_codomain()
            ).value
            return MathType.linear_operator(
                dimension,
                dimension,
                scalar_system=scalar,
                units=left.units,
                domain_id=_combined_space_id(
                    left.domain_id,
                    right.domain_id,
                    "tensor",
                ),
                codomain_id=_combined_space_id(
                    left.codomain_id,
                    right.codomain_id,
                    "tensor",
                ),
            )

        if self.kind == OperatorKind.LOW_RANK_UPDATE:
            base, update = (operand.infer_type() for operand in self.operands)
            return base.additive_result(update)

        if self.declared_type is not None:
            return self.declared_type

        raise TypeSystemError(
            f"type inference is not implemented for {self.kind.value}"
        )

    def depth(self) -> int:
        return 1 if not self.operands else 1 + max(
            operand.depth() for operand in self.operands
        )

    def node_count(self) -> int:
        return 1 + sum(operand.node_count() for operand in self.operands)

    def symbols(self) -> tuple[str, ...]:
        result: set[str] = set()
        if self.kind == OperatorKind.SYMBOL:
            result.add(self.name)
        for operand in self.operands:
            result.update(operand.symbols())
        return tuple(sorted(result))

    def has_property(
        self,
        name: str,
        *,
        minimum_status: str | None = None,
    ) -> bool:
        ranking = {
            "unknown": 0,
            "declared": 1,
            "tested": 2,
            "proved": 3,
            "refuted": -1,
        }
        for prop in self.properties:
            if prop.name == name:
                return minimum_status is None or (
                    ranking[prop.status] >= ranking[minimum_status]
                )
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "name": self.name,
            "declared_type": None
            if self.declared_type is None
            else self.declared_type.to_dict(),
            "scalar_value": _json_scalar(self.scalar_value),
            "matrix_value": [
                [_json_scalar(value) for value in row]
                for row in self.matrix_value
            ],
            "exponent": self.exponent,
            "attributes": self.attribute_map(),
            "properties": [value.to_dict() for value in self.properties],
            "operands": [operand.to_dict() for operand in self.operands],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    def digest(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def simplify(self, *, max_passes: int = 32) -> "OperatorExpr":
        expression = self
        for _ in range(max_passes):
            candidate = _simplify_once(expression)
            if candidate == expression:
                return candidate
            expression = candidate
        raise OperatorError(
            "simplification did not converge within max_passes"
        )

    def __add__(self, other: "OperatorExpr") -> "OperatorExpr":
        return OperatorExpr.binary(OperatorKind.SUM, self, other)

    def __sub__(self, other: "OperatorExpr") -> "OperatorExpr":
        return OperatorExpr.binary(OperatorKind.DIFFERENCE, self, other)

    def __matmul__(self, other: "OperatorExpr") -> "OperatorExpr":
        return OperatorExpr.binary(OperatorKind.COMPOSE, self, other)

    def scale(self, scalar: complex | float | int) -> "OperatorExpr":
        return OperatorExpr.unary(
            OperatorKind.SCALAR_MULTIPLY,
            self,
            scalar_value=scalar,
        )

    def adjoint(self) -> "OperatorExpr":
        return OperatorExpr.unary(OperatorKind.ADJOINT, self)

    def tensor(self, other: "OperatorExpr") -> "OperatorExpr":
        return OperatorExpr.binary(
            OperatorKind.TENSOR_PRODUCT,
            self,
            other,
        )

    def commutator(self, other: "OperatorExpr") -> "OperatorExpr":
        return OperatorExpr.binary(
            OperatorKind.COMMUTATOR,
            self,
            other,
        )

    def anticommutator(self, other: "OperatorExpr") -> "OperatorExpr":
        return OperatorExpr.binary(
            OperatorKind.ANTICOMMUTATOR,
            self,
            other,
        )


def _json_scalar(value: Any) -> Any:
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def _validate_arity(kind: OperatorKind, arity: int) -> None:
    zero = {
        OperatorKind.SYMBOL,
        OperatorKind.IDENTITY,
        OperatorKind.ZERO,
        OperatorKind.MATRIX_LITERAL,
    }
    unary = {
        OperatorKind.SCALAR_MULTIPLY,
        OperatorKind.ADJOINT,
        OperatorKind.TRANSPOSE,
        OperatorKind.CONJUGATE,
        OperatorKind.INVERSE,
        OperatorKind.PSEUDOINVERSE,
        OperatorKind.POWER,
        OperatorKind.EXPONENTIAL,
        OperatorKind.LOGARITHM,
        OperatorKind.PROJECTION,
        OperatorKind.DERIVATIVE,
        OperatorKind.MULTIPLICATION,
        OperatorKind.TRANSLATION,
        OperatorKind.RESTRICTION,
        OperatorKind.EXTENSION,
    }
    binary = {
        OperatorKind.DIFFERENCE,
        OperatorKind.COMMUTATOR,
        OperatorKind.ANTICOMMUTATOR,
        OperatorKind.KRONECKER_SUM,
        OperatorKind.LOW_RANK_UPDATE,
    }
    nary = {
        OperatorKind.SUM,
        OperatorKind.COMPOSE,
        OperatorKind.TENSOR_PRODUCT,
        OperatorKind.DIRECT_SUM,
    }
    if kind in zero and arity != 0:
        raise OperatorError(f"{kind.value} requires zero operands")
    if kind in unary and arity != 1:
        raise OperatorError(f"{kind.value} requires one operand")
    if kind in binary and arity != 2:
        raise OperatorError(f"{kind.value} requires two operands")
    if kind in nary and arity < 2:
        raise OperatorError(f"{kind.value} requires at least two operands")


def _require_square_operator(math_type: MathType) -> None:
    if math_type.structure != StructureKind.LINEAR_OPERATOR:
        raise TypeSystemError(
            "operation requires a finite linear operator"
        )
    if not math_type.shape.matrix_codomain().compatible_with(
        math_type.shape.matrix_domain()
    ):
        raise TypeSystemError("operation requires a square operator")
    if (
        math_type.domain_id is not None
        and math_type.codomain_id is not None
        and math_type.domain_id != math_type.codomain_id
    ):
        raise TypeSystemError(
            "operation requires matching named domain and codomain"
        )


def _combined_space_id(
    left: str | None,
    right: str | None,
    operation: str,
) -> str | None:
    if left is None and right is None:
        return None
    return f"{operation}({left or '?'},{right or '?'})"


def _dimension_sum(values: Sequence[int | str]) -> int | str:
    if all(isinstance(value, int) for value in values):
        return sum(int(value) for value in values)
    return "(" + "+".join(str(value) for value in values) + ")"


def _flatten(
    kind: OperatorKind,
    operands: Iterable[OperatorExpr],
) -> tuple[OperatorExpr, ...]:
    result: list[OperatorExpr] = []
    for operand in operands:
        if operand.kind == kind:
            result.extend(operand.operands)
        else:
            result.append(operand)
    return tuple(result)


def _rebuild(
    expression: OperatorExpr,
    operands: tuple[OperatorExpr, ...],
) -> OperatorExpr:
    return OperatorExpr(
        kind=expression.kind,
        operands=operands,
        name=expression.name,
        declared_type=expression.declared_type,
        scalar_value=expression.scalar_value,
        matrix_value=expression.matrix_value,
        exponent=expression.exponent,
        attributes=expression.attributes,
        properties=expression.properties,
    )


def _simplify_once(expression: OperatorExpr) -> OperatorExpr:
    if not expression.operands:
        return expression

    operands = tuple(
        operand.simplify(max_passes=8)
        for operand in expression.operands
    )
    current = _rebuild(expression, operands)

    if current.kind == OperatorKind.ADJOINT:
        operand = operands[0]
        if operand.kind == OperatorKind.ADJOINT:
            return operand.operands[0]
        if operand.kind == OperatorKind.IDENTITY:
            return operand
        if operand.kind == OperatorKind.ZERO:
            return OperatorExpr.zero(
                operand.infer_type().adjoint_result()
            )
        if operand.kind == OperatorKind.COMPOSE:
            return OperatorExpr.nary(
                OperatorKind.COMPOSE,
                tuple(
                    value.adjoint()
                    for value in reversed(operand.operands)
                ),
            )
        if operand.kind in {
            OperatorKind.SUM,
            OperatorKind.DIFFERENCE,
        }:
            return OperatorExpr(
                kind=operand.kind,
                operands=tuple(
                    value.adjoint()
                    for value in operand.operands
                ),
            )
        if operand.kind == OperatorKind.SCALAR_MULTIPLY:
            scalar = complex(operand.scalar_value).conjugate()
            if scalar.imag == 0:
                scalar = scalar.real
            return operand.operands[0].adjoint().scale(scalar)

    if current.kind == OperatorKind.COMPOSE:
        flat = list(_flatten(OperatorKind.COMPOSE, operands))
        if any(value.kind == OperatorKind.ZERO for value in flat):
            return OperatorExpr.zero(current.infer_type())
        flat = [
            value
            for value in flat
            if value.kind != OperatorKind.IDENTITY
        ]
        if not flat:
            return OperatorExpr.identity(current.infer_type())
        if len(flat) == 1:
            return flat[0]
        return OperatorExpr.nary(OperatorKind.COMPOSE, flat)

    if current.kind == OperatorKind.SUM:
        flat = list(_flatten(OperatorKind.SUM, operands))
        original_type = current.infer_type()
        flat = [
            value
            for value in flat
            if value.kind != OperatorKind.ZERO
        ]
        if not flat:
            return OperatorExpr.zero(original_type)
        if len(flat) == 1:
            return flat[0]
        flat.sort(key=lambda value: value.digest())
        return OperatorExpr.nary(OperatorKind.SUM, flat)

    if current.kind == OperatorKind.DIFFERENCE:
        left, right = operands
        if right.kind == OperatorKind.ZERO:
            return left
        if left == right:
            return OperatorExpr.zero(left.infer_type())

    if current.kind == OperatorKind.SCALAR_MULTIPLY:
        operand = operands[0]
        scalar = current.scalar_value
        assert scalar is not None
        if scalar == 0:
            return OperatorExpr.zero(operand.infer_type())
        if scalar == 1:
            return operand
        if operand.kind == OperatorKind.SCALAR_MULTIPLY:
            return operand.operands[0].scale(
                scalar * operand.scalar_value
            )

    if current.kind == OperatorKind.COMMUTATOR:
        left, right = operands
        if left == right:
            return OperatorExpr.zero(left.infer_type())
        if (
            left.kind == OperatorKind.IDENTITY
            or right.kind == OperatorKind.IDENTITY
        ):
            return OperatorExpr.zero(left.infer_type())

    if current.kind == OperatorKind.ANTICOMMUTATOR:
        left, right = operands
        if (
            left.kind == OperatorKind.ZERO
            or right.kind == OperatorKind.ZERO
        ):
            return OperatorExpr.zero(left.infer_type())

    if current.kind == OperatorKind.POWER:
        operand = operands[0]
        assert current.exponent is not None
        if current.exponent == 0:
            return OperatorExpr.identity(operand.infer_type())
        if current.exponent == 1:
            return operand
        if operand.kind == OperatorKind.IDENTITY:
            return operand

    if current.kind == OperatorKind.TENSOR_PRODUCT:
        flat = list(_flatten(OperatorKind.TENSOR_PRODUCT, operands))
        if len(flat) == 1:
            return flat[0]
        return OperatorExpr.nary(
            OperatorKind.TENSOR_PRODUCT,
            flat,
        )

    return current


def operator_expression_from_dict(
    payload: Mapping[str, Any],
) -> OperatorExpr:
    from .types import math_type_from_dict

    scalar = payload.get("scalar_value")
    if (
        isinstance(scalar, Mapping)
        and "real" in scalar
        and "imag" in scalar
    ):
        scalar = complex(
            float(scalar["real"]),
            float(scalar["imag"]),
        )

    matrix = tuple(
        tuple(
            complex(value["real"], value["imag"])
            if (
                isinstance(value, Mapping)
                and "real" in value
                and "imag" in value
            )
            else value
            for value in row
        )
        for row in payload.get("matrix_value", [])
    )

    return OperatorExpr(
        kind=OperatorKind(payload["kind"]),
        operands=tuple(
            operator_expression_from_dict(value)
            for value in payload.get("operands", [])
        ),
        name=str(payload.get("name", "")),
        declared_type=None
        if payload.get("declared_type") is None
        else math_type_from_dict(payload["declared_type"]),
        scalar_value=scalar,
        matrix_value=matrix,
        exponent=payload.get("exponent"),
        attributes=tuple(
            sorted(payload.get("attributes", {}).items())
        ),
        properties=tuple(
            OperatorProperty(
                name=str(value["name"]),
                status=str(value.get("status", "declared")),
                evidence=tuple(
                    str(item)
                    for item in value.get("evidence", [])
                ),
            )
            for value in payload.get("properties", [])
        ),
    )
