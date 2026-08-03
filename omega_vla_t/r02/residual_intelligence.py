"""Residual Intelligence Engine for bounded numerical diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True)
class ResidualProfile:
    size: int
    mean: float
    standard_deviation: float
    l1_norm: float
    l2_norm: float
    linf_norm: float
    zero_fraction: float
    lag1_autocorrelation: float
    spectral_flatness: float
    dominant_frequency_fraction: float
    outlier_fraction: float
    classification: str
    structured: bool
    candidate_actions: tuple[str, ...]
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _lag1_autocorrelation(values: np.ndarray) -> float:
    if values.size < 2:
        return 0.0
    centered = values - np.mean(values)
    denominator = float(np.dot(centered, centered))
    if denominator <= np.finfo(float).eps:
        return 0.0
    return float(np.dot(centered[:-1], centered[1:]) / denominator)


def _spectral_metrics(values: np.ndarray) -> tuple[float, float]:
    if values.size < 2:
        return 1.0, 0.0
    spectrum = np.abs(np.fft.rfft(values - np.mean(values))) ** 2
    spectrum = spectrum[1:]
    if spectrum.size == 0 or float(np.sum(spectrum)) <= 0.0:
        return 1.0, 0.0
    epsilon = np.finfo(float).tiny
    flatness = float(
        np.exp(np.mean(np.log(spectrum + epsilon)))
        / np.mean(spectrum + epsilon)
    )
    dominant = float(np.max(spectrum) / np.sum(spectrum))
    return flatness, dominant


def _outlier_fraction(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    median = float(np.median(values))
    deviations = np.abs(values - median)
    mad = float(np.median(deviations))
    if mad <= np.finfo(float).eps:
        # A sparse/event-like residual commonly has an exactly zero median and
        # MAD because most entries are identical. Returning zero here hides
        # every nonzero event. Use a scale-aware numerical threshold instead;
        # a constant vector still returns zero while isolated deviations are
        # retained as candidate outliers.
        magnitude = max(float(np.max(np.abs(values), initial=0.0)), 1.0)
        threshold = 32.0 * np.finfo(float).eps * magnitude
        return float(np.mean(deviations > threshold))
    robust_z = 0.6744897501960817 * (values - median) / mad
    return float(np.mean(np.abs(robust_z) > 3.5))


def analyze_residual(
    residual: npt.ArrayLike,
    *,
    zero_tolerance: float = 1e-12,
) -> ResidualProfile:
    """Classify a finite residual using transparent heuristics.

    The classification is a routing aid. It is not a discovery, causal claim or
    proof that a latent variable exists.
    """

    values = np.asarray(residual, dtype=float).reshape(-1)
    if not np.all(np.isfinite(values)):
        raise ValueError("residual entries must be finite")
    if zero_tolerance < 0.0:
        raise ValueError("zero_tolerance cannot be negative")

    size = int(values.size)
    mean = float(np.mean(values)) if size else 0.0
    std = float(np.std(values)) if size else 0.0
    l1 = float(np.linalg.norm(values, ord=1)) if size else 0.0
    l2 = float(np.linalg.norm(values)) if size else 0.0
    linf = float(np.linalg.norm(values, ord=np.inf)) if size else 0.0
    zero_fraction = float(np.mean(np.abs(values) <= zero_tolerance)) if size else 1.0
    autocorr = _lag1_autocorrelation(values)
    flatness, dominant = _spectral_metrics(values)
    outliers = _outlier_fraction(values)

    classification, structured, actions = _classify(
        size=size,
        std=std,
        zero_fraction=zero_fraction,
        autocorr=autocorr,
        flatness=flatness,
        dominant=dominant,
        outliers=outliers,
    )

    return ResidualProfile(
        size=size,
        mean=mean,
        standard_deviation=std,
        l1_norm=l1,
        l2_norm=l2,
        linf_norm=linf,
        zero_fraction=zero_fraction,
        lag1_autocorrelation=autocorr,
        spectral_flatness=flatness,
        dominant_frequency_fraction=dominant,
        outlier_fraction=outliers,
        classification=classification,
        structured=structured,
        candidate_actions=actions,
    )


def _classify(
    *,
    size: int,
    std: float,
    zero_fraction: float,
    autocorr: float,
    flatness: float,
    dominant: float,
    outliers: float,
) -> tuple[str, bool, tuple[str, ...]]:
    if size == 0 or std <= 1e-15:
        return "negligible", False, ("retain current model",)
    if zero_fraction >= 0.85 and outliers > 0.0:
        return (
            "sparse_or_event_like",
            True,
            (
                "inspect localized events",
                "compare robust and sparse models",
                "test boundary or anomaly hypotheses",
            ),
        )
    if abs(autocorr) >= 0.45:
        return (
            "correlated",
            True,
            (
                "inspect missing state variables",
                "test autoregressive or dynamical residual models",
                "audit temporal ordering and regime changes",
            ),
        )
    if dominant >= 0.35 or flatness <= 0.25:
        return (
            "oscillatory_or_multiscale",
            True,
            (
                "inspect Fourier or wavelet structure",
                "test omitted periodic modes",
                "compare FFWT and classical wavelet baselines",
            ),
        )
    if outliers >= 0.03:
        return (
            "heavy_tailed_or_contaminated",
            True,
            (
                "run robust regression",
                "inspect sensor or preprocessing failures",
                "separate contamination from rare structure",
            ),
        )
    return (
        "approximately_unstructured",
        False,
        (
            "compare against a whiteness baseline",
            "retain uncertainty instead of declaring model completeness",
        ),
    )
