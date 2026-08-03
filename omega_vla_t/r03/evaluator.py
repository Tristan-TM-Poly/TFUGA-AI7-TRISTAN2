"""Bounded numerical evaluation of finite OperatorExpr trees.

Only finite matrices are evaluated.  Symbolic differential, unbounded and
infinite-dimensional operators remain typed IR objects until a dedicated
backend supplies semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import numpy.typing as npt

from .operators import OperatorError, OperatorExpr, OperatorKind


Array = npt.NDArray[np.complex128]


@dataclass(frozen=True)
class EvaluationLimits:
    max_nodes: int = 100_000
    max_matrix_elements: int = 25_000_000
    max_power: int = 1024

    def __post_init__(self) -> None:
        if self.max_nodes <= 0 or self.max_matrix_elements <= 0 or self.max_power < 0:
            raise ValueError("evaluation limits must be positive")


@dataclass(frozen=True)
class EvaluationReport:
    matrix: Array
    expression_digest: str
    simplified_digest: str
    node_count_before: int
    node_count_after: int
    finite: bool
    residual_checks: tuple[tuple[str, float], ...]
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrix_real": self.matrix.real.tolist(),
            "matrix_imag": self.matrix.imag.tolist(),
            "shape": list(self.matrix.shape),
            "expression_digest": self.expression_digest,
            "simplified_digest": self.simplified_digest,
            "node_count_before": self.node_count_before,
            "node_count_after": self.node_count_after,
            "finite": self.finite,
            "residual_checks": dict(self.residual_checks),
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
        }


def evaluate_operator(
    expression: OperatorExpr,
    environment: Mapping[str, npt.ArrayLike] | None = None,
    *,
    simplify: bool = True,
    limits: EvaluationLimits | None = None,
) -> EvaluationReport:
    limits = limits or EvaluationLimits()
    if expression.node_count() > limits.max_nodes:
        raise OperatorError("expression exceeds max_nodes")
    simplified = expression.simplify() if simplify else expression
    matrix = _evaluate(simplified, dict(environment or {}), limits)
    _check_matrix_budget(matrix, limits)
    residuals = _property_residuals(simplified, matrix)
    return EvaluationReport(
        matrix=matrix,
        expression_digest=expression.digest(),
        simplified_digest=simplified.digest(),
        node_count_before=expression.node_count(),
        node_count_after=simplified.node_count(),
        finite=bool(np.all(np.isfinite(matrix))),
        residual_checks=tuple(sorted(residuals.items())),
    )


def _evaluate(
    expression: OperatorExpr,
    environment: dict[str, npt.ArrayLike],
    limits: EvaluationLimits,
) -> Array:
    kind = expression.kind
    inferred = expression.infer_type()
    raw_shape = inferred.shape.to_dict()
    if any(not isinstance(value, int) for value in raw_shape):
        raise OperatorError("numerical evaluation requires concrete dimensions")
    shape = tuple(int(value) for value in raw_shape)

    if kind == OperatorKind.SYMBOL:
        if expression.name not in environment:
            raise OperatorError(f"missing numerical binding for symbol {expression.name!r}")
        result = np.asarray(environment[expression.name], dtype=np.complex128)
        if result.shape != shape:
            raise OperatorError(
                f"symbol {expression.name!r} expected shape {shape}, got {result.shape}"
            )
        _check_matrix_budget(result, limits)
        return result
    if kind == OperatorKind.IDENTITY:
        return np.eye(shape[0], dtype=np.complex128)
    if kind == OperatorKind.ZERO:
        return np.zeros(shape, dtype=np.complex128)
    if kind == OperatorKind.MATRIX_LITERAL:
        return np.asarray(expression.matrix_value, dtype=np.complex128)

    operands = [_evaluate(value, environment, limits) for value in expression.operands]

    if kind == OperatorKind.SUM:
        result = operands[0].copy()
        for operand in operands[1:]:
            result = result + operand
        return result
    if kind == OperatorKind.DIFFERENCE:
        return operands[0] - operands[1]
    if kind == OperatorKind.COMPOSE:
        result = operands[-1]
        for outer in reversed(operands[:-1]):
            result = outer @ result
        return result
    if kind == OperatorKind.SCALAR_MULTIPLY:
        return complex(expression.scalar_value) * operands[0]
    if kind == OperatorKind.ADJOINT:
        return operands[0].conj().T
    if kind == OperatorKind.TRANSPOSE:
        return operands[0].T
    if kind == OperatorKind.CONJUGATE:
        return operands[0].conj()
    if kind == OperatorKind.INVERSE:
        return np.linalg.inv(operands[0])
    if kind == OperatorKind.PSEUDOINVERSE:
        return np.linalg.pinv(operands[0])
    if kind == OperatorKind.POWER:
        exponent = int(expression.exponent)
        if abs(exponent) > limits.max_power:
            raise OperatorError("matrix power exceeds max_power")
        return np.linalg.matrix_power(operands[0], exponent)
    if kind == OperatorKind.EXPONENTIAL:
        return _matrix_function_via_eigendecomposition(operands[0], np.exp)
    if kind == OperatorKind.LOGARITHM:
        return _matrix_function_via_eigendecomposition(operands[0], np.log)
    if kind == OperatorKind.COMMUTATOR:
        return operands[0] @ operands[1] - operands[1] @ operands[0]
    if kind == OperatorKind.ANTICOMMUTATOR:
        return operands[0] @ operands[1] + operands[1] @ operands[0]
    if kind == OperatorKind.TENSOR_PRODUCT:
        result = operands[0]
        for operand in operands[1:]:
            projected_size = result.size * operand.size
            if projected_size > limits.max_matrix_elements:
                raise OperatorError("tensor product exceeds max_matrix_elements")
            result = np.kron(result, operand)
        return result
    if kind == OperatorKind.DIRECT_SUM:
        return _block_diag(operands, limits)
    if kind == OperatorKind.KRONECKER_SUM:
        left, right = operands
        return np.kron(left, np.eye(right.shape[0])) + np.kron(np.eye(left.shape[0]), right)
    if kind in {OperatorKind.LOW_RANK_UPDATE, OperatorKind.PROJECTION}:
        if kind == OperatorKind.LOW_RANK_UPDATE:
            return operands[0] + operands[1]
        return operands[0]

    raise OperatorError(f"no NumPy evaluator for {kind.value}")


def _matrix_function_via_eigendecomposition(
    matrix: Array,
    function: Any,
) -> Array:
    """Reference implementation for diagonalizable fixtures.

    This is deliberately not advertised as a production-stable matrix function
    algorithm.  Dedicated SciPy/Schur/Padé backends belong in later waves.
    """

    values, vectors = np.linalg.eig(matrix)
    condition = np.linalg.cond(vectors)
    if not np.isfinite(condition) or condition > 1e12:
        raise OperatorError(
            "reference eigendecomposition backend rejected an ill-conditioned eigenbasis"
        )
    return vectors @ np.diag(function(values)) @ np.linalg.inv(vectors)


def _block_diag(operands: list[Array], limits: EvaluationLimits) -> Array:
    rows = sum(value.shape[0] for value in operands)
    columns = sum(value.shape[1] for value in operands)
    if rows * columns > limits.max_matrix_elements:
        raise OperatorError("direct sum exceeds max_matrix_elements")
    result = np.zeros((rows, columns), dtype=np.complex128)
    row = 0
    column = 0
    for value in operands:
        result[row : row + value.shape[0], column : column + value.shape[1]] = value
        row += value.shape[0]
        column += value.shape[1]
    return result


def _check_matrix_budget(matrix: Array, limits: EvaluationLimits) -> None:
    if matrix.ndim != 2:
        raise OperatorError("operator evaluation must produce a matrix")
    if matrix.size > limits.max_matrix_elements:
        raise OperatorError("matrix exceeds max_matrix_elements")
    if not np.all(np.isfinite(matrix)):
        raise OperatorError("operator evaluation produced non-finite values")


def _relative_residual(numerator: Array, denominator: Array) -> float:
    scale = max(float(np.linalg.norm(denominator)), np.finfo(float).eps)
    return float(np.linalg.norm(numerator) / scale)


def _property_residuals(expression: OperatorExpr, matrix: Array) -> dict[str, float]:
    residuals: dict[str, float] = {}
    if expression.has_property("self_adjoint"):
        residuals["self_adjoint"] = _relative_residual(matrix - matrix.conj().T, matrix)
    if expression.has_property("unitary"):
        identity = np.eye(matrix.shape[0], dtype=np.complex128)
        residuals["unitary"] = _relative_residual(matrix.conj().T @ matrix - identity, identity)
    if expression.has_property("projection") or expression.kind == OperatorKind.PROJECTION:
        residuals["idempotent"] = _relative_residual(matrix @ matrix - matrix, matrix)
    if expression.has_property("normal"):
        residuals["normal"] = _relative_residual(
            matrix @ matrix.conj().T - matrix.conj().T @ matrix,
            matrix,
        )
    return residuals
