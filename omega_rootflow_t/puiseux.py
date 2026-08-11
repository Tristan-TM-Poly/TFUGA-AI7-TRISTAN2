"""Numerical Puiseux diagnostics near polynomial root collisions.

Near a generic multiplicity-m branch point, root displacements often scale as
``|r-r_c| ~ C |t-t_c|**alpha`` with ``alpha=1/m`` in the canonical local model.
This module estimates such an exponent from supplied coefficient samples.

The fitted exponent is empirical evidence for a local scaling regime.  It is
not a proof of multiplicity, analyticity, or a convergent Puiseux expansion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import numpy.typing as npt

from .core import roots

ComplexArray = npt.NDArray[np.complex128]
CoefficientFamily = Callable[[float], npt.ArrayLike]


@dataclass(frozen=True)
class PuiseuxSample:
    parameter: float
    parameter_distance: float
    nearest_root: complex
    root_distance: float


@dataclass(frozen=True)
class PuiseuxFit:
    critical_parameter: float
    critical_root: complex
    exponent: float
    prefactor: float
    r_squared: float
    inferred_reciprocal_integer: int | None
    reciprocal_mismatch: float
    samples: tuple[PuiseuxSample, ...]
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "critical_parameter": self.critical_parameter,
            "critical_root": [float(self.critical_root.real), float(self.critical_root.imag)],
            "exponent": self.exponent,
            "prefactor": self.prefactor,
            "r_squared": self.r_squared,
            "inferred_reciprocal_integer": self.inferred_reciprocal_integer,
            "reciprocal_mismatch": self.reciprocal_mismatch,
            "samples": [
                {
                    "parameter": item.parameter,
                    "parameter_distance": item.parameter_distance,
                    "nearest_root": [float(item.nearest_root.real), float(item.nearest_root.imag)],
                    "root_distance": item.root_distance,
                }
                for item in self.samples
            ],
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def estimate_puiseux_exponent(
    coefficient_family: CoefficientFamily,
    *,
    critical_parameter: float,
    critical_root: complex,
    offsets: npt.ArrayLike,
    minimum_distance: float = 1e-15,
    reciprocal_tolerance: float = 0.08,
) -> PuiseuxFit:
    """Fit ``log|r-r_c| = log C + alpha log|t-t_c|`` for the nearest branch."""
    offset_values = np.asarray(offsets, dtype=float)
    if offset_values.ndim != 1 or offset_values.size < 3:
        raise ValueError("offsets must contain at least three one-dimensional samples")
    if np.any(offset_values == 0.0) or not np.all(np.isfinite(offset_values)):
        raise ValueError("offsets must be finite and non-zero")
    if minimum_distance <= 0 or reciprocal_tolerance <= 0:
        raise ValueError("distance and tolerance parameters must be positive")

    samples: list[PuiseuxSample] = []
    for offset in offset_values:
        parameter = float(critical_parameter + offset)
        rr = roots(coefficient_family(parameter))
        nearest = complex(rr[int(np.argmin(np.abs(rr - critical_root)))])
        distance = float(abs(nearest - critical_root))
        if distance <= minimum_distance:
            raise ValueError("root displacement is too small for logarithmic fitting")
        samples.append(
            PuiseuxSample(
                parameter=parameter,
                parameter_distance=float(abs(offset)),
                nearest_root=nearest,
                root_distance=distance,
            )
        )

    x = np.log(np.asarray([item.parameter_distance for item in samples], dtype=float))
    y = np.log(np.asarray([item.root_distance for item in samples], dtype=float))
    design = np.column_stack([x, np.ones_like(x)])
    slope, intercept = np.linalg.lstsq(design, y, rcond=None)[0]
    predicted = slope * x + intercept
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 if ss_tot <= np.finfo(float).eps else 1.0 - ss_res / ss_tot

    inferred: int | None = None
    mismatch = float("inf")
    if slope > 0:
        candidate = max(1, int(round(1.0 / slope)))
        mismatch = float(abs(slope - 1.0 / candidate))
        if mismatch <= reciprocal_tolerance:
            inferred = candidate

    if r_squared < 0.95:
        status = "OAK_WARN_PUISEUX_POOR_SCALING_FIT"
    elif inferred is None:
        status = "OAK_PASS_PUISEUX_EMPIRICAL_EXPONENT"
    else:
        status = "OAK_PASS_PUISEUX_RECIPROCAL_PATTERN"

    return PuiseuxFit(
        critical_parameter=float(critical_parameter),
        critical_root=complex(critical_root),
        exponent=float(slope),
        prefactor=float(np.exp(intercept)),
        r_squared=float(r_squared),
        inferred_reciprocal_integer=inferred,
        reciprocal_mismatch=mismatch,
        samples=tuple(samples),
        status=status,
    )


def canonical_collision_family(multiplicity: int) -> CoefficientFamily:
    """Return coefficients for the fixture ``z**m - t``."""
    if multiplicity < 2:
        raise ValueError("multiplicity must be >= 2")

    def family(parameter: float) -> ComplexArray:
        coeffs = np.zeros(multiplicity + 1, dtype=np.complex128)
        coeffs[0] = -parameter
        coeffs[-1] = 1.0
        return coeffs

    return family


def canonical_puiseux_fit(
    multiplicity: int,
    *,
    offsets: npt.ArrayLike | None = None,
) -> PuiseuxFit:
    """Fit the canonical ``z**m-t`` branch-point fixture near ``t=0``."""
    if offsets is None:
        offsets = np.logspace(-8, -2, 13)
    return estimate_puiseux_exponent(
        canonical_collision_family(multiplicity),
        critical_parameter=0.0,
        critical_root=0j,
        offsets=offsets,
    )
