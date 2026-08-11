"""Projective polynomial roots and degree transitions for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

ComplexArray = npt.NDArray[np.complex128]


def _projective_coefficients(values: npt.ArrayLike) -> ComplexArray:
    coeffs = np.asarray(values, dtype=np.complex128)
    if coeffs.ndim != 1 or coeffs.size < 2:
        raise ValueError("coefficients must be a one-dimensional nominal-degree vector")
    if not np.all(np.isfinite(coeffs.real)) or not np.all(np.isfinite(coeffs.imag)):
        raise ValueError("coefficients must be finite")
    if np.all(coeffs == 0):
        raise ValueError("the zero polynomial has no well-defined projective root divisor")
    return coeffs


def homogeneous_value(coefficients: npt.ArrayLike, u: complex, v: complex) -> complex:
    """Evaluate the homogenization F(u,v)=sum_k a_k u^k v^(n-k)."""
    coeffs = _projective_coefficients(coefficients)
    degree = coeffs.size - 1
    return complex(sum(coeffs[k] * u**k * v ** (degree - k) for k in range(coeffs.size)))


@dataclass(frozen=True)
class ProjectiveRoot:
    u: complex
    v: complex
    at_infinity: bool

    @property
    def affine(self) -> complex | None:
        if self.at_infinity or self.v == 0:
            return None
        return self.u / self.v

    def normalized(self) -> "ProjectiveRoot":
        norm = float(np.sqrt(abs(self.u) ** 2 + abs(self.v) ** 2))
        if norm == 0:
            raise ValueError("projective coordinate [0:0] is invalid")
        return ProjectiveRoot(self.u / norm, self.v / norm, self.at_infinity)


@dataclass(frozen=True)
class ProjectiveSpectrum:
    nominal_degree: int
    effective_degree: int
    infinity_multiplicity: int
    roots: tuple[ProjectiveRoot, ...]
    maximum_homogeneous_residual: float
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def finite_roots(self) -> ComplexArray:
        return np.asarray(
            [root.affine for root in self.roots if not root.at_infinity],
            dtype=np.complex128,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "nominal_degree": self.nominal_degree,
            "effective_degree": self.effective_degree,
            "infinity_multiplicity": self.infinity_multiplicity,
            "roots": [
                {
                    "u": [float(root.u.real), float(root.u.imag)],
                    "v": [float(root.v.real), float(root.v.imag)],
                    "at_infinity": root.at_infinity,
                    "affine": None
                    if root.affine is None
                    else [float(root.affine.real), float(root.affine.imag)],
                }
                for root in self.roots
            ],
            "maximum_homogeneous_residual": self.maximum_homogeneous_residual,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def projective_roots(
    coefficients: npt.ArrayLike,
    *,
    coefficient_tolerance: float = 0.0,
) -> ProjectiveSpectrum:
    """Return the nominal-degree root divisor in CP^1, including infinity.

    Trailing high-degree coefficients may vanish.  If the nominal degree is n
    but the effective affine degree is m<n, the missing n-m roots are represented
    at ``[1:0]`` rather than being silently dropped.
    """
    coeffs = _projective_coefficients(coefficients)
    if coefficient_tolerance < 0:
        raise ValueError("coefficient_tolerance must be non-negative")
    active = np.where(np.abs(coeffs) > coefficient_tolerance)[0]
    if active.size == 0:
        raise ValueError("all coefficients fall below coefficient_tolerance")
    nominal_degree = coeffs.size - 1
    effective_degree = int(active[-1])
    infinity_multiplicity = nominal_degree - effective_degree

    projective: list[ProjectiveRoot] = []
    if effective_degree > 0:
        finite_coeffs = coeffs[: effective_degree + 1]
        finite = np.polynomial.polynomial.polyroots(finite_coeffs)
        projective.extend(
            ProjectiveRoot(complex(root), 1.0 + 0j, False).normalized()
            for root in finite
        )
    projective.extend(
        ProjectiveRoot(1.0 + 0j, 0j, True)
        for _ in range(infinity_multiplicity)
    )

    residuals = [
        abs(homogeneous_value(coeffs, root.u, root.v))
        for root in projective
    ]
    maximum_residual = float(max(residuals)) if residuals else 0.0
    status = (
        "OAK_PROJECTIVE_DEGREE_TRANSITION"
        if infinity_multiplicity > 0
        else "OAK_PASS_PROJECTIVE_FINITE_SPECTRUM"
    )
    return ProjectiveSpectrum(
        nominal_degree=nominal_degree,
        effective_degree=effective_degree,
        infinity_multiplicity=infinity_multiplicity,
        roots=tuple(projective),
        maximum_homogeneous_residual=maximum_residual,
        status=status,
    )


def chordal_distance(first: ProjectiveRoot, second: ProjectiveRoot) -> float:
    """Fubini-Study chordal distance proxy on CP^1 in homogeneous coordinates."""
    a = first.normalized()
    b = second.normalized()
    numerator = abs(a.u * b.v - a.v * b.u)
    return float(numerator)
