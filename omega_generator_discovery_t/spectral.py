"""Minimal physical-shape spectral morph analysis."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import pi
from typing import Iterable, Sequence

_EPS = 1.0e-12


def lorentzian(axis: Sequence[float], *, area: float, center: float, hwhm: float) -> tuple[float, ...]:
    if hwhm <= 0:
        raise ValueError("hwhm must be positive")
    gamma = float(hwhm)
    return tuple((area/pi) * gamma / ((float(x)-center)**2 + gamma**2) for x in axis)


def mixture(axis: Sequence[float], peaks: Iterable[tuple[float, float, float]]) -> tuple[float, ...]:
    x = tuple(float(value) for value in axis)
    total = [0.0 for _ in x]
    for area, center, hwhm in peaks:
        component = lorentzian(x, area=area, center=center, hwhm=hwhm)
        total = [a+b for a, b in zip(total, component)]
    return tuple(total)


def _moments(axis: Sequence[float], intensity: Sequence[float]) -> tuple[float, float, float]:
    if len(axis) != len(intensity) or len(axis) < 3:
        raise ValueError("Axis and intensity must share length >= 3")
    weights = tuple(max(0.0, float(value)) for value in intensity)
    total = sum(weights)
    if total <= _EPS:
        raise ValueError("Spectrum must have positive intensity")
    centroid = sum(float(x)*w for x, w in zip(axis, weights))/total
    variance = sum(((float(x)-centroid)**2)*w for x, w in zip(axis, weights))/total
    return total, centroid, variance**0.5


@dataclass(frozen=True, slots=True)
class SpectralMorph:
    amplitude_ratio: float
    centroid_shift: float
    width_ratio: float
    log_amplitude: float | None
    log_width: float | None
    normalized_residual: float
    discrete_event_score: float
    status: str = "moment_based_candidate_not_peak_certification"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def compare_spectra(
    axis: Sequence[float],
    before: Sequence[float],
    after: Sequence[float],
    *,
    event_threshold_fraction: float = 0.15,
) -> SpectralMorph:
    if len(before) != len(after):
        raise ValueError("Spectra must share a length")
    area0, center0, width0 = _moments(axis, before)
    area1, center1, width1 = _moments(axis, after)
    amplitude_ratio = area1/area0
    width_ratio = width1/max(width0, _EPS)
    predicted = []
    for x in axis:
        source_x = center0 + (float(x)-center1)/max(width_ratio, _EPS)
        nearest = min(range(len(axis)), key=lambda i: abs(float(axis[i])-source_x))
        predicted.append(amplitude_ratio*float(before[nearest]))
    denom = max(sum(float(v)**2 for v in after)**0.5, _EPS)
    residual = sum((float(a)-float(b))**2 for a, b in zip(after, predicted))**0.5/denom
    positive_after = [max(0.0, float(a)-float(b)) for a, b in zip(after, predicted)]
    event_score = sum(positive_after)/max(sum(max(0.0, float(v)) for v in after), _EPS)
    if event_score < event_threshold_fraction:
        event_score = 0.0
    from math import log
    return SpectralMorph(
        amplitude_ratio=amplitude_ratio,
        centroid_shift=center1-center0,
        width_ratio=width_ratio,
        log_amplitude=log(amplitude_ratio) if amplitude_ratio > _EPS else None,
        log_width=log(width_ratio) if width_ratio > _EPS else None,
        normalized_residual=residual,
        discrete_event_score=event_score,
    )
