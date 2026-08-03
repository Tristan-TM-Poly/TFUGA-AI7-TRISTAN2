"""Ω-VLA-T∞ R0.1 — vector calculus and linear algebra of Tristan.

Established mathematics is implemented as deterministic software fixtures.
Tristan extensions remain explicitly labelled as architecture or hypotheses
until formalized, benchmarked, and independently validated.
"""

from .core import LinearOperator, SVDReport, VectorSpace
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
    "OAKCheck",
    "OAKReport",
    "SVDReport",
    "VectorSpace",
    "audit_operator",
    "basis_covariance_error",
    "curl_2d",
    "divergence",
    "gradient",
    "graph_divergence",
    "graph_gradient",
    "graph_hodge_decomposition",
    "graph_laplacian",
    "laplacian",
    "validate_incidence",
]

__version__ = "0.1.0"
