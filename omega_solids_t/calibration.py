from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import fmean
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class CalibrationPoint:
    reference: float
    observed: float
    standard_uncertainty: float | None = None
    conditions: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.standard_uncertainty is not None and self.standard_uncertainty <= 0:
            raise ValueError("Standard uncertainty must be positive")


@dataclass(frozen=True, slots=True)
class LinearCalibration:
    slope: float
    intercept: float
    residual_standard_deviation: float
    r_squared: float
    count: int

    def predict(self, observed: float) -> float:
        return self.slope * observed + self.intercept

    def residual(self, point: CalibrationPoint) -> float:
        return point.reference - self.predict(point.observed)

    def to_dict(self) -> dict[str, float | int]:
        return {
            "slope": self.slope,
            "intercept": self.intercept,
            "residual_standard_deviation": self.residual_standard_deviation,
            "r_squared": self.r_squared,
            "count": self.count,
        }


def fit_linear_calibration(points: Iterable[CalibrationPoint]) -> LinearCalibration:
    data = tuple(points)
    if len(data) < 2:
        raise ValueError("At least two calibration points are required")
    x = [point.observed for point in data]
    y = [point.reference for point in data]
    x_mean = fmean(x)
    y_mean = fmean(y)
    denominator = sum((value - x_mean) ** 2 for value in x)
    if denominator == 0:
        raise ValueError("Observed calibration values must not all be equal")
    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)) / denominator
    intercept = y_mean - slope * x_mean
    predicted = [slope * value + intercept for value in x]
    residuals = [yi - estimate for yi, estimate in zip(y, predicted)]
    residual_sum = sum(value**2 for value in residuals)
    total_sum = sum((value - y_mean) ** 2 for value in y)
    r_squared = 1.0 if total_sum == 0 else max(0.0, 1.0 - residual_sum / total_sum)
    degrees = max(1, len(data) - 2)
    residual_standard_deviation = math.sqrt(residual_sum / degrees)
    return LinearCalibration(
        slope,
        intercept,
        residual_standard_deviation,
        r_squared,
        len(data),
    )


@dataclass(frozen=True, slots=True)
class InstrumentAgreement:
    bias: float
    mean_absolute_error: float
    root_mean_square_error: float
    normalized_rmse: float | None
    coverage_within_uncertainty: float | None

    def to_dict(self) -> dict[str, float | None]:
        return {
            "bias": self.bias,
            "mean_absolute_error": self.mean_absolute_error,
            "root_mean_square_error": self.root_mean_square_error,
            "normalized_rmse": self.normalized_rmse,
            "coverage_within_uncertainty": self.coverage_within_uncertainty,
        }


def compare_instruments(
    reference: Sequence[float],
    candidate: Sequence[float],
    *,
    combined_standard_uncertainty: Sequence[float] | None = None,
) -> InstrumentAgreement:
    if len(reference) != len(candidate) or not reference:
        raise ValueError("Instrument series must be non-empty and equal length")
    residuals = [float(value) - float(target) for target, value in zip(reference, candidate)]
    bias = fmean(residuals)
    mae = fmean(abs(value) for value in residuals)
    rmse = math.sqrt(fmean(value**2 for value in residuals))
    data_range = max(reference) - min(reference)
    normalized = None if data_range == 0 else rmse / data_range
    coverage = None
    if combined_standard_uncertainty is not None:
        if len(combined_standard_uncertainty) != len(reference):
            raise ValueError("Uncertainty series length must match data series")
        if any(value <= 0 for value in combined_standard_uncertainty):
            raise ValueError("Combined standard uncertainties must be positive")
        coverage = sum(
            abs(residual) <= 1.96 * uncertainty
            for residual, uncertainty in zip(residuals, combined_standard_uncertainty)
        ) / len(residuals)
    return InstrumentAgreement(bias, mae, rmse, normalized, coverage)
