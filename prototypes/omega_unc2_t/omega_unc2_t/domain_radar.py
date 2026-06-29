"""Domain-shift radar for Ω-UNC²-T."""

from __future__ import annotations

from collections.abc import Mapping

from .u2_types import clamp01

DEFAULT_WEIGHTS = {
    "out_of_domain": 0.20,
    "model_disagreement": 0.18,
    "residual_anomaly": 0.18,
    "source_gap": 0.16,
    "residual_volatility": 0.14,
    "novelty": 0.14,
}


def domain_shift_score(signals: Mapping[str, float], weights: Mapping[str, float] | None = None) -> float:
    """Estimate when a claim may be outside its reliable validity domain.

    This is an OAK-safe caution score. It does not prove the claim false; it
    says that stronger evidence, baselines or human review may be needed.
    """

    active_weights = dict(DEFAULT_WEIGHTS)
    if weights:
        active_weights.update({k: max(0.0, float(v)) for k, v in weights.items()})

    total_weight = 0.0
    total = 0.0
    for key, weight in active_weights.items():
        total += clamp01(signals.get(key, 0.0)) * weight
        total_weight += weight
    if total_weight <= 0:
        return 0.0
    return clamp01(total / total_weight)
