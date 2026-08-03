"""Ω-SUITE-FORM-T∞ R0.1.

Exact finite-prefix discovery for Newton polynomials, minimal linear
recurrences and rational generating functions, with explicit OAK evidence
levels and no claim that finite agreement proves a global identity.
"""
from .discover import discover_forms
from .exact import as_fraction, normalize_terms
from .finite import detect_newton_polynomial, difference_table, evaluate_newton
from .models import CandidateKind, DiscoveryReport, FormCandidate, OAKLevel, ValidationSummary
from .recurrence import (
    detect_linear_recurrence,
    rational_generating_coefficients,
    recurrence_value,
    verify_recurrence,
)

__all__ = [
    "CandidateKind",
    "DiscoveryReport",
    "FormCandidate",
    "OAKLevel",
    "ValidationSummary",
    "as_fraction",
    "detect_linear_recurrence",
    "detect_newton_polynomial",
    "difference_table",
    "discover_forms",
    "evaluate_newton",
    "normalize_terms",
    "rational_generating_coefficients",
    "recurrence_value",
    "verify_recurrence",
]

__version__ = "0.1.0"
