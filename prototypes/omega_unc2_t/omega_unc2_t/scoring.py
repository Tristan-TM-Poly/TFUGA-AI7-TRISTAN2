"""Scoring kernels for Ω-UNC²-T."""

from __future__ import annotations

from collections.abc import Mapping

from .u2_types import U2Claim, clamp01


def weighted_mean(values: Mapping[str, float], weights: Mapping[str, float] | None = None) -> float:
    """Return a clamped weighted mean.

    Empty mappings return 0.0, which means no uncertainty was declared. The OAK
    gate can still penalize missing U1/U2 explicitly.
    """

    if not values:
        return 0.0
    if weights is None:
        return clamp01(sum(clamp01(v) for v in values.values()) / len(values))
    total_weight = 0.0
    total = 0.0
    for key, value in values.items():
        weight = max(0.0, float(weights.get(key, 1.0)))
        total += clamp01(value) * weight
        total_weight += weight
    if total_weight <= 0:
        return 0.0
    return clamp01(total / total_weight)


def confidence_debt(displayed_confidence: float, evidence_strength: float, calibration_strength: float) -> float:
    """Debt accumulated when confidence exceeds evidence + calibration.

    A high confidence with weak evidence/calibration is treated as epistemic debt.
    """

    confidence = clamp01(displayed_confidence)
    support = 0.5 * clamp01(evidence_strength) + 0.5 * clamp01(calibration_strength)
    return clamp01(max(0.0, confidence - support))


def oak_u2_score(
    claim: U2Claim,
    *,
    u1_weights: Mapping[str, float] | None = None,
    u2_weights: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Compute the core Ω-UNC²-T scalar scores.

    risk increases with U1, U2, decision cost and irreversibility.
    maturity increases with evidence and decreases with U1, U2 and residuals.
    priority favors fertile/value-rich claims whose uncertainty deserves testing.
    """

    c = claim.normalized()
    u1 = weighted_mean(c.uncertainty_u1, u1_weights)
    u2 = weighted_mean(c.meta_uncertainty_u2, u2_weights)
    risk = clamp01(u1 * u2 * c.decision_cost * (1.0 - c.reversibility))
    maturity = clamp01(c.evidence_strength / (1.0 + u1 + u2 + c.residual_score))
    debt = confidence_debt(
        displayed_confidence=float(c.metadata.get("displayed_confidence", maturity)),
        evidence_strength=c.evidence_strength,
        calibration_strength=1.0 - u2,
    )
    priority = priority_score(
        risk=risk,
        value=c.value,
        fertility=c.fertility,
        u1=u1,
        u2=u2,
    )
    return {
        "u1": u1,
        "u2": u2,
        "risk": risk,
        "maturity": maturity,
        "confidence_debt": debt,
        "priority": priority,
    }


def priority_score(*, risk: float, value: float, fertility: float, u1: float, u2: float) -> float:
    """Prioritize tests that could reduce valuable/fertile uncertainty."""

    return clamp01((0.40 * clamp01(risk)) + (0.25 * clamp01(value)) + (0.20 * clamp01(fertility)) + (0.15 * clamp01(u1 * u2)))


def decision_fragility_index(sensitivity_to_u1: float, sensitivity_to_u2: float) -> float:
    """Small proxy for how much the preferred action changes if U1/U2 shift."""

    return clamp01(0.5 * clamp01(abs(sensitivity_to_u1)) + 0.5 * clamp01(abs(sensitivity_to_u2)))
