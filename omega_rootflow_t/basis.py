"""Multi-representation polynomial bases and conditioning atlas for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Iterable

import numpy as np
import numpy.typing as npt

from .continuation import match_roots
from .core import _coefficients, derivative_value, roots

ComplexArray = npt.NDArray[np.complex128]

SUPPORTED_BASES = ("monomial", "chebyshev", "legendre", "bernstein")


def _vector(values: npt.ArrayLike) -> ComplexArray:
    array = np.asarray(values, dtype=np.complex128)
    if array.ndim != 1 or array.size < 2:
        raise ValueError("basis coefficients must be a one-dimensional array of length >= 2")
    if not np.all(np.isfinite(array.real)) or not np.all(np.isfinite(array.imag)):
        raise ValueError("basis coefficients must be finite")
    return array


def bernstein_to_monomial(coefficients: npt.ArrayLike) -> ComplexArray:
    """Convert degree-n Bernstein coefficients on [0,1] to power coefficients."""
    beta = _vector(coefficients)
    degree = beta.size - 1
    result = np.zeros(degree + 1, dtype=np.complex128)
    for k, value in enumerate(beta):
        for j in range(k, degree + 1):
            result[j] += (
                value
                * comb(degree, k)
                * comb(degree - k, j - k)
                * ((-1) ** (j - k))
            )
    return result


def monomial_to_bernstein(coefficients: npt.ArrayLike) -> ComplexArray:
    """Convert degree-n power coefficients to Bernstein coefficients on [0,1]."""
    poly = _coefficients(coefficients)
    degree = poly.size - 1
    beta = np.zeros(degree + 1, dtype=np.complex128)
    for k in range(degree + 1):
        beta[k] = sum(
            poly[j] * comb(k, j) / comb(degree, j)
            for j in range(k + 1)
        )
    return beta


def basis_to_monomial(coefficients: npt.ArrayLike, basis: str) -> ComplexArray:
    """Convert supported native-basis coefficients to ascending power coefficients."""
    values = _vector(coefficients)
    key = basis.lower()
    if key == "monomial":
        result = values.copy()
    elif key == "chebyshev":
        result = np.asarray(np.polynomial.chebyshev.cheb2poly(values), dtype=np.complex128)
    elif key == "legendre":
        result = np.asarray(np.polynomial.legendre.leg2poly(values), dtype=np.complex128)
    elif key == "bernstein":
        result = bernstein_to_monomial(values)
    else:
        raise ValueError(f"unsupported basis {basis!r}; choose from {SUPPORTED_BASES}")
    if result.size < 2 or abs(result[-1]) <= np.finfo(float).eps:
        raise ValueError("converted polynomial must retain a non-zero leading coefficient")
    return result


def monomial_to_basis(coefficients: npt.ArrayLike, basis: str) -> ComplexArray:
    """Represent one power-basis polynomial in a supported native basis."""
    poly = _coefficients(coefficients)
    key = basis.lower()
    if key == "monomial":
        return poly.copy()
    if key == "chebyshev":
        return np.asarray(np.polynomial.chebyshev.poly2cheb(poly), dtype=np.complex128)
    if key == "legendre":
        return np.asarray(np.polynomial.legendre.poly2leg(poly), dtype=np.complex128)
    if key == "bernstein":
        return monomial_to_bernstein(poly)
    raise ValueError(f"unsupported basis {basis!r}; choose from {SUPPORTED_BASES}")


def basis_values_at(basis: str, z: complex, count: int) -> ComplexArray:
    """Evaluate every native basis function phi_0..phi_(count-1) at z."""
    if count <= 0:
        raise ValueError("count must be positive")
    key = basis.lower()
    degree = count - 1
    if key == "monomial":
        return np.asarray([z**k for k in range(count)], dtype=np.complex128)
    if key == "chebyshev":
        return np.asarray(np.polynomial.chebyshev.chebvander(np.asarray([z]), degree)[0], dtype=np.complex128)
    if key == "legendre":
        return np.asarray(np.polynomial.legendre.legvander(np.asarray([z]), degree)[0], dtype=np.complex128)
    if key == "bernstein":
        return np.asarray(
            [comb(degree, k) * z**k * (1.0 - z) ** (degree - k) for k in range(count)],
            dtype=np.complex128,
        )
    raise ValueError(f"unsupported basis {basis!r}; choose from {SUPPORTED_BASES}")


def native_root_jacobian(
    coefficients: npt.ArrayLike,
    basis: str,
    root_values: npt.ArrayLike | None = None,
    *,
    singularity_tolerance: float = 1e-12,
) -> ComplexArray:
    """Return derivatives of roots with respect to coefficients in a native basis."""
    native = _vector(coefficients)
    power = basis_to_monomial(native, basis)
    rr = roots(power) if root_values is None else np.asarray(root_values, dtype=np.complex128)
    if rr.ndim != 1:
        raise ValueError("root_values must be one-dimensional")
    result = np.empty((rr.size, native.size), dtype=np.complex128)
    for index, root_value in enumerate(rr):
        root = complex(root_value)
        derivative = derivative_value(power, root)
        if abs(derivative) <= singularity_tolerance:
            raise np.linalg.LinAlgError("native-basis root Jacobian is singular near a repeated root")
        result[index] = -basis_values_at(basis, root, native.size) / derivative
    return result


@dataclass(frozen=True)
class BasisConditionRecord:
    basis: str
    coefficient_norm: float
    maximum_jacobian_row_norm: float
    median_relative_condition: float
    maximum_relative_condition: float
    reconstruction_error: float

    def to_dict(self) -> dict[str, object]:
        return {
            "basis": self.basis,
            "coefficient_norm": self.coefficient_norm,
            "maximum_jacobian_row_norm": self.maximum_jacobian_row_norm,
            "median_relative_condition": self.median_relative_condition,
            "maximum_relative_condition": self.maximum_relative_condition,
            "reconstruction_error": self.reconstruction_error,
        }


@dataclass(frozen=True)
class BasisConditionAtlas:
    roots: ComplexArray
    records: tuple[BasisConditionRecord, ...]
    best_maximum_relative_condition_basis: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "roots": [[float(z.real), float(z.imag)] for z in self.roots],
            "records": [record.to_dict() for record in self.records],
            "best_maximum_relative_condition_basis": self.best_maximum_relative_condition_basis,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def conditioning_atlas(
    monomial_coefficients: npt.ArrayLike,
    *,
    bases: Iterable[str] = SUPPORTED_BASES,
    singularity_tolerance: float = 1e-12,
) -> BasisConditionAtlas:
    """Compare first-order relative root sensitivity across coefficient bases.

    The represented polynomial is held fixed.  Because coefficient coordinates
    differ between bases, this atlas measures representation-dependent local
    conditioning; it does not claim that one basis is universally optimal.
    """
    power = _coefficients(monomial_coefficients)
    baseline_roots = roots(power)
    records: list[BasisConditionRecord] = []
    for basis in bases:
        key = basis.lower()
        native = monomial_to_basis(power, key)
        reconstructed = basis_to_monomial(native, key)
        # Align lengths in the unlikely event a conversion trims exact zeros.
        padded = np.zeros_like(power)
        padded[: reconstructed.size] = reconstructed
        reconstruction_error = float(
            np.linalg.norm(power - padded) / max(np.linalg.norm(power), np.finfo(float).eps)
        )
        native_roots = roots(reconstructed)
        ordered_roots = match_roots(baseline_roots, native_roots)
        jac = native_root_jacobian(
            native,
            key,
            ordered_roots,
            singularity_tolerance=singularity_tolerance,
        )
        row_norms = np.linalg.norm(jac, axis=1)
        coefficient_norm = float(np.linalg.norm(native))
        relative = coefficient_norm * row_norms / np.maximum(np.abs(ordered_roots), np.finfo(float).eps)
        records.append(
            BasisConditionRecord(
                basis=key,
                coefficient_norm=coefficient_norm,
                maximum_jacobian_row_norm=float(np.max(row_norms)),
                median_relative_condition=float(np.median(relative)),
                maximum_relative_condition=float(np.max(relative)),
                reconstruction_error=reconstruction_error,
            )
        )
    if not records:
        raise ValueError("bases must contain at least one supported basis")
    best = min(records, key=lambda item: item.maximum_relative_condition).basis
    return BasisConditionAtlas(
        roots=baseline_roots,
        records=tuple(records),
        best_maximum_relative_condition_basis=best,
    )
