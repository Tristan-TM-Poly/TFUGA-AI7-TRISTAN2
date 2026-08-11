"""Ω-ZETA-CERT-T∞: OAK-safe spectral-certificate research compiler.

The package manages research routes, barriers, negative memory and Problem Atlas
cells. It never promotes numerical or external-reported evidence to a proof of
RH.
"""

from .core import classify_frontier, compile_problem_cells, effective_rank_diagnostic, rank_routes
from .model import (
    BarrierClass,
    CertificateFamily,
    EpistemicStatus,
    FrontierDecision,
    MMinusRecord,
    MomentTensorSpec,
    ResearchBundle,
    ResearchRoute,
)

__all__ = [
    "BarrierClass",
    "CertificateFamily",
    "EpistemicStatus",
    "FrontierDecision",
    "MMinusRecord",
    "MomentTensorSpec",
    "ResearchBundle",
    "ResearchRoute",
    "classify_frontier",
    "compile_problem_cells",
    "effective_rank_diagnostic",
    "rank_routes",
]
