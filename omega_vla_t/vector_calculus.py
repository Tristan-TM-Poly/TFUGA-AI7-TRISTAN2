"""Vector-calculus and discrete exterior-calculus kernels for Ω-VLA-T∞."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import numpy.typing as npt

Array = npt.NDArray[np.float64]


def _validate_spacing(spacing: float | Sequence[float], dimensions: int) -> tuple[float, ...]:
    if np.isscalar(spacing):
        values = (float(spacing),) * dimensions
    else:
        values = tuple(float(value) for value in spacing)
    if len(values) != dimensions or any(value <= 0 for value in values):
        raise ValueError("spacing must contain one positive value per dimension")
    return values


def gradient(field: npt.ArrayLike, *, spacing: float | Sequence[float] = 1.0) -> Array:
    """Return a finite-difference gradient with component axis first."""
    scalar = np.asarray(field, dtype=float)
    if scalar.ndim == 0 or not np.all(np.isfinite(scalar)):
        raise ValueError("field must be a finite scalar grid")
    steps = _validate_spacing(spacing, scalar.ndim)
    derivatives = np.gradient(scalar, *steps, edge_order=1)
    return np.stack(derivatives, axis=0)


def divergence(vector_field: npt.ArrayLike, *, spacing: float | Sequence[float] = 1.0) -> Array:
    """Divergence of a grid vector field whose first axis indexes components."""
    vector = np.asarray(vector_field, dtype=float)
    if vector.ndim < 2 or not np.all(np.isfinite(vector)):
        raise ValueError("vector_field must have shape (dimension, ...grid)")
    dimensions = vector.shape[0]
    if vector.ndim - 1 != dimensions:
        raise ValueError("the grid dimension must equal the number of vector components")
    steps = _validate_spacing(spacing, dimensions)
    result = np.zeros(vector.shape[1:], dtype=float)
    for axis in range(dimensions):
        result += np.gradient(vector[axis], steps[axis], axis=axis, edge_order=1)
    return result


def laplacian(field: npt.ArrayLike, *, spacing: float | Sequence[float] = 1.0) -> Array:
    return divergence(gradient(field, spacing=spacing), spacing=spacing)


def curl_2d(vector_field: npt.ArrayLike, *, spacing: float | Sequence[float] = 1.0) -> Array:
    """Scalar z-component of curl for a two-dimensional vector field."""
    vector = np.asarray(vector_field, dtype=float)
    if vector.ndim != 3 or vector.shape[0] != 2:
        raise ValueError("curl_2d expects shape (2, nx, ny)")
    dx, dy = _validate_spacing(spacing, 2)
    return np.gradient(vector[1], dx, axis=0) - np.gradient(vector[0], dy, axis=1)


def validate_incidence(incidence: npt.ArrayLike) -> Array:
    matrix = np.asarray(incidence, dtype=float)
    if matrix.ndim != 2 or not np.all(np.isfinite(matrix)):
        raise ValueError("incidence must be a finite two-dimensional matrix")
    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("incidence must contain vertices and edges")
    return matrix


def graph_gradient(incidence: npt.ArrayLike, node_potential: npt.ArrayLike) -> Array:
    """Discrete gradient B^T f for a vertex-edge incidence matrix B."""
    matrix = validate_incidence(incidence)
    potential = np.asarray(node_potential, dtype=float)
    if potential.shape != (matrix.shape[0],):
        raise ValueError("node_potential must contain one value per vertex")
    return matrix.T @ potential


def graph_divergence(incidence: npt.ArrayLike, edge_flow: npt.ArrayLike) -> Array:
    """Discrete divergence -B j under the documented orientation convention."""
    matrix = validate_incidence(incidence)
    flow = np.asarray(edge_flow, dtype=float)
    if flow.shape != (matrix.shape[1],):
        raise ValueError("edge_flow must contain one value per edge")
    return -(matrix @ flow)


def graph_laplacian(incidence: npt.ArrayLike, weights: npt.ArrayLike | None = None) -> Array:
    matrix = validate_incidence(incidence)
    if weights is None:
        weight_matrix = np.eye(matrix.shape[1])
    else:
        weight_array = np.asarray(weights, dtype=float)
        if weight_array.shape != (matrix.shape[1],) or np.any(weight_array < 0):
            raise ValueError("weights must be non-negative with one value per edge")
        weight_matrix = np.diag(weight_array)
    return matrix @ weight_matrix @ matrix.T


@dataclass(frozen=True)
class GraphHodgeReport:
    potential: Array
    gradient_flow: Array
    cycle_flow: Array
    reconstruction_error: float
    orthogonality_error: float

    def to_dict(self) -> dict[str, object]:
        return {
            "potential": self.potential.tolist(),
            "gradient_flow": self.gradient_flow.tolist(),
            "cycle_flow": self.cycle_flow.tolist(),
            "reconstruction_error": self.reconstruction_error,
            "orthogonality_error": self.orthogonality_error,
        }


def graph_hodge_decomposition(incidence: npt.ArrayLike, edge_flow: npt.ArrayLike) -> GraphHodgeReport:
    """Least-squares split of an edge flow into gradient and cycle components.

    The additive gauge of the potential is fixed implicitly by the minimum-norm
    least-squares solution.  The cycle component lies numerically in ker(B).
    """
    matrix = validate_incidence(incidence)
    flow = np.asarray(edge_flow, dtype=float)
    if flow.shape != (matrix.shape[1],):
        raise ValueError("edge_flow must contain one value per edge")

    potential, *_ = np.linalg.lstsq(matrix.T, flow, rcond=None)
    gradient_flow = matrix.T @ potential
    cycle_flow = flow - gradient_flow
    reconstruction_error = float(np.linalg.norm(flow - gradient_flow - cycle_flow))
    orthogonality_error = float(abs(gradient_flow @ cycle_flow))
    return GraphHodgeReport(
        potential=potential,
        gradient_flow=gradient_flow,
        cycle_flow=cycle_flow,
        reconstruction_error=reconstruction_error,
        orthogonality_error=orthogonality_error,
    )
