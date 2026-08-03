"""Bounded matrix-function baselines for Ω-VLA Wave 2.

Algorithms are dependency-light reference implementations with explicit
residuals and rejection conditions. They are compared against mathematical
identities, not advertised as replacements for LAPACK/SciPy production code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

Array = npt.NDArray[np.complex128]


class MatrixFunctionError(ValueError):
    pass


@dataclass(frozen=True)
class MatrixFunctionReport:
    function: str
    method: str
    shape: tuple[int, int]
    result: Array
    residual_name: str
    residual: float
    iterations: int
    scaling_steps: int
    condition_estimate: float | None
    finite: bool
    passed: bool
    warnings: tuple[str, ...] = ()
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["result_real"] = self.result.real.tolist()
        payload["result_imag"] = self.result.imag.tolist()
        payload.pop("result")
        return payload


def _square_matrix(matrix: npt.ArrayLike, *, max_dimension: int) -> Array:
    array = np.asarray(matrix, dtype=np.complex128)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise MatrixFunctionError("matrix functions require a square matrix")
    if array.shape[0] > max_dimension:
        raise MatrixFunctionError("matrix dimension exceeds the configured envelope")
    if not np.all(np.isfinite(array)):
        raise MatrixFunctionError("matrix entries must be finite")
    return array


def _relative_residual(numerator: Array, reference: Array) -> float:
    scale = max(float(np.linalg.norm(reference, ord="fro")), np.finfo(float).eps)
    return float(np.linalg.norm(numerator, ord="fro") / scale)


def _solve(left: Array, right: Array, *, condition_limit: float = 1e15) -> tuple[Array, float]:
    condition = float(np.linalg.cond(left))
    if not np.isfinite(condition) or condition > condition_limit:
        raise MatrixFunctionError(
            f"linear solve rejected condition estimate {condition:.6g}"
        )
    return np.linalg.solve(left, right), condition


def _pade13_exponential(matrix: Array) -> tuple[Array, int, float]:
    """Return exp(A), scaling count and solve condition without recursion."""

    n = matrix.shape[0]
    identity = np.eye(n, dtype=np.complex128)
    theta13 = 5.371920351148152
    norm1 = float(np.linalg.norm(matrix, 1))
    scaling = 0 if norm1 == 0.0 else max(
        0, int(np.ceil(np.log2(norm1 / theta13)))
    )
    scaled = matrix / (2**scaling)
    b = (
        64764752532480000.0,
        32382376266240000.0,
        7771770303897600.0,
        1187353796428800.0,
        129060195264000.0,
        10559470521600.0,
        670442572800.0,
        33522128640.0,
        1323241920.0,
        40840800.0,
        960960.0,
        16380.0,
        182.0,
        1.0,
    )
    a2 = scaled @ scaled
    a4 = a2 @ a2
    a6 = a4 @ a2
    u = scaled @ (
        a6 @ (b[13] * a6 + b[11] * a4 + b[9] * a2)
        + b[7] * a6
        + b[5] * a4
        + b[3] * a2
        + b[1] * identity
    )
    v = (
        a6 @ (b[12] * a6 + b[10] * a4 + b[8] * a2)
        + b[6] * a6
        + b[4] * a4
        + b[2] * a2
        + b[0] * identity
    )
    result, condition = _solve(v - u, v + u)
    for _ in range(scaling):
        result = result @ result
    return result, scaling, condition


def matrix_exponential(
    matrix: npt.ArrayLike,
    *,
    tolerance: float = 1e-11,
    max_dimension: int = 2048,
    audit_inverse_dimension: int = 128,
) -> MatrixFunctionReport:
    """Scaling-and-squaring with the [13/13] Padé approximant."""

    a = _square_matrix(matrix, max_dimension=max_dimension)
    result, scaling, condition = _pade13_exponential(a)
    identity = np.eye(a.shape[0], dtype=np.complex128)
    warnings: tuple[str, ...] = ()
    if a.shape[0] <= audit_inverse_dimension:
        inverse_result, _, _ = _pade13_exponential(-a)
        residual = _relative_residual(result @ inverse_result - identity, identity)
    else:
        residual = float("nan")
        warnings = ("inverse identity audit skipped above audit_inverse_dimension",)
    finite = bool(np.all(np.isfinite(result)))
    passed = finite and (np.isnan(residual) or residual <= tolerance * 100)
    return MatrixFunctionReport(
        function="exponential",
        method="pade13_scaling_squaring",
        shape=a.shape,
        result=result,
        residual_name="exp(A)exp(-A)-I",
        residual=residual,
        iterations=1,
        scaling_steps=scaling,
        condition_estimate=condition,
        finite=finite,
        passed=passed,
        warnings=warnings,
    )


def _newton_sqrt(
    matrix: Array,
    *,
    tolerance: float,
    max_iterations: int,
) -> tuple[Array, int, float]:
    n = matrix.shape[0]
    y = matrix.copy()
    z = np.eye(n, dtype=np.complex128)
    identity = np.eye(n, dtype=np.complex128)
    for iteration in range(1, max_iterations + 1):
        inv_y, _ = _solve(y, identity)
        inv_z, _ = _solve(z, identity)
        y_next = 0.5 * (y + inv_z)
        z_next = 0.5 * (z + inv_y)
        change = _relative_residual(y_next - y, y_next)
        y, z = y_next, z_next
        if change <= tolerance:
            return y, iteration, change
    raise MatrixFunctionError("matrix square-root iteration did not converge")


def matrix_square_root(
    matrix: npt.ArrayLike,
    *,
    tolerance: float = 1e-11,
    max_iterations: int = 100,
    max_dimension: int = 1024,
) -> MatrixFunctionReport:
    """Denman-Beavers reference iteration with residual audit."""

    a = _square_matrix(matrix, max_dimension=max_dimension)
    result, iterations, change = _newton_sqrt(
        a, tolerance=tolerance, max_iterations=max_iterations
    )
    residual = _relative_residual(result @ result - a, a)
    finite = bool(np.all(np.isfinite(result)))
    return MatrixFunctionReport(
        function="square_root",
        method="denman_beavers",
        shape=a.shape,
        result=result,
        residual_name="X^2-A",
        residual=residual,
        iterations=iterations,
        scaling_steps=0,
        condition_estimate=float(np.linalg.cond(a)),
        finite=finite,
        passed=finite and residual <= tolerance * 100,
        warnings=(f"last relative iterate change={change:.6g}",),
    )


def matrix_logarithm(
    matrix: npt.ArrayLike,
    *,
    tolerance: float = 1e-11,
    max_square_roots: int = 32,
    max_terms: int = 256,
    max_dimension: int = 512,
) -> MatrixFunctionReport:
    """Inverse scaling-and-squaring plus atanh series near identity."""

    a = _square_matrix(matrix, max_dimension=max_dimension)
    eigenvalues = np.linalg.eigvals(a)
    for value in eigenvalues:
        if abs(value) <= tolerance:
            raise MatrixFunctionError("principal logarithm is undefined for singular matrices")
        if value.real <= 0 and abs(value.imag) <= tolerance:
            raise MatrixFunctionError("principal logarithm rejected the negative real axis")

    identity = np.eye(a.shape[0], dtype=np.complex128)
    reduced = a.copy()
    roots = 0
    while np.linalg.norm(reduced - identity, 1) > 0.5:
        if roots >= max_square_roots:
            raise MatrixFunctionError("logarithm inverse scaling exceeded max_square_roots")
        reduced, _, _ = _newton_sqrt(
            reduced, tolerance=tolerance, max_iterations=100
        )
        roots += 1

    x, condition = _solve(reduced + identity, reduced - identity)
    x2 = x @ x
    term = x.copy()
    series = x.copy()
    iterations = 1
    for index in range(1, max_terms):
        term = term @ x2
        addition = term / (2 * index + 1)
        series = series + addition
        iterations = index + 1
        if np.linalg.norm(addition, ord="fro") <= tolerance * max(
            np.linalg.norm(series, ord="fro"), 1.0
        ):
            break
    else:
        raise MatrixFunctionError("logarithm series did not converge within max_terms")

    result = (2 ** (roots + 1)) * series
    exponential, _, _ = _pade13_exponential(result)
    residual = _relative_residual(exponential - a, a)
    finite = bool(np.all(np.isfinite(result)))
    return MatrixFunctionReport(
        function="logarithm",
        method="inverse_scaling_atanh_series",
        shape=a.shape,
        result=result,
        residual_name="exp(log(A))-A",
        residual=residual,
        iterations=iterations,
        scaling_steps=roots,
        condition_estimate=condition,
        finite=finite,
        passed=finite and residual <= tolerance * 1000,
    )


def matrix_sign(
    matrix: npt.ArrayLike,
    *,
    tolerance: float = 1e-11,
    max_iterations: int = 100,
    max_dimension: int = 1024,
) -> MatrixFunctionReport:
    """Newton iteration X_{k+1}=1/2(X_k+X_k^{-1})."""

    a = _square_matrix(matrix, max_dimension=max_dimension)
    eigenvalues = np.linalg.eigvals(a)
    if np.any(np.abs(eigenvalues.real) <= tolerance):
        raise MatrixFunctionError("matrix sign rejected eigenvalues near the imaginary axis")
    x = a.copy()
    identity = np.eye(x.shape[0], dtype=np.complex128)
    condition: float | None = None
    for iteration in range(1, max_iterations + 1):
        inverse, condition = _solve(x, identity)
        candidate = 0.5 * (x + inverse)
        change = _relative_residual(candidate - x, candidate)
        x = candidate
        if change <= tolerance:
            break
    else:
        raise MatrixFunctionError("matrix-sign iteration did not converge")
    residual = _relative_residual(x @ x - identity, identity)
    finite = bool(np.all(np.isfinite(x)))
    return MatrixFunctionReport(
        function="sign",
        method="newton",
        shape=a.shape,
        result=x,
        residual_name="sign(A)^2-I",
        residual=residual,
        iterations=iteration,
        scaling_steps=0,
        condition_estimate=condition,
        finite=finite,
        passed=finite and residual <= tolerance * 100,
    )
