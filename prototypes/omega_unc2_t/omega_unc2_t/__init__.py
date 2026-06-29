"""Ω-UNC²-T — Incertitude de l’Incertitude de Tristan.

This package is a small OAK-safe prototype for scoring claims with first-order
uncertainty U1, second-order uncertainty U2, residuals, decision cost, and
robust action gates.
"""

from .u2_types import EvidencePacket, OAKU2Result, U2Claim
from .scoring import (
    confidence_debt,
    decision_fragility_index,
    oak_u2_score,
    priority_score,
    weighted_mean,
)
from .oak_gate import oak_u2_gate
from .calibration import expected_calibration_error, meta_calibration_error, residual_of_uncertainty
from .domain_radar import domain_shift_score

__all__ = [
    "EvidencePacket",
    "OAKU2Result",
    "U2Claim",
    "confidence_debt",
    "decision_fragility_index",
    "domain_shift_score",
    "expected_calibration_error",
    "meta_calibration_error",
    "oak_u2_gate",
    "oak_u2_score",
    "priority_score",
    "residual_of_uncertainty",
    "weighted_mean",
]
