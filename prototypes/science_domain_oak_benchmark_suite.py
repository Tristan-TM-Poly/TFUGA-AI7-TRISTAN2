#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Science Domain OAK Benchmark Suite

Micro-oracle benchmark layer for the science-domain atlas.

The science_domain_omni_harvester maps many fields into tensors. This file adds
an explicit synthetic truth layer: each benchmark has a known parameter, expected
signature, or structural condition that OAK can score.

Important: these are synthetic proxy benchmarks. Passing them means the pipeline
recovers known toy structure, not that a real scientific claim is proven.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple
import argparse
import json
import math
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from jkd_fusion_strike import jkd_strike  # noqa: E402

REPORT_PATH = ROOT / "reports" / "science_oak" / "science_oak_benchmark_report.json"
N = 1024


@dataclass(frozen=True)
class ScienceBenchmark:
    name: str
    family: str
    signal: np.ndarray
    truth: Dict[str, float]
    estimator: str
    expected_max_rel_error: float


@dataclass(frozen=True)
class ScienceBenchmarkResult:
    name: str
    family: str
    estimator: str
    truth: Dict[str, float]
    extracted: Dict[str, float]
    errors: Dict[str, float]
    oak_score: float
    verdict: str
    jkd_verdict: str
    jkd_score: float
    notes: str


def stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def rng(name: str) -> np.random.Generator:
    return np.random.default_rng(abs(hash((name, "SCIENCE-OAK"))) % (2**32))


def relerr(a: float, b: float) -> float:
    return abs(float(a) - float(b)) / (abs(float(b)) + 1e-12)


def verdict(score: float) -> str:
    if score >= 80.0:
        return "CANON"
    if score >= 55.0:
        return "FERTILE"
    return "M_MINUS"


def score_from_errors(errors: Dict[str, float], complexity: float = 4.0) -> float:
    if not errors:
        return 0.0
    err = float(np.mean(list(errors.values())))
    return float(np.clip(100.0 * max(0.0, 1.0 - err) - complexity, 0.0, 100.0))


def estimate_frequency(t: np.ndarray, y: np.ndarray) -> float:
    dt = float(np.median(np.diff(t)))
    centered = y - float(np.mean(y))
    p = np.abs(np.fft.rfft(centered * np.hanning(centered.size))) ** 2
    f = np.fft.rfftfreq(centered.size, d=dt)
    if p.size <= 1:
        return 0.0
    idx = int(np.argmax(p[1:]) + 1)
    return float(2.0 * np.pi * f[idx])


def estimate_decay(t: np.ndarray, y: np.ndarray) -> float:
    envelope = np.abs(y)
    mask = envelope > max(1e-9, np.percentile(envelope, 55))
    if int(np.sum(mask)) < 8:
        mask = np.ones_like(envelope, dtype=bool)
    slope, _ = np.polyfit(t[mask], np.log(envelope[mask] + 1e-12), 1)
    return max(0.0, float(-slope))


def estimate_peak_centers(x: np.ndarray, y: np.ndarray, count: int) -> List[float]:
    yy = np.asarray(y, dtype=float)
    # simple non-maximum suppression
    candidates = np.argsort(yy)[::-1]
    selected: List[int] = []
    min_sep = max(3, yy.size // 30)
    for idx in candidates:
        if all(abs(int(idx) - chosen) >= min_sep for chosen in selected):
            selected.append(int(idx))
        if len(selected) >= count:
            break
    return sorted(float(x[i]) for i in selected)


def estimate_logistic_midpoint(t: np.ndarray, y: np.ndarray) -> float:
    target = 0.5 * (float(np.min(y)) + float(np.max(y)))
    idx = int(np.argmin(np.abs(y - target)))
    return float(t[idx])


def estimate_motif_period(y: np.ndarray, max_period: int = 32) -> int:
    arr = np.asarray(y, dtype=float)
    best_p = 1
    best_err = float("inf")
    for p in range(1, max_period + 1):
        tiled = np.resize(arr[:p], arr.size)
        err = float(np.mean(np.abs(arr - tiled)))
        if err < best_err:
            best_err = err
            best_p = p
    return best_p


def estimate_burst_count(y: np.ndarray) -> int:
    arr = np.asarray(y, dtype=float)
    threshold = float(np.mean(arr) + 3.0 * np.std(arr))
    above = arr > threshold
    count = 0
    in_burst = False
    for flag in above:
        if flag and not in_burst:
            count += 1
            in_burst = True
        elif not flag:
            in_burst = False
    return int(count)


def lyapunov_logistic(series: np.ndarray, r: float) -> float:
    x = np.asarray(series, dtype=float)
    deriv = np.abs(r * (1.0 - 2.0 * x[10:])) + 1e-12
    return float(np.mean(np.log(deriv)))


def make_benchmarks() -> List[ScienceBenchmark]:
    t = np.linspace(0.0, 12.0, N)
    x = np.linspace(0.0, 1.0, N)

    # Formal: logistic map with known positive Lyapunov tendency.
    r = 3.9
    logistic = np.empty(N)
    logistic[0] = 0.271828
    for i in range(1, N):
        logistic[i] = r * logistic[i - 1] * (1.0 - logistic[i - 1])

    # Physical: oscillator frequency.
    w = 5.0
    oscillator = np.cos(w * t) + rng("oscillator").normal(0.0, 0.02, N)

    # Chemistry/materials: three spectral peaks.
    centers = [0.22, 0.53, 0.78]
    spectrum = rng("spectrum").normal(0.0, 0.01, N)
    for c, width, amp in [(0.22, 0.012, 2.0), (0.53, 0.020, 1.6), (0.78, 0.015, 1.8)]:
        spectrum += amp * np.exp(-((x - c) ** 2) / (2.0 * width * width))

    # Earth/life: diffusion width.
    d = 0.08
    xx = np.linspace(-4.0, 4.0, N)
    diffusion = np.exp(-(xx**2) / (4.0 * d)) / math.sqrt(4.0 * math.pi * d)

    # Life: genomics motif period.
    motif = np.tile([1.0, 3.0, 2.0, 4.0, 1.0, 4.0, 3.0, 2.0], N // 8 + 1)[:N]

    # Social/cyber: burst count.
    traffic = rng("traffic").poisson(15, N).astype(float)
    for start in [180, 480, 760]:
        width = 36
        z = np.linspace(-3, 3, width)
        traffic[start:start + width] += 160.0 * np.exp(-(z**2))

    # Engineering: damped RLC-like decay and frequency.
    gamma = 0.35
    wd = 4.8
    rlc = np.exp(-gamma * t) * np.cos(wd * t) + rng("rlc").normal(0.0, 0.015, N)

    # Epidemiology: logistic midpoint.
    midpoint = 0.43
    epi = 1.0 / (1.0 + np.exp(-18.0 * (x - midpoint)))

    return [
        ScienceBenchmark("formal_logistic_lyapunov", "formal", logistic, {"lyapunov_positive": 1.0, "r": r}, "lyapunov_sign", 0.0),
        ScienceBenchmark("physics_oscillator_frequency", "physical", oscillator, {"omega": w}, "frequency", 0.06),
        ScienceBenchmark("chemistry_three_peaks", "physical", spectrum, {"peak_1": centers[0], "peak_2": centers[1], "peak_3": centers[2]}, "peak_centers", 0.08),
        ScienceBenchmark("earth_diffusion_width", "earth", diffusion, {"variance": 2.0 * d}, "variance", 0.05),
        ScienceBenchmark("life_genomic_motif_period", "life", motif, {"period": 8.0}, "motif_period", 0.0),
        ScienceBenchmark("cyber_social_burst_count", "engineering", traffic, {"burst_count": 3.0}, "burst_count", 0.20),
        ScienceBenchmark("engineering_rlc_decay_frequency", "engineering", rlc, {"gamma": gamma, "omega": wd}, "decay_frequency", 0.20),
        ScienceBenchmark("epidemiology_logistic_midpoint", "life", epi, {"midpoint": midpoint}, "logistic_midpoint", 0.03),
    ]


def run_benchmark(bench: ScienceBenchmark, permutation_checks: int) -> ScienceBenchmarkResult:
    extracted: Dict[str, float] = {}
    errors: Dict[str, float] = {}

    if bench.estimator == "lyapunov_sign":
        lyap = lyapunov_logistic(bench.signal, bench.truth["r"])
        extracted["lyapunov"] = lyap
        extracted["lyapunov_positive"] = 1.0 if lyap > 0.0 else 0.0
        errors["sign_error"] = 0.0 if lyap > 0.0 else 1.0
    elif bench.estimator == "frequency":
        t = np.linspace(0.0, 12.0, bench.signal.size)
        omega = estimate_frequency(t, bench.signal)
        extracted["omega"] = omega
        errors["omega_rel_error"] = relerr(omega, bench.truth["omega"])
    elif bench.estimator == "peak_centers":
        x = np.linspace(0.0, 1.0, bench.signal.size)
        peaks = estimate_peak_centers(x, bench.signal, 3)
        for idx, peak in enumerate(peaks, 1):
            extracted[f"peak_{idx}"] = peak
            errors[f"peak_{idx}_rel_error"] = relerr(peak, bench.truth[f"peak_{idx}"])
    elif bench.estimator == "variance":
        x = np.linspace(-4.0, 4.0, bench.signal.size)
        y = np.clip(bench.signal, 0.0, None)
        weights = y / (float(np.sum(y)) + 1e-12)
        mean = float(np.sum(weights * x))
        var = float(np.sum(weights * (x - mean) ** 2))
        extracted["variance"] = var
        errors["variance_rel_error"] = relerr(var, bench.truth["variance"])
    elif bench.estimator == "motif_period":
        period = float(estimate_motif_period(bench.signal, 16))
        extracted["period"] = period
        errors["period_rel_error"] = relerr(period, bench.truth["period"])
    elif bench.estimator == "burst_count":
        count = float(estimate_burst_count(bench.signal))
        extracted["burst_count"] = count
        errors["burst_count_rel_error"] = relerr(count, bench.truth["burst_count"])
    elif bench.estimator == "decay_frequency":
        t = np.linspace(0.0, 12.0, bench.signal.size)
        omega = estimate_frequency(t, bench.signal)
        gamma = estimate_decay(t, bench.signal)
        extracted["omega"] = omega
        extracted["gamma"] = gamma
        errors["omega_rel_error"] = relerr(omega, bench.truth["omega"])
        errors["gamma_rel_error"] = relerr(gamma, bench.truth["gamma"])
    elif bench.estimator == "logistic_midpoint":
        t = np.linspace(0.0, 1.0, bench.signal.size)
        midpoint = estimate_logistic_midpoint(t, bench.signal)
        extracted["midpoint"] = midpoint
        errors["midpoint_rel_error"] = relerr(midpoint, bench.truth["midpoint"])
    else:
        errors["unknown_estimator"] = 1.0

    jkd = jkd_strike(bench.signal, permutation_checks=permutation_checks)
    score = score_from_errors(errors, complexity=4.0)
    notes = "Synthetic proxy benchmark; success validates parameter recovery only inside this toy domain."
    return ScienceBenchmarkResult(
        name=bench.name,
        family=bench.family,
        estimator=bench.estimator,
        truth=bench.truth,
        extracted=extracted,
        errors=errors,
        oak_score=score,
        verdict=verdict(score),
        jkd_verdict=str(jkd.get("verdict")),
        jkd_score=float(jkd.get("oak_score", 0.0)),
        notes=notes,
    )


def summarize(results: List[ScienceBenchmarkResult]) -> Dict[str, Any]:
    verdicts: Dict[str, int] = {}
    families: Dict[str, int] = {}
    for item in results:
        verdicts[item.verdict] = verdicts.get(item.verdict, 0) + 1
        families[item.family] = families.get(item.family, 0) + 1
    return {
        "benchmark_count": len(results),
        "verdicts": verdicts,
        "families": families,
        "mean_oak_score": float(np.mean([r.oak_score for r in results])) if results else 0.0,
    }


def main(argv: list[str] | None = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Run synthetic science-domain OAK micro-oracle benchmarks")
    parser.add_argument("--permutation-checks", type=int, default=6)
    args = parser.parse_args(argv)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results = [run_benchmark(bench, int(args.permutation_checks)) for bench in make_benchmarks()]
    report = {
        "system": "TTM Science Domain OAK Benchmark Suite",
        "created_at": stamp(),
        "summary": summarize(results),
        "results": [asdict(result) for result in results],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
