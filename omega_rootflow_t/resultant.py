"""Resultant/discriminant and single-coefficient collision geometry for R0.5.

For a one-parameter coefficient shift

    F(z,t) = P(z) + t z^k,

finite multiple roots satisfy ``F=F_z=0``.  For ``k=0`` they occur at critical
points of ``P`` with ``t=-P(c)``.  For ``k>0`` and ``c!=0``, eliminating ``t``
gives the polynomial condition

    c P'(c) - k P(c) = 0,
    t = -P(c)/c^k.

This turns variation of *any one coefficient* into an explicit collision atlas.
When ``k=n`` there is additionally a projective degree transition at
``t=-a_n`` where the leading coefficient vanishes; that event is not confused
with a finite repeated root.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_coefficients, derivative_value, polynomial_value, roots

ComplexArray = npt.NDArray[np.complex128]


def _effective_polynomial(values: npt.ArrayLike) -> ComplexArray:
    coeffs = np.asarray(values, dtype=np.complex128)
    if coeffs.ndim != 1 or coeffs.size == 0:
        raise ValueError("polynomial coefficients must be a non-empty vector")
    if not np.all(np.isfinite(coeffs.real)) or not np.all(np.isfinite(coeffs.imag)):
        raise ValueError("polynomial coefficients must be finite")
    last = coeffs.size - 1
    while last > 0 and coeffs[last] == 0:
        last -= 1
    coeffs = coeffs[: last + 1]
    if coeffs.size == 1 and coeffs[0] == 0:
        raise ValueError("zero polynomial has no finite resultant degree")
    return np.asarray(coeffs, dtype=np.complex128)


def sylvester_matrix(
    first_coefficients: npt.ArrayLike,
    second_coefficients: npt.ArrayLike,
) -> ComplexArray:
    """Return the Sylvester matrix for ascending-order polynomials."""
    first = _effective_polynomial(first_coefficients)
    second = _effective_polynomial(second_coefficients)
    degree_first = first.size - 1
    degree_second = second.size - 1
    size = degree_first + degree_second
    if size == 0:
        return np.zeros((0, 0), dtype=np.complex128)
    matrix = np.zeros((size, size), dtype=np.complex128)
    first_descending = first[::-1]
    second_descending = second[::-1]
    for row in range(degree_second):
        matrix[row, row : row + degree_first + 1] = first_descending
    for offset in range(degree_first):
        row = degree_second + offset
        matrix[row, offset : offset + degree_second + 1] = second_descending
    return matrix


def polynomial_resultant(
    first_coefficients: npt.ArrayLike,
    second_coefficients: npt.ArrayLike,
) -> complex:
    """Numerical resultant from the Sylvester determinant."""
    first = _effective_polynomial(first_coefficients)
    second = _effective_polynomial(second_coefficients)
    degree_first = first.size - 1
    degree_second = second.size - 1
    if degree_first == 0:
        return complex(first[0] ** degree_second)
    if degree_second == 0:
        return complex(second[0] ** degree_first)
    return complex(np.linalg.det(sylvester_matrix(first, second)))


def discriminant_from_resultant(coefficients: npt.ArrayLike) -> complex:
    """Return ``Disc(P)=(-1)^(n(n-1)/2) Res(P,P')/a_n``."""
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    if degree == 1:
        return 1.0 + 0j
    derivative = derivative_coefficients(coeffs)
    sign = (-1) ** (degree * (degree - 1) // 2)
    return complex(sign * polynomial_resultant(coeffs, derivative) / coeffs[-1])


def discriminant_from_roots(coefficients: npt.ArrayLike) -> complex:
    """Independent root-product discriminant cross-check."""
    coeffs = _coefficients(coefficients)
    rr = roots(coeffs)
    degree = rr.size
    product = 1.0 + 0j
    for left in range(degree):
        for right in range(left + 1, degree):
            product *= (rr[left] - rr[right]) ** 2
    return complex(coeffs[-1] ** (2 * degree - 2) * product)


@dataclass(frozen=True)
class DiscriminantAudit:
    degree: int
    resultant_discriminant: complex
    root_discriminant: complex
    absolute_error: float
    relative_error: float
    near_collision: bool
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def passed(self) -> bool:
        return self.status in {
            "OAK_PASS_DISCRIMINANT_CROSSCHECK",
            "OAK_PASS_DISCRIMINANT_COLLISION",
        }

    def to_dict(self) -> dict[str, object]:
        def encode(value: complex) -> list[float]:
            return [float(value.real), float(value.imag)]

        return {
            "degree": self.degree,
            "resultant_discriminant": encode(self.resultant_discriminant),
            "root_discriminant": encode(self.root_discriminant),
            "absolute_error": self.absolute_error,
            "relative_error": self.relative_error,
            "near_collision": self.near_collision,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_discriminant(
    coefficients: npt.ArrayLike,
    *,
    relative_tolerance: float = 1e-7,
    collision_tolerance: float = 1e-9,
) -> DiscriminantAudit:
    coeffs = _coefficients(coefficients)
    if relative_tolerance <= 0 or collision_tolerance <= 0:
        raise ValueError("tolerances must be positive")
    via_resultant = discriminant_from_resultant(coeffs)
    via_roots = discriminant_from_roots(coeffs)
    absolute = float(abs(via_resultant - via_roots))
    scale = max(abs(via_resultant), abs(via_roots), np.finfo(float).eps)
    relative = absolute / scale
    near = abs(via_resultant) <= collision_tolerance
    if near and abs(via_roots) <= max(collision_tolerance, 10.0 * absolute):
        status = "OAK_PASS_DISCRIMINANT_COLLISION"
    elif relative <= relative_tolerance:
        status = "OAK_PASS_DISCRIMINANT_CROSSCHECK"
    else:
        status = "OAK_WARN_DISCRIMINANT_CROSSCHECK"
    return DiscriminantAudit(
        degree=coeffs.size - 1,
        resultant_discriminant=via_resultant,
        root_discriminant=via_roots,
        absolute_error=absolute,
        relative_error=float(relative),
        near_collision=bool(near),
        status=status,
    )


@dataclass(frozen=True)
class CollisionCandidate:
    critical_root: complex
    parameter: complex
    polynomial_residual: float
    derivative_residual: float

    def to_dict(self) -> dict[str, object]:
        return {
            "critical_root": [float(self.critical_root.real), float(self.critical_root.imag)],
            "parameter": [float(self.parameter.real), float(self.parameter.imag)],
            "polynomial_residual": self.polynomial_residual,
            "derivative_residual": self.derivative_residual,
        }


@dataclass(frozen=True)
class SingleCoefficientCollisionAtlas:
    degree: int
    coefficient_degree: int
    candidates: tuple[CollisionCandidate, ...]
    persistent_zero_collision: bool
    infinity_transition_parameter: complex | None
    maximum_residual: float
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        infinity = None
        if self.infinity_transition_parameter is not None:
            infinity = [
                float(self.infinity_transition_parameter.real),
                float(self.infinity_transition_parameter.imag),
            ]
        return {
            "degree": self.degree,
            "coefficient_degree": self.coefficient_degree,
            "candidates": [item.to_dict() for item in self.candidates],
            "persistent_zero_collision": self.persistent_zero_collision,
            "infinity_transition_parameter": infinity,
            "maximum_residual": self.maximum_residual,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def _raw_value(coefficients: ComplexArray, z: complex) -> complex:
    return complex(np.polynomial.polynomial.polyval(z, coefficients))


def _raw_derivative_value(coefficients: ComplexArray, z: complex) -> complex:
    if coefficients.size <= 1:
        return 0j
    derivative = np.arange(1, coefficients.size, dtype=float) * coefficients[1:]
    return complex(np.polynomial.polynomial.polyval(z, derivative))


def single_coefficient_collision_atlas(
    coefficients: npt.ArrayLike,
    coefficient_degree: int,
    *,
    root_tolerance: float = 1e-10,
    residual_tolerance: float = 1e-7,
) -> SingleCoefficientCollisionAtlas:
    """Find finite collision parameters for ``P(z)+t*z^k``.

    For the leading coefficient ``k=n``, ``t=-a_n`` is separately reported as
    a root-at-infinity / degree-transition parameter.
    """
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    if not 0 <= coefficient_degree <= degree:
        raise ValueError("coefficient_degree must satisfy 0 <= k <= degree")
    if root_tolerance <= 0 or residual_tolerance <= 0:
        raise ValueError("tolerances must be positive")
    k = int(coefficient_degree)

    if k == 0:
        critical_polynomial = derivative_coefficients(coeffs)
    else:
        indices = np.arange(coeffs.size, dtype=float)
        critical_polynomial = (indices - k) * coeffs

    effective = _effective_polynomial(critical_polynomial)
    critical_roots = (
        np.asarray([], dtype=np.complex128)
        if effective.size == 1
        else np.polynomial.polynomial.polyroots(effective)
    )

    persistent_zero = False
    candidates: list[CollisionCandidate] = []
    for raw_root in critical_roots:
        critical = complex(raw_root)
        if abs(critical) <= root_tolerance and k > 0:
            if k == 1 and abs(coeffs[0]) <= residual_tolerance:
                parameter = -coeffs[1]
            elif k > 1 and abs(coeffs[0]) <= residual_tolerance and abs(coeffs[1]) <= residual_tolerance:
                persistent_zero = True
                continue
            else:
                continue
        else:
            denominator = critical**k if k > 0 else 1.0 + 0j
            parameter = -_raw_value(coeffs, critical) / denominator

        augmented = coeffs.copy()
        augmented[k] += parameter
        polynomial_residual = abs(_raw_value(augmented, critical))
        derivative_residual = abs(_raw_derivative_value(augmented, critical))
        candidates.append(
            CollisionCandidate(
                critical_root=critical,
                parameter=complex(parameter),
                polynomial_residual=float(polynomial_residual),
                derivative_residual=float(derivative_residual),
            )
        )

    candidates.sort(
        key=lambda item: (
            round(item.parameter.real, 14),
            round(item.parameter.imag, 14),
            round(item.critical_root.real, 14),
            round(item.critical_root.imag, 14),
        )
    )
    maximum = max(
        (max(item.polynomial_residual, item.derivative_residual) for item in candidates),
        default=0.0,
    )
    infinity_transition = complex(-coeffs[-1]) if k == degree else None
    if maximum > residual_tolerance:
        status = "OAK_WARN_COLLISION_RESIDUAL"
    elif persistent_zero:
        status = "OAK_WARN_PERSISTENT_ZERO_COLLISION"
    else:
        status = "OAK_PASS_SINGLE_COEFFICIENT_COLLISIONS"
    return SingleCoefficientCollisionAtlas(
        degree=degree,
        coefficient_degree=k,
        candidates=tuple(candidates),
        persistent_zero_collision=persistent_zero,
        infinity_transition_parameter=infinity_transition,
        maximum_residual=float(maximum),
        status=status,
    )
