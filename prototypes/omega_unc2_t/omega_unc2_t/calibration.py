"""Calibration metrics for Ω-UNC²-T."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .u2_types import clamp01


def expected_calibration_error(
    confidences: Sequence[float],
    outcomes: Sequence[bool],
    *,
    bins: int = 10,
) -> float:
    """Compute a simple Expected Calibration Error (ECE1).

    If a model says 0.80 confidence, it should be correct about 80% of the time.
    """

    if len(confidences) != len(outcomes):
        raise ValueError("confidences and outcomes must have the same length")
    if not confidences:
        return 0.0
    bins = max(1, int(bins))
    total = len(confidences)
    ece = 0.0
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        members = [i for i, c in enumerate(confidences) if low <= clamp01(c) < high or (index == bins - 1 and clamp01(c) == 1.0)]
        if not members:
            continue
        avg_conf = sum(clamp01(confidences[i]) for i in members) / len(members)
        accuracy = sum(1.0 for i in members if outcomes[i]) / len(members)
        ece += (len(members) / total) * abs(avg_conf - accuracy)
    return clamp01(ece)


def meta_calibration_error(
    meta_confidences: Sequence[float],
    calibration_was_good: Sequence[bool],
    *,
    bins: int = 10,
) -> float:
    """Compute ECE2: calibration of the calibration confidence itself."""

    return expected_calibration_error(meta_confidences, calibration_was_good, bins=bins)


def residual_of_uncertainty(observed_errors: Iterable[float], predicted_u1: Iterable[float]) -> dict[str, float]:
    """Return residual-of-uncertainty diagnostics.

    RU = max(0, |observed_error| - predicted_u1). Positive values mean U1
    understated the real error. The mean is a direct overconfidence signal.
    """

    errors = [abs(float(x)) for x in observed_errors]
    predicted = [max(0.0, float(x)) for x in predicted_u1]
    if len(errors) != len(predicted):
        raise ValueError("observed_errors and predicted_u1 must have the same length")
    if not errors:
        return {"mean_ru": 0.0, "max_ru": 0.0, "coverage": 1.0}

    residuals = [max(0.0, err - pred) for err, pred in zip(errors, predicted, strict=True)]
    covered = sum(1 for err, pred in zip(errors, predicted, strict=True) if err <= pred)
    return {
        "mean_ru": sum(residuals) / len(residuals),
        "max_ru": max(residuals),
        "coverage": covered / len(errors),
    }
