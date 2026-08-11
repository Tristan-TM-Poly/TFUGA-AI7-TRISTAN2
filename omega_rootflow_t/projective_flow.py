"""Projective root continuation across polynomial degree transitions.

R0.1-R0.3 treat finite simple-root differentials and projective spectra as
separate layers.  This module bridges them numerically by matching root divisors
in CP^1 with chordal distance.  It can therefore keep a branch finite when
appropriate and let another branch converge continuously to [1:0] as a leading
coefficient vanishes.

The matcher is deliberately metric/numerical: it does not claim analytic
continuation through a singular discriminant.  It compactifies infinity and
makes degree transitions observable without floating-point overflow being the
representation itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

import numpy as np
import numpy.typing as npt

from .projective import ProjectiveRoot, ProjectiveSpectrum, chordal_distance, projective_roots

ComplexArray = npt.NDArray[np.complex128]


def match_projective_roots(
    reference: tuple[ProjectiveRoot, ...],
    candidates: tuple[ProjectiveRoot, ...],
) -> tuple[ProjectiveRoot, ...]:
    """Reorder a nominal-degree divisor by minimum total chordal distance."""
    if len(reference) != len(candidates):
        raise ValueError("reference and candidates must have equal nominal degree")
    count = len(reference)
    if count <= 8:
        best_perm: tuple[int, ...] | None = None
        best_cost = float("inf")
        for perm in permutations(range(count)):
            cost = float(
                sum(chordal_distance(reference[i], candidates[perm[i]]) for i in range(count))
            )
            if cost < best_cost:
                best_cost = cost
                best_perm = tuple(int(index) for index in perm)
        assert best_perm is not None
        return tuple(candidates[index] for index in best_perm)

    remaining = list(range(count))
    ordered: list[ProjectiveRoot] = []
    for root in reference:
        index = min(remaining, key=lambda j: (chordal_distance(root, candidates[j]), j))
        ordered.append(candidates[index])
        remaining.remove(index)
    return tuple(ordered)


@dataclass(frozen=True)
class ProjectiveFlowStep:
    parameter: float
    coefficients: ComplexArray
    roots: tuple[ProjectiveRoot, ...]
    infinity_multiplicity: int
    maximum_branch_step: float
    total_branch_step: float
    maximum_homogeneous_residual: float

    def to_dict(self) -> dict[str, object]:
        return {
            "parameter": self.parameter,
            "coefficients": [[float(z.real), float(z.imag)] for z in self.coefficients],
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
            "infinity_multiplicity": self.infinity_multiplicity,
            "maximum_branch_step": self.maximum_branch_step,
            "total_branch_step": self.total_branch_step,
            "maximum_homogeneous_residual": self.maximum_homogeneous_residual,
        }


@dataclass(frozen=True)
class ProjectiveFlowResult:
    steps: tuple[ProjectiveFlowStep, ...]
    maximum_branch_step: float
    degree_transition_count: int
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def final_roots(self) -> tuple[ProjectiveRoot, ...]:
        return self.steps[-1].roots

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "maximum_branch_step": self.maximum_branch_step,
            "degree_transition_count": self.degree_transition_count,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def track_projective_path(
    coefficient_path: npt.ArrayLike,
    *,
    coefficient_tolerance: float = 0.0,
) -> ProjectiveFlowResult:
    """Track a fixed nominal-degree root divisor along supplied coefficient samples.

    Each row of ``coefficient_path`` has the same nominal degree.  Leading
    coefficients may become exactly zero, in which case projective roots at
    infinity appear instead of changing the divisor cardinality.
    """
    path = np.asarray(coefficient_path, dtype=np.complex128)
    if path.ndim != 2 or path.shape[0] < 2 or path.shape[1] < 2:
        raise ValueError("coefficient_path must be a 2D array with >=2 samples and >=2 coefficients")
    if coefficient_tolerance < 0:
        raise ValueError("coefficient_tolerance must be non-negative")

    spectra = [projective_roots(row, coefficient_tolerance=coefficient_tolerance) for row in path]
    nominal = spectra[0].nominal_degree
    if any(item.nominal_degree != nominal for item in spectra):
        raise ValueError("all coefficient samples must share one nominal degree")

    ordered = spectra[0].roots
    records: list[ProjectiveFlowStep] = [
        ProjectiveFlowStep(
            parameter=0.0,
            coefficients=path[0].copy(),
            roots=ordered,
            infinity_multiplicity=spectra[0].infinity_multiplicity,
            maximum_branch_step=0.0,
            total_branch_step=0.0,
            maximum_homogeneous_residual=spectra[0].maximum_homogeneous_residual,
        )
    ]
    global_maximum = 0.0
    transitions = 0

    for index in range(1, len(spectra)):
        spectrum: ProjectiveSpectrum = spectra[index]
        matched = match_projective_roots(ordered, spectrum.roots)
        distances = np.asarray(
            [chordal_distance(ordered[j], matched[j]) for j in range(nominal)],
            dtype=float,
        )
        maximum = float(np.max(distances)) if distances.size else 0.0
        total = float(np.sum(distances))
        global_maximum = max(global_maximum, maximum)
        if spectrum.infinity_multiplicity != spectra[index - 1].infinity_multiplicity:
            transitions += 1
        ordered = matched
        records.append(
            ProjectiveFlowStep(
                parameter=float(index / (len(spectra) - 1)),
                coefficients=path[index].copy(),
                roots=ordered,
                infinity_multiplicity=spectrum.infinity_multiplicity,
                maximum_branch_step=maximum,
                total_branch_step=total,
                maximum_homogeneous_residual=spectrum.maximum_homogeneous_residual,
            )
        )

    status = (
        "OAK_PASS_PROJECTIVE_DEGREE_FLOW"
        if transitions > 0
        else "OAK_PASS_PROJECTIVE_FLOW"
    )
    return ProjectiveFlowResult(
        steps=tuple(records),
        maximum_branch_step=global_maximum,
        degree_transition_count=transitions,
        status=status,
    )


def cubic_degree_collapse_path(samples: int = 33) -> ComplexArray:
    """Fixture ``epsilon*z^3 + z^2 - 1`` with epsilon -> 0.

    Two roots remain near ±1 while the third branch moves to projective infinity.
    The endpoint keeps nominal degree three with a zero cubic coefficient.
    """
    if samples < 3:
        raise ValueError("samples must be >= 3")
    epsilon = np.linspace(1.0, 0.0, samples)
    return np.asarray(
        [[-1.0 + 0j, 0j, 1.0 + 0j, complex(value)] for value in epsilon],
        dtype=np.complex128,
    )
