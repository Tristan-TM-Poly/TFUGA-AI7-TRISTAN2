"""Omega-FFWT-HAC-CVCD minimal executable core.

This module is intentionally conservative. It does not claim that the current
Haar-like transform is the final FFWT. It creates a reproducible OAK-3 style
candidate pipeline:

signal -> multiscale coefficients -> reconstruction/residue -> HAC/CVCD metrics

The implementation uses only the Python standard library so it can run in small
CI environments without numerical dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import math
import random
from typing import Dict, Iterable, List, Sequence

NumberList = List[float]


@dataclass(frozen=True)
class Coefficients:
    """Multiscale coefficient packet for the MVP transform.

    ``approximation`` stores the final coarse scale. ``details`` stores one list
    per scale, from fine to coarse. This is a minimal tensor-like coefficient
    object that can later be replaced by a true FFWT tensor.
    """

    approximation: NumberList
    details: List[NumberList]
    transform: str = "haar_ffwt_candidate"

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OAKScore:
    """Small OAK score packet for MVP experiments."""

    coherence: float
    testability: float
    reproducibility: float
    gain_vs_baseline: float
    compression: float
    fertility: float
    safety: float
    utility: float

    @property
    def total(self) -> float:
        return (
            0.18 * self.coherence
            + 0.18 * self.testability
            + 0.16 * self.reproducibility
            + 0.14 * self.gain_vs_baseline
            + 0.12 * self.compression
            + 0.10 * self.fertility
            + 0.07 * self.safety
            + 0.05 * self.utility
        )

    def verdict(self) -> str:
        if self.total >= 0.78:
            return "ACCEPT_LOCAL"
        if self.total >= 0.55:
            return "TEST_MORE"
        if self.total >= 0.35:
            return "HOLD"
        return "M_MINUS_CANDIDATE"

    def to_dict(self) -> Dict[str, float | str]:
        data = asdict(self)
        data["total"] = self.total
        data["verdict"] = self.verdict()
        return data


def _require_power_of_two_length(signal: Sequence[float]) -> None:
    if not signal:
        raise ValueError("signal must not be empty")
    n = len(signal)
    if n & (n - 1):
        raise ValueError("signal length must be a power of two for this MVP transform")


def generate_signal(kind: str, length: int = 128, seed: int = 7) -> NumberList:
    """Generate deterministic synthetic signals for OAK tests.

    Supported kinds: ``sine``, ``chirp``, ``step``, ``white_noise``,
    ``pink_like_noise``, and ``fractal_like``.
    """

    if length <= 0 or length & (length - 1):
        raise ValueError("length must be a positive power of two")

    rng = random.Random(seed)
    xs = [i / length for i in range(length)]

    if kind == "sine":
        return [math.sin(2.0 * math.pi * 5.0 * x) for x in xs]

    if kind == "chirp":
        return [math.sin(2.0 * math.pi * (2.0 + 18.0 * x) * x) for x in xs]

    if kind == "step":
        return [-1.0 if i < length // 2 else 1.0 for i in range(length)]

    if kind == "white_noise":
        return [rng.uniform(-1.0, 1.0) for _ in range(length)]

    if kind == "pink_like_noise":
        white = [rng.uniform(-1.0, 1.0) for _ in range(length)]
        out: NumberList = []
        acc = 0.0
        for value in white:
            acc = 0.92 * acc + 0.08 * value
            out.append(acc)
        return _normalize(out)

    if kind == "fractal_like":
        # Deterministic multi-frequency signal with diminishing amplitudes.
        return _normalize(
            [
                sum(
                    (0.5**k) * math.sin(2.0 * math.pi * (2**k) * x)
                    for k in range(1, 6)
                )
                for x in xs
            ]
        )

    raise ValueError(f"unsupported signal kind: {kind}")


def _normalize(values: Sequence[float]) -> NumberList:
    max_abs = max(abs(v) for v in values) or 1.0
    return [float(v) / max_abs for v in values]


def haar_ffwt_candidate(signal: Sequence[float], levels: int | None = None) -> Coefficients:
    """Return a Haar-like multiscale coefficient packet.

    This is the MVP placeholder for FFWT. It is deliberately named as a
    candidate so that OAK does not over-promote it.
    """

    _require_power_of_two_length(signal)
    current = [float(v) for v in signal]
    max_levels = int(math.log2(len(current)))
    if levels is None:
        levels = max_levels
    if levels < 1 or levels > max_levels:
        raise ValueError(f"levels must be between 1 and {max_levels}")

    details: List[NumberList] = []
    inv_sqrt2 = 1.0 / math.sqrt(2.0)

    for _ in range(levels):
        approx: NumberList = []
        detail: NumberList = []
        for i in range(0, len(current), 2):
            a = current[i]
            b = current[i + 1]
            approx.append((a + b) * inv_sqrt2)
            detail.append((a - b) * inv_sqrt2)
        details.append(detail)
        current = approx

    return Coefficients(approximation=current, details=details)


def inverse_haar_ffwt_candidate(coefficients: Coefficients) -> NumberList:
    """Reconstruct a signal from ``haar_ffwt_candidate`` coefficients."""

    current = [float(v) for v in coefficients.approximation]
    inv_sqrt2 = 1.0 / math.sqrt(2.0)

    for detail in reversed(coefficients.details):
        if len(detail) != len(current):
            raise ValueError("invalid coefficient packet: detail/approximation mismatch")
        restored: NumberList = []
        for a, d in zip(current, detail):
            restored.append((a + d) * inv_sqrt2)
            restored.append((a - d) * inv_sqrt2)
        current = restored

    return current


def reconstruction_error(original: Sequence[float], reconstructed: Sequence[float]) -> float:
    """Root mean squared reconstruction error."""

    if len(original) != len(reconstructed):
        raise ValueError("signals must have the same length")
    if not original:
        raise ValueError("signals must not be empty")
    mse = sum((float(a) - float(b)) ** 2 for a, b in zip(original, reconstructed)) / len(original)
    return math.sqrt(mse)


def flatten_coefficients(coefficients: Coefficients) -> NumberList:
    """Flatten coefficient packet for metric computation."""

    flat = [float(v) for v in coefficients.approximation]
    for detail in coefficients.details:
        flat.extend(float(v) for v in detail)
    return flat


def energy_concentration(coefficients: Coefficients, keep_ratio: float = 0.10) -> float:
    """Fraction of coefficient energy contained in the largest coefficients."""

    if not 0.0 < keep_ratio <= 1.0:
        raise ValueError("keep_ratio must be in (0, 1]")
    flat = flatten_coefficients(coefficients)
    energies = sorted((v * v for v in flat), reverse=True)
    total = sum(energies)
    if total == 0.0:
        return 1.0
    k = max(1, int(math.ceil(len(energies) * keep_ratio)))
    return sum(energies[:k]) / total


def real_hac(x: Sequence[float], y: Sequence[float]) -> Dict[str, float]:
    """Real covariance/correlation/coherence metric.

    This is the robust real projection that all higher algebraic experiments must
    keep as a safety baseline.
    """

    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    if not x:
        raise ValueError("x and y must not be empty")

    xf = [float(v) for v in x]
    yf = [float(v) for v in y]
    mx = sum(xf) / len(xf)
    my = sum(yf) / len(yf)
    cov = sum((a - mx) * (b - my) for a, b in zip(xf, yf)) / len(xf)
    var_x = sum((a - mx) ** 2 for a in xf) / len(xf)
    var_y = sum((b - my) ** 2 for b in yf) / len(yf)
    denom = math.sqrt(var_x * var_y)
    corr = cov / denom if denom else 0.0
    return {
        "covariance": cov,
        "correlation": corr,
        "coherence": corr * corr,
        "variance_x": var_x,
        "variance_y": var_y,
    }


def _naive_dft_magnitudes(signal: Sequence[float]) -> NumberList:
    """Small standard-library DFT magnitude baseline for short MVP signals."""

    n = len(signal)
    out: NumberList = []
    for k in range(n):
        real = 0.0
        imag = 0.0
        for t, value in enumerate(signal):
            angle = -2.0 * math.pi * k * t / n
            real += float(value) * math.cos(angle)
            imag += float(value) * math.sin(angle)
        out.append(math.sqrt(real * real + imag * imag))
    return out


def spectral_energy_concentration(signal: Sequence[float], keep_ratio: float = 0.10) -> float:
    """Naive DFT energy concentration baseline."""

    magnitudes = _naive_dft_magnitudes(signal)
    energies = sorted((v * v for v in magnitudes), reverse=True)
    total = sum(energies)
    if total == 0.0:
        return 1.0
    k = max(1, int(math.ceil(len(energies) * keep_ratio)))
    return sum(energies[:k]) / total


def oak_score(
    *,
    reconstruction_rmse: float,
    candidate_energy: float,
    baseline_energy: float,
    reproducible: bool = True,
) -> OAKScore:
    """Compute a conservative MVP OAK score.

    The score intentionally caps promotion because this MVP uses synthetic data
    and a placeholder transform.
    """

    gain = max(0.0, min(1.0, candidate_energy - baseline_energy + 0.5))
    coherence = max(0.0, min(1.0, 1.0 - reconstruction_rmse))
    compression = max(0.0, min(1.0, candidate_energy))
    return OAKScore(
        coherence=coherence,
        testability=0.85,
        reproducibility=1.0 if reproducible else 0.0,
        gain_vs_baseline=gain,
        compression=compression,
        fertility=0.70,
        safety=0.82,
        utility=0.58,
    )


def cvcd_summary(kind: str, signal: Sequence[float], keep_ratio: float = 0.10) -> Dict[str, object]:
    """Run the MVP CVCD summary for one signal."""

    coefficients = haar_ffwt_candidate(signal)
    reconstructed = inverse_haar_ffwt_candidate(coefficients)
    rmse = reconstruction_error(signal, reconstructed)
    candidate_energy = energy_concentration(coefficients, keep_ratio=keep_ratio)
    baseline_energy = spectral_energy_concentration(signal, keep_ratio=keep_ratio)
    hac = real_hac(signal, reconstructed)
    score = oak_score(
        reconstruction_rmse=rmse,
        candidate_energy=candidate_energy,
        baseline_energy=baseline_energy,
    )

    baseline_delta = candidate_energy - baseline_energy
    if baseline_delta > 0.05:
        hypothesis = "candidate_multiscale_coefficients_are_more_concentrated_than_dft_baseline"
    elif baseline_delta < -0.05:
        hypothesis = "dft_baseline_is_more_concentrated_mminus_candidate"
    else:
        hypothesis = "candidate_and_baseline_are_close"

    return {
        "signal": kind,
        "truth_layer": "T3 simulation",
        "oak_level": "OAK-3 candidate",
        "invariants": {
            "reconstruction_rmse": rmse,
            "candidate_energy_concentration": candidate_energy,
            "dft_baseline_energy_concentration": baseline_energy,
            "baseline_delta": baseline_delta,
            "real_reconstruction_coherence": hac["coherence"],
        },
        "residues": {
            "reconstruction_rmse": rmse,
            "baseline_delta": baseline_delta,
        },
        "hypotheses": [hypothesis],
        "m_minus_candidates": [
            "baseline_loss" if baseline_delta < 0.0 else "none",
            "synthetic_only_validation",
        ],
        "oak_score": score.to_dict(),
    }


def run_minimal_benchmark(length: int = 64, seed: int = 7) -> Dict[str, object]:
    """Run the MVP benchmark suite on deterministic synthetic signals."""

    kinds = ["sine", "chirp", "step", "white_noise", "pink_like_noise", "fractal_like"]
    results = [cvcd_summary(kind, generate_signal(kind, length=length, seed=seed)) for kind in kinds]
    mean_total = sum(float(r["oak_score"]["total"]) for r in results) / len(results)
    return {
        "module": "omega_ffwt_hac_cvcd",
        "status": "MVP / OAK-3 candidate",
        "length": length,
        "seed": seed,
        "results": results,
        "aggregate": {
            "mean_oak_total": mean_total,
            "verdict": "TEST_MORE" if mean_total >= 0.55 else "HOLD",
            "claim_boundary": "synthetic signals only; no universal superiority claim",
        },
    }


def benchmark_json(length: int = 64, seed: int = 7) -> str:
    """Return benchmark output as stable JSON."""

    return json.dumps(run_minimal_benchmark(length=length, seed=seed), indent=2, sort_keys=True)


if __name__ == "__main__":
    print(benchmark_json())
