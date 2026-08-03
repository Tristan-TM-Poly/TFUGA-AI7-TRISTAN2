"""Ω-VLA-T∞ R0.1 — vector calculus and linear algebra of Tristan.

Established mathematics is implemented as deterministic software fixtures.
Tristan extensions remain explicitly labelled as architecture or hypotheses
until formalized, benchmarked, and independently validated.
"""

from .core import LinearOperator, SVDReport, VectorSpace
from .decompositions import (
    ProjectorAudit,
    SymmetryDecomposition,
    anticommutator,
    audit_orthogonal_projector,
    commutator,
    decompose_symmetric_skew,
    metric_projector,
    orthogonal_projector,
    orthonormal_basis,
    principal_angles,
    projection_residual,
)
from .differential import (
    LinearizationReport,
    audit_linearization,
    directional_derivative,
    gradient_fd,
    hessian,
    jacobian,
    propagate_covariance,
)
from .oak import OAKCheck, OAKReport, audit_operator, basis_covariance_error
from .vector_calculus import (
    GraphHodgeReport,
    curl_2d,
    divergence,
    gradient,
    graph_divergence,
    graph_gradient,
    graph_hodge_decomposition,
    graph_laplacian,
    laplacian,
    validate_incidence,
)

__all__ = [
    "GraphHodgeReport",
    "LinearOperator",
    "LinearizationReport",
    "OAKCheck",
    "OAKReport",
    "ProjectorAudit",
    "SVDReport",
    "SymmetryDecomposition",
    "VectorSpace",
    "anticommutator",
    "audit_linearization",
    "audit_operator",
    "audit_orthogonal_projector",
    "basis_covariance_error",
    "commutator",
    "curl_2d",
    "decompose_symmetric_skew",
    "directional_derivative",
    "divergence",
    "gradient",
    "gradient_fd",
    "graph_divergence",
    "graph_gradient",
    "graph_hodge_decomposition",
    "graph_laplacian",
    "hessian",
    "jacobian",
    "laplacian",
    "metric_projector",
    "orthogonal_projector",
    "orthonormal_basis",
    "principal_angles",
    "projection_residual",
    "propagate_covariance",
    "validate_incidence",
]

__version__ = "0.1.0"
