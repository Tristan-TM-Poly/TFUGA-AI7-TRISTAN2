"""Synthetic Raman / CVCD / OAK experiment seed.

This is not a validated Raman method yet. It is an executable friction test:
- generate a known synthetic Raman signal;
- add fluorescence-like baseline and noise;
- compare a classical smooth-baseline correction against a simple CVCD-like
  multi-scale residual extraction;
- emit OAK-style metrics.

The script uses only Python's standard library so it can run in minimal CI.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import math
import random
from typing import Dict, List, Tuple


@dataclass
class RamanMetrics:
    method: str
    rmse: float
    snr_gain: float
    peak_position_error: float
    distortion_score: float


@dataclass
class OakRamanReport:
    status: str
    verdict: str
    baseline: RamanMetrics
    hgfm_cvcd: RamanMetrics
    residue: List[str]


def gaussian(x: float, mu: float, sigma: float, amplitude: float) -> float:
    return amplitude * math.exp(-((x - mu) ** 2) / (2.0 * sigma * sigma))


def generate_synthetic_spectrum(seed: int = 42, n: int = 600) -> Tuple[List[float], List[float], List[float]]:
    rng = random.Random(seed)
    xs = [100.0 + i * (1800.0 / (n - 1)) for i in range(n)]
    peaks = [
        (350.0, 18.0, 1.2),
        (725.0, 25.0, 0.9),
        (1080.0, 16.0, 1.5),
        (1450.0, 30.0, 0.7),
    ]
    true_signal = [sum(gaussian(x, mu, sigma, amp) for mu, sigma, amp in peaks) for x in xs]
    baseline = [0.25 + 0.00045 * (x - 100.0) + 0.35 * math.exp(-(x - 100.0) / 900.0) for x in xs]
    noise = [rng.gauss(0.0, 0.045) for _ in xs]
    raw = [s + b + e for s, b, e in zip(true_signal, baseline, noise)]
    return xs, true_signal, raw


def moving_average(values: List[float], radius: int) -> List[float]:
    out: List[float] = []
    n = len(values)
    for idx in range(n):
        lo = max(0, idx - radius)
        hi = min(n, idx + radius + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


def smooth_baseline_correction(raw: List[float]) -> List[float]:
    """Simple classical baseline proxy.

    This is not full ALS. It is a deterministic low-frequency smoother used as
    a dependency-free baseline until the real ALS implementation is added.
    """

    slow = moving_average(raw, radius=40)
    very_slow = moving_average(slow, radius=40)
    return [max(0.0, y - b) for y, b in zip(raw, very_slow)]


def cvcd_like_multiscale_extraction(raw: List[float]) -> List[float]:
    """Very small CVCD-like spectral seed.

    Principle:
    - remove a slow trend;
    - keep positive localized residuals;
    - smooth lightly to preserve peaks while reducing noise.
    """

    slow = moving_average(raw, radius=65)
    residual = [max(0.0, y - b) for y, b in zip(raw, slow)]
    local = moving_average(residual, radius=3)
    return local


def rmse(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def snr_gain(true_signal: List[float], raw: List[float], corrected: List[float]) -> float:
    raw_noise = rmse(true_signal, raw)
    corrected_noise = rmse(true_signal, corrected)
    if corrected_noise == 0:
        return float("inf")
    return raw_noise / corrected_noise


def find_peak_positions(xs: List[float], ys: List[float], top_k: int = 4, min_spacing: int = 25) -> List[float]:
    candidates = sorted(range(1, len(ys) - 1), key=lambda i: ys[i], reverse=True)
    selected: List[int] = []
    for idx in candidates:
        if ys[idx] >= ys[idx - 1] and ys[idx] >= ys[idx + 1]:
            if all(abs(idx - chosen) >= min_spacing for chosen in selected):
                selected.append(idx)
                if len(selected) == top_k:
                    break
    return sorted(xs[idx] for idx in selected)


def peak_position_error(xs: List[float], true_signal: List[float], corrected: List[float]) -> float:
    true_peaks = find_peak_positions(xs, true_signal)
    corrected_peaks = find_peak_positions(xs, corrected)
    if not true_peaks or not corrected_peaks:
        return float("inf")
    pairs = zip(true_peaks, corrected_peaks)
    return sum(abs(a - b) for a, b in pairs) / min(len(true_peaks), len(corrected_peaks))


def distortion_score(true_signal: List[float], corrected: List[float]) -> float:
    true_max = max(true_signal) or 1.0
    corr_max = max(corrected) or 1.0
    normalized_true = [v / true_max for v in true_signal]
    normalized_corr = [v / corr_max for v in corrected]
    return rmse(normalized_true, normalized_corr)


def metrics_for(method: str, xs: List[float], true_signal: List[float], raw: List[float], corrected: List[float]) -> RamanMetrics:
    return RamanMetrics(
        method=method,
        rmse=rmse(true_signal, corrected),
        snr_gain=snr_gain(true_signal, raw, corrected),
        peak_position_error=peak_position_error(xs, true_signal, corrected),
        distortion_score=distortion_score(true_signal, corrected),
    )


def oak_decide(baseline: RamanMetrics, hgfm: RamanMetrics) -> OakRamanReport:
    residue: List[str] = [
        "synthetic spectrum only",
        "baseline is smooth proxy, not full ALS",
        "CVCD is heuristic v0, not the final FFWT-HAC-CVCD operator",
    ]

    passes = (
        hgfm.snr_gain > baseline.snr_gain
        and hgfm.peak_position_error <= baseline.peak_position_error + 1e-9
        and hgfm.distortion_score <= baseline.distortion_score + 0.05
    )

    if passes:
        status = "OAK-4-PARTIAL"
        verdict = "HGFM-CVCD synthetic seed beats the smooth baseline under the configured metrics."
    else:
        status = "OAK-3/UNKNOWN"
        verdict = "Synthetic seed is executable but not yet superior; keep residue and improve operator."

    return OakRamanReport(status=status, verdict=verdict, baseline=baseline, hgfm_cvcd=hgfm, residue=residue)


def run(seed: int = 42) -> OakRamanReport:
    xs, true_signal, raw = generate_synthetic_spectrum(seed=seed)
    baseline_corrected = smooth_baseline_correction(raw)
    hgfm_corrected = cvcd_like_multiscale_extraction(raw)
    baseline_metrics = metrics_for("smooth_baseline_proxy", xs, true_signal, raw, baseline_corrected)
    hgfm_metrics = metrics_for("hgfm_cvcd_like_v0", xs, true_signal, raw, hgfm_corrected)
    return oak_decide(baseline_metrics, hgfm_metrics)


if __name__ == "__main__":
    report = run()
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
