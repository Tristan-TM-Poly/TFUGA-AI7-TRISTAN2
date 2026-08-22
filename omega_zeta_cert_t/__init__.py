"""Ω-ZETA-CERT-T∞: OAK-safe spectral-certificate research compiler.

R0.2 adds noncommutative/cyclic moment words, Fourier-support debt,
theorem-obligation compilation, exact countermodels and caller-supplied
dual-sensitivity VOI. Nothing in this package promotes numerical or
external-reported evidence to a proof of RH.
"""

from .core import (
    classify_frontier,
    compile_problem_cells,
    effective_rank_diagnostic,
    minimal_order_for_observable_budget,
    rank_routes,
)
from .debt import (
    DebtStatus,
    DualSensitivity,
    SupportDebt,
    TheoremObligation,
    compile_support_debt,
    compile_theorem_obligations,
    rank_sensitivities,
)
from .dual import (
    IntervalPolynomialCheck,
    RationalPolynomial,
    SpectralDualCertificate,
    moments_from_exact_spectrum,
    synthetic_dual_fixture,
)
from .formal import FormalTheoremSpec, build_finite_certificate_theorem_spec
from .model import (
    BarrierClass,
    CertificateFamily,
    EpistemicStatus,
    FrontierDecision,
    MMinusRecord,
    MomentTensorSpec,
    MomentWordMode,
    ResearchBundle,
    ResearchRoute,
    necklace_count,
)
from .moments import (
    canonical_cyclic_word,
    cyclic_word_representatives,
    moment_coordinate_labels,
    noncommutative_trace_countermodel,
)

__all__ = [
    "BarrierClass",
    "CertificateFamily",
    "DebtStatus",
    "DualSensitivity",
    "FormalTheoremSpec",
    "IntervalPolynomialCheck",
    "EpistemicStatus",
    "FrontierDecision",
    "MMinusRecord",
    "MomentTensorSpec",
    "RationalPolynomial",
    "MomentWordMode",
    "ResearchBundle",
    "ResearchRoute",
    "SpectralDualCertificate",
    "SupportDebt",
    "TheoremObligation",
    "build_finite_certificate_theorem_spec",
    "canonical_cyclic_word",
    "classify_frontier",
    "compile_problem_cells",
    "compile_support_debt",
    "compile_theorem_obligations",
    "cyclic_word_representatives",
    "effective_rank_diagnostic",
    "minimal_order_for_observable_budget",
    "moments_from_exact_spectrum",
    "moment_coordinate_labels",
    "necklace_count",
    "noncommutative_trace_countermodel",
    "rank_routes",
    "rank_sensitivities",
    "synthetic_dual_fixture",
]
