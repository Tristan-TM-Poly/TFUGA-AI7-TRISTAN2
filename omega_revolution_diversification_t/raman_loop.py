"""Deterministic Raman discovery-loop demonstrator.

This module implements a small analytic benchmark around Lorentzian peaks,
baseline drift, shift, broadening and model comparison.  It is an executable
research fixture, not a replacement for calibrated spectroscopy workflows.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import math
import random
from statistics import mean
from typing import Any, Iterable, Sequence

from .models import MMinusRule, OakStatus, Quantity, stable_id


class RamanModelKind(str, Enum):
    SHIFT_ONLY = "shift_only"
    SHIFT_BROADENING = "shift_broadening"
    SHIFT_BROADENING_BASELINE = "shift_broadening_baseline"


@dataclass(frozen=True)
class Peak:
    center: float
    width: float
    area: float

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not math.isfinite(self.center):
            errors.append("peak center must be finite")
        if not math.isfinite(self.width) or self.width <= 0:
            errors.append("peak width must be finite and positive")
        if not math.isfinite(self.area) or self.area < 0:
            errors.append("peak area must be finite and non-negative")
        return errors


@dataclass(frozen=True)
class Spectrum:
    x: tuple[float, ...]
    y: tuple[float, ...]
    condition: float
    unit_x: str = "cm^-1"
    unit_y: str = "a.u."

    def validate(self) -> list[str]:
        errors: list[str] = []
        if len(self.x) != len(self.y) or len(self.x) < 5:
            errors.append("spectrum x/y lengths must match and contain at least five points")
        if any(not math.isfinite(v) for v in self.x + self.y):
            errors.append("spectrum values must be finite")
        if any(b <= a for a, b in zip(self.x, self.x[1:])):
            errors.append("spectrum x must be strictly increasing")
        if not self.unit_x.strip() or not self.unit_y.strip():
            errors.append("spectrum units are required")
        return errors


@dataclass(frozen=True)
class RamanCandidate:
    kind: RamanModelKind
    shift_per_condition: float
    broadening_per_condition: float
    baseline_slope_per_condition: float
    training_rmse: float
    holdout_rmse: float
    parameter_count: int
    score: float
    candidate_id: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data


@dataclass(frozen=True)
class DiscriminatingExperiment:
    condition: float
    expected_divergence: float
    compared_candidates: tuple[str, str]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RamanLoopResult:
    best_candidate: RamanCandidate
    baseline_rmse: float
    candidates: tuple[RamanCandidate, ...]
    experiment: DiscriminatingExperiment
    oak_transition: tuple[str, str]
    m_minus: tuple[MMinusRule, ...]
    quantities: dict[str, Quantity]
    boundary: str = (
        "The Raman loop is a deterministic synthetic benchmark. A favorable score "
        "does not establish molecular identity, causal mechanism, or instrument validity."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "best_candidate": self.best_candidate.to_dict(),
            "baseline_rmse": self.baseline_rmse,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "experiment": self.experiment.to_dict(),
            "oak_transition": list(self.oak_transition),
            "m_minus": [rule.to_dict() for rule in self.m_minus],
            "quantities": {key: value.to_dict() for key, value in self.quantities.items()},
            "boundary": self.boundary,
        }


def lorentzian(x: float, peak: Peak) -> float:
    gamma = peak.width / 2.0
    return peak.area * (gamma / math.pi) / ((x - peak.center) ** 2 + gamma**2)


def render_spectrum(
    x: Sequence[float],
    peaks: Sequence[Peak],
    *,
    condition: float,
    shift_per_condition: float = 0.0,
    broadening_per_condition: float = 0.0,
    baseline_offset: float = 0.0,
    baseline_slope_per_condition: float = 0.0,
    noise_std: float = 0.0,
    seed: int = 0,
) -> Spectrum:
    if not x:
        raise ValueError("x grid is required")
    for peak in peaks:
        errors = peak.validate()
        if errors:
            raise ValueError("; ".join(errors))
    rng = random.Random(seed)
    x_mid = (x[0] + x[-1]) / 2.0
    values: list[float] = []
    for coordinate in x:
        intensity = baseline_offset + baseline_slope_per_condition * condition * (
            coordinate - x_mid
        )
        for peak in peaks:
            transformed = Peak(
                center=peak.center + shift_per_condition * condition,
                width=max(1e-9, peak.width + broadening_per_condition * condition),
                area=peak.area,
            )
            intensity += lorentzian(coordinate, transformed)
        if noise_std:
            intensity += rng.gauss(0.0, noise_std)
        values.append(intensity)
    spectrum = Spectrum(tuple(float(v) for v in x), tuple(values), float(condition))
    errors = spectrum.validate()
    if errors:
        raise ValueError("; ".join(errors))
    return spectrum


def rmse(actual: Sequence[float], predicted: Sequence[float]) -> float:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("actual/predicted lengths must match and be non-empty")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(actual, predicted)) / len(actual))


def _predict_from_reference(
    reference: Spectrum,
    peaks: Sequence[Peak],
    condition: float,
    shift: float,
    broadening: float,
    baseline_slope: float,
) -> tuple[float, ...]:
    # The synthetic benchmark knows the analytic peak family but not the true
    # parameter rates.  This mirrors a physics-informed fit without claiming
    # that real spectra are exactly Lorentzian.
    x_mid = (reference.x[0] + reference.x[-1]) / 2.0
    baseline_offset = min(reference.y)
    predicted: list[float] = []
    for coordinate in reference.x:
        value = baseline_offset + baseline_slope * condition * (coordinate - x_mid)
        for peak in peaks:
            transformed = Peak(
                center=peak.center + shift * condition,
                width=max(1e-9, peak.width + broadening * condition),
                area=peak.area,
            )
            value += lorentzian(coordinate, transformed)
        predicted.append(value)
    return tuple(predicted)


def _candidate_grid(kind: RamanModelKind) -> Iterable[tuple[float, float, float]]:
    # The compact grid contains the canonical fixture values exactly while
    # avoiding thousands of redundant combinations in repeated CI commands.
    shifts = [round(-0.10 + 0.01 * i, 3) for i in range(13)]
    broadenings = [0.0] if kind is RamanModelKind.SHIFT_ONLY else [
        round(-0.01 + 0.01 * i, 3) for i in range(7)
    ]
    slopes = [0.0]
    if kind is RamanModelKind.SHIFT_BROADENING_BASELINE:
        slopes = [round(0.0001 * i, 7) for i in range(7)]
    for shift in shifts:
        for broadening in broadenings:
            for slope in slopes:
                yield shift, broadening, slope


def fit_candidate(
    kind: RamanModelKind,
    reference: Spectrum,
    training: Sequence[Spectrum],
    holdout: Spectrum,
    peaks: Sequence[Peak],
) -> RamanCandidate:
    if not training:
        raise ValueError("at least one training spectrum is required")
    best: tuple[float, float, float, float] | None = None
    for shift, broadening, slope in _candidate_grid(kind):
        errors = []
        for spectrum in training:
            prediction = _predict_from_reference(
                reference,
                peaks,
                spectrum.condition,
                shift,
                broadening,
                slope,
            )
            errors.append(rmse(spectrum.y, prediction))
        training_error = mean(errors)
        if best is None or training_error < best[3]:
            best = (shift, broadening, slope, training_error)
    assert best is not None
    shift, broadening, slope, training_error = best
    holdout_prediction = _predict_from_reference(
        reference, peaks, holdout.condition, shift, broadening, slope
    )
    holdout_error = rmse(holdout.y, holdout_prediction)
    parameter_count = {
        RamanModelKind.SHIFT_ONLY: 1,
        RamanModelKind.SHIFT_BROADENING: 2,
        RamanModelKind.SHIFT_BROADENING_BASELINE: 3,
    }[kind]
    # Penalize unnecessary parameters on a transparent scale.
    score = holdout_error * (1.0 + 0.03 * parameter_count)
    candidate_id = stable_id(
        "raman-candidate",
        {
            "kind": kind.value,
            "shift": shift,
            "broadening": broadening,
            "slope": slope,
            "training": round(training_error, 12),
            "holdout": round(holdout_error, 12),
        },
    )
    return RamanCandidate(
        kind=kind,
        shift_per_condition=shift,
        broadening_per_condition=broadening,
        baseline_slope_per_condition=slope,
        training_rmse=training_error,
        holdout_rmse=holdout_error,
        parameter_count=parameter_count,
        score=score,
        candidate_id=candidate_id,
    )


def naive_baseline_rmse(training: Sequence[Spectrum], holdout: Spectrum) -> float:
    if not training:
        raise ValueError("training spectra are required")
    nearest = min(training, key=lambda spectrum: abs(spectrum.condition - holdout.condition))
    return rmse(holdout.y, nearest.y)


def propose_discriminating_experiment(
    candidates: Sequence[RamanCandidate],
    reference: Spectrum,
    peaks: Sequence[Peak],
    candidate_conditions: Sequence[float],
) -> DiscriminatingExperiment:
    if len(candidates) < 2:
        raise ValueError("at least two candidates are required")
    first, second = sorted(candidates, key=lambda item: item.score)[:2]
    best_condition = candidate_conditions[0]
    best_divergence = -1.0
    for condition in candidate_conditions:
        first_prediction = _predict_from_reference(
            reference,
            peaks,
            condition,
            first.shift_per_condition,
            first.broadening_per_condition,
            first.baseline_slope_per_condition,
        )
        second_prediction = _predict_from_reference(
            reference,
            peaks,
            condition,
            second.shift_per_condition,
            second.broadening_per_condition,
            second.baseline_slope_per_condition,
        )
        divergence = rmse(first_prediction, second_prediction)
        if divergence > best_divergence:
            best_divergence = divergence
            best_condition = condition
    return DiscriminatingExperiment(
        condition=best_condition,
        expected_divergence=best_divergence,
        compared_candidates=(first.candidate_id, second.candidate_id),
        rationale=(
            "Select the bounded condition with the largest predicted RMSE "
            "between the two leading mechanism classes."
        ),
    )


def run_raman_loop(
    reference: Spectrum,
    training: Sequence[Spectrum],
    holdout: Spectrum,
    peaks: Sequence[Peak],
) -> RamanLoopResult:
    for spectrum in [reference, *training, holdout]:
        errors = spectrum.validate()
        if errors:
            raise ValueError("; ".join(errors))
    candidates = tuple(
        sorted(
            (
                fit_candidate(kind, reference, training, holdout, peaks)
                for kind in RamanModelKind
            ),
            key=lambda item: (item.score, item.kind.value),
        )
    )
    baseline_error = naive_baseline_rmse(training, holdout)
    best = candidates[0]
    m_minus: list[MMinusRule] = []
    if best.holdout_rmse < baseline_error:
        transition = (OakStatus.SIMULATED.value, OakStatus.DEMONSTRATED.value)
    else:
        transition = (OakStatus.SIMULATED.value, OakStatus.REFUTED.value)
        m_minus.append(
            MMinusRule(
                trigger=f"{best.kind.value} loses to nearest-condition baseline",
                root_cause="Candidate does not improve holdout RMSE under the fixture.",
                forbidden_inference=(
                    "Do not claim superiority from training fit or mechanistic elegance alone."
                ),
                safe_replacement=(
                    "Retain the baseline, inspect residual structure, and add a discriminating condition."
                ),
                prevention_test="holdout_rmse < baseline_rmse",
                domain="raman-synthetic",
                severity=3,
                source_event_ids=(best.candidate_id,),
            )
        )
    experiment = propose_discriminating_experiment(
        candidates,
        reference,
        peaks,
        candidate_conditions=(1.5, 2.0, 2.5, 3.0, 4.0),
    )
    return RamanLoopResult(
        best_candidate=best,
        baseline_rmse=baseline_error,
        candidates=candidates,
        experiment=experiment,
        oak_transition=transition,
        m_minus=tuple(m_minus),
        quantities={
            "best_holdout_rmse": Quantity(best.holdout_rmse, "a.u."),
            "baseline_rmse": Quantity(baseline_error, "a.u."),
            "experiment_condition": Quantity(experiment.condition, "relative_condition"),
            "expected_model_divergence": Quantity(
                experiment.expected_divergence, "a.u."
            ),
        },
    )


def canonical_raman_fixture() -> tuple[Spectrum, tuple[Spectrum, ...], Spectrum, tuple[Peak, ...]]:
    x = tuple(960.0 + 1.0 * i for i in range(161))
    peaks = (
        Peak(center=1005.0, width=5.0, area=16.0),
        Peak(center=1060.0, width=8.0, area=11.0),
    )
    reference = render_spectrum(x, peaks, condition=0.0, baseline_offset=0.08, seed=1)
    parameters = dict(
        shift_per_condition=-0.05,
        broadening_per_condition=0.02,
        baseline_offset=0.08,
        baseline_slope_per_condition=0.0003,
        noise_std=0.0008,
    )
    training = tuple(
        render_spectrum(x, peaks, condition=condition, seed=20 + index, **parameters)
        for index, condition in enumerate((0.5, 1.0, 1.5))
    )
    holdout = render_spectrum(
        x, peaks, condition=2.5, seed=99, **parameters
    )
    return reference, training, holdout, peaks
