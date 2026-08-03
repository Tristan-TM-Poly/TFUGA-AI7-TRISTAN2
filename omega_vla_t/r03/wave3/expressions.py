"""Finite matrix-expression IR for Ω-VLA Wave 3.

This module implements bounded, finite-dimensional software semantics. It does
not assign universal meaning to unbounded operators and does not turn numerical
equality into proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping
import numpy as np
import numpy.typing as npt

Array = npt.NDArray[np.complex128]


class ExprError(ValueError):
    """Raised when a matrix expression is malformed or cannot be evaluated."""


class ExprKind(str, Enum):
    VARIABLE = "variable"
    IDENTITY = "identity"
    ZERO = "zero"
    ADD = "add"
    SUBTRACT = "subtract"
    MATMUL = "matmul"
    ADJOINT = "adjoint"
    TRANSPOSE = "transpose"
    INVERSE = "inverse"
    POWER = "power"
    COMMUTATOR = "commutator"
    ANTICOMMUTATOR = "anticommutator"
    TENSOR = "tensor"
    SCALAR_MULTIPLY = "scalar_multiply"


@dataclass(frozen=True)
class MatrixExpr:
    kind: ExprKind
    operands: tuple["MatrixExpr", ...] = ()
    name: str = ""
    dimension: int | None = None
    scalar: complex | float | int | None = None
    exponent: int | None = None

    def __post_init__(self) -> None:
        arity = len(self.operands)
        if self.kind == ExprKind.VARIABLE:
            if not self.name or arity:
                raise ExprError("variables require a name and no operands")
        elif self.kind in {ExprKind.IDENTITY, ExprKind.ZERO}:
            if self.dimension is None or self.dimension < 1 or arity:
                raise ExprError("identity/zero require a positive dimension")
        elif self.kind in {
            ExprKind.ADJOINT, ExprKind.TRANSPOSE, ExprKind.INVERSE, ExprKind.POWER,
            ExprKind.SCALAR_MULTIPLY,
        }:
            if arity != 1:
                raise ExprError(f"{self.kind.value} requires one operand")
        elif self.kind in {
            ExprKind.SUBTRACT, ExprKind.COMMUTATOR, ExprKind.ANTICOMMUTATOR,
            ExprKind.TENSOR,
        }:
            if arity != 2:
                raise ExprError(f"{self.kind.value} requires two operands")
        elif self.kind in {ExprKind.ADD, ExprKind.MATMUL}:
            if arity < 2:
                raise ExprError(f"{self.kind.value} requires at least two operands")
        if self.kind == ExprKind.POWER and self.exponent is None:
            raise ExprError("power requires an integer exponent")
        if self.kind == ExprKind.SCALAR_MULTIPLY and self.scalar is None:
            raise ExprError("scalar multiplication requires a scalar")

    @classmethod
    def variable(cls, name: str) -> "MatrixExpr":
        return cls(ExprKind.VARIABLE, name=name)

    @classmethod
    def identity(cls, dimension: int) -> "MatrixExpr":
        return cls(ExprKind.IDENTITY, dimension=dimension)

    @classmethod
    def zero(cls, dimension: int) -> "MatrixExpr":
        return cls(ExprKind.ZERO, dimension=dimension)

    @classmethod
    def nary(cls, kind: ExprKind, *operands: "MatrixExpr") -> "MatrixExpr":
        return cls(kind, operands=tuple(operands))

    def __add__(self, other: "MatrixExpr") -> "MatrixExpr":
        return MatrixExpr(ExprKind.ADD, (self, other))

    def __sub__(self, other: "MatrixExpr") -> "MatrixExpr":
        return MatrixExpr(ExprKind.SUBTRACT, (self, other))

    def __matmul__(self, other: "MatrixExpr") -> "MatrixExpr":
        return MatrixExpr(ExprKind.MATMUL, (self, other))

    def adjoint(self) -> "MatrixExpr":
        return MatrixExpr(ExprKind.ADJOINT, (self,))

    def transpose(self) -> "MatrixExpr":
        return MatrixExpr(ExprKind.TRANSPOSE, (self,))

    def inverse(self) -> "MatrixExpr":
        return MatrixExpr(ExprKind.INVERSE, (self,))

    def power(self, exponent: int) -> "MatrixExpr":
        return MatrixExpr(ExprKind.POWER, (self,), exponent=int(exponent))

    def scale(self, scalar: complex | float | int) -> "MatrixExpr":
        return MatrixExpr(ExprKind.SCALAR_MULTIPLY, (self,), scalar=scalar)

    def commutator(self, other: "MatrixExpr") -> "MatrixExpr":
        return MatrixExpr(ExprKind.COMMUTATOR, (self, other))

    def anticommutator(self, other: "MatrixExpr") -> "MatrixExpr":
        return MatrixExpr(ExprKind.ANTICOMMUTATOR, (self, other))

    def tensor(self, other: "MatrixExpr") -> "MatrixExpr":
        return MatrixExpr(ExprKind.TENSOR, (self, other))

    def symbols(self) -> tuple[str, ...]:
        found: set[str] = set()
        if self.kind == ExprKind.VARIABLE:
            found.add(self.name)
        for operand in self.operands:
            found.update(operand.symbols())
        return tuple(sorted(found))

    def node_count(self) -> int:
        return 1 + sum(value.node_count() for value in self.operands)

    def depth(self) -> int:
        return 1 if not self.operands else 1 + max(x.depth() for x in self.operands)

    def to_dict(self) -> dict[str, Any]:
        scalar: Any = self.scalar
        if isinstance(scalar, complex):
            scalar = {"real": scalar.real, "imag": scalar.imag}
        return {
            "kind": self.kind.value,
            "operands": [value.to_dict() for value in self.operands],
            "name": self.name,
            "dimension": self.dimension,
            "scalar": scalar,
            "exponent": self.exponent,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MatrixExpr":
        scalar = payload.get("scalar")
        if isinstance(scalar, Mapping):
            scalar = complex(float(scalar["real"]), float(scalar["imag"]))
        return cls(
            kind=ExprKind(str(payload["kind"])),
            operands=tuple(cls.from_dict(x) for x in payload.get("operands", [])),
            name=str(payload.get("name", "")),
            dimension=payload.get("dimension"),
            scalar=scalar,
            exponent=payload.get("exponent"),
        )

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return sha256(self.canonical_json().encode()).hexdigest()

    def evaluate(self, environment: Mapping[str, npt.ArrayLike]) -> Array:
        if self.kind == ExprKind.VARIABLE:
            if self.name not in environment:
                raise ExprError(f"missing matrix variable {self.name!r}")
            value = np.asarray(environment[self.name], dtype=np.complex128)
            if value.ndim != 2 or not np.all(np.isfinite(value)):
                raise ExprError(f"{self.name} must be a finite matrix")
            return value
        if self.kind == ExprKind.IDENTITY:
            assert self.dimension is not None
            return np.eye(self.dimension, dtype=np.complex128)
        if self.kind == ExprKind.ZERO:
            assert self.dimension is not None
            return np.zeros((self.dimension, self.dimension), dtype=np.complex128)

        values = tuple(value.evaluate(environment) for value in self.operands)
        try:
            if self.kind == ExprKind.ADD:
                result = values[0].copy()
                for value in values[1:]:
                    result = result + value
                return result
            if self.kind == ExprKind.SUBTRACT:
                return values[0] - values[1]
            if self.kind == ExprKind.MATMUL:
                result = values[0]
                for value in values[1:]:
                    result = result @ value
                return result
            if self.kind == ExprKind.ADJOINT:
                return values[0].conj().T
            if self.kind == ExprKind.TRANSPOSE:
                return values[0].T
            if self.kind == ExprKind.INVERSE:
                return np.linalg.inv(values[0])
            if self.kind == ExprKind.POWER:
                assert self.exponent is not None
                return np.linalg.matrix_power(values[0], self.exponent)
            if self.kind == ExprKind.COMMUTATOR:
                return values[0] @ values[1] - values[1] @ values[0]
            if self.kind == ExprKind.ANTICOMMUTATOR:
                return values[0] @ values[1] + values[1] @ values[0]
            if self.kind == ExprKind.TENSOR:
                return np.kron(values[0], values[1])
            if self.kind == ExprKind.SCALAR_MULTIPLY:
                assert self.scalar is not None
                return self.scalar * values[0]
        except ValueError as exc:
            raise ExprError(f"shape error while evaluating {self.kind.value}") from exc
        except np.linalg.LinAlgError as exc:
            raise ExprError(f"linear algebra failure in {self.kind.value}") from exc
        raise ExprError(f"unsupported expression kind {self.kind.value}")

    def simplify(self, *, max_passes: int = 32) -> "MatrixExpr":
        result = self
        for _ in range(max_passes):
            candidate = _simplify_once(result)
            if candidate == result:
                return result
            result = candidate
        raise ExprError("simplifier did not converge")


def _simplify_once(expr: MatrixExpr) -> MatrixExpr:
    if not expr.operands:
        return expr
    ops = tuple(value.simplify(max_passes=8) for value in expr.operands)
    rebuilt = MatrixExpr(
        expr.kind, ops, expr.name, expr.dimension, expr.scalar, expr.exponent
    )
    if rebuilt.kind in {ExprKind.ADJOINT, ExprKind.TRANSPOSE}:
        operand = ops[0]
        if operand.kind == rebuilt.kind:
            return operand.operands[0]
        if operand.kind in {ExprKind.IDENTITY, ExprKind.ZERO}:
            return operand
        if operand.kind == ExprKind.MATMUL:
            transformed = [
                MatrixExpr(rebuilt.kind, (value,)) for value in reversed(operand.operands)
            ]
            return MatrixExpr(ExprKind.MATMUL, tuple(transformed))
        if operand.kind in {ExprKind.ADD, ExprKind.SUBTRACT}:
            return MatrixExpr(
                operand.kind,
                tuple(MatrixExpr(rebuilt.kind, (value,)) for value in operand.operands),
            )
    if rebuilt.kind == ExprKind.POWER and rebuilt.exponent == 1:
        return ops[0]
    if rebuilt.kind == ExprKind.SCALAR_MULTIPLY:
        if rebuilt.scalar == 1:
            return ops[0]
        if ops[0].kind == ExprKind.SCALAR_MULTIPLY:
            return ops[0].operands[0].scale(rebuilt.scalar * ops[0].scalar)
    if rebuilt.kind in {ExprKind.ADD, ExprKind.MATMUL}:
        flat: list[MatrixExpr] = []
        for value in ops:
            flat.extend(value.operands if value.kind == rebuilt.kind else (value,))
        return MatrixExpr(rebuilt.kind, tuple(flat))
    return rebuilt


def relative_residual(
    left: MatrixExpr,
    right: MatrixExpr,
    environment: Mapping[str, npt.ArrayLike],
) -> tuple[float, float]:
    """Return absolute and scale-normalized Frobenius residuals."""
    lhs = left.evaluate(environment)
    rhs = right.evaluate(environment)
    if lhs.shape != rhs.shape:
        raise ExprError(f"identity sides have incompatible shapes: {lhs.shape} != {rhs.shape}")
    absolute = float(np.linalg.norm(lhs - rhs))
    scale = max(float(np.linalg.norm(lhs)), float(np.linalg.norm(rhs)), np.finfo(float).eps)
    return absolute, absolute / scale
