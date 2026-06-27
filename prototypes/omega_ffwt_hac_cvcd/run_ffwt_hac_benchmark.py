#!/usr/bin/env python3
"""FFWT-HAC-CVCD benchmark v0.1.

Stdlib-only benchmark scaffold comparing FFT, DWT, FFWT-HAC, and FFWT+FFT
features on deterministic 1D signal tasks.

OAK boundary: this is exploratory evidence only. It does not claim general
superiority over FFT, DWT, scattering, or learned transforms.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

Signal = list[float]
Label = str
FeatureVector = list[float]


@dataclass(frozen=True)
class Sample:
    signal: Signal
    label: Label
    source: str


@dataclass(frozen=True)
class ClassifierResult:
    feature_set: str
    dataset: str
    noise: float
    accuracy: float
    train_size: int
    test_size: int


@dataclass(frozen=True)
class CompressionResult:
    transform: str
    dataset: str
    keep_fraction: float
    mean_relative_error: float
    mean_kept_coefficients: float


@dataclass(frozen=True)
class BenchmarkReport:
    version: str
    datasets: list[str]
    noise_sweep: list[float]
    classification_results: list[ClassifierResult]
    compression_results: list[CompressionResult]
    winners_by_dataset_noise: list[dict]
    ablation_summary: list[dict]
    oak_status: str
    oak_boundary: str
    m_minus: list[str]


def mean(xs: Iterable[float]) -> float:
    values = list(xs)
    return sum(values) / len(values) if values else 0.0


def stdev(xs: Iterable[float]) -> float:
    values = list(xs)
    mu = mean(values)
    return math.sqrt(mean((x - mu) ** 2 for x in values)) if values else 0.0


def l2_norm(xs: Signal) -> float:
    return math.sqrt(sum(x * x for x in xs))


def normalize(signal: Signal) -> Signal:
    mu = mean(signal)
    centered = [x - mu for x in signal]
    sd = stdev(centered) or 1.0
    return [x / sd for x in centered]


def deterministic_noise(n: int, level: float, seed: int) -> Signal:
    rng = random.Random(seed)
    return [level * rng.gauss(0.0, 1.0) for _ in range(n)]


def add_noise(signal: Signal, level: float, seed: int) -> Signal:
    noise = deterministic_noise(len(signal), level, seed)
    return [x + e for x, e in zip(signal, noise)]


def make_wave(length: int, freq: float, phase: float = 0.0, amp: float = 1.0) -> Signal:
    return [amp * math.sin(2.0 * math.pi * freq * i / length + phase) for i in range(length)]


def make_synthetic_dataset(n_per_class: int = 36, length: int = 64, noise: float = 0.0) -> list[Sample]:
    rows: list[Sample] = []
    for k in range(n_per_class):
        phase = 0.17 * k
        base = make_wave(length, 3.0, phase, 1.0)
        rows.append(Sample(normalize(add_noise(base, noise, 1000 + k)), "smooth_low", "synthetic"))

        mixed = [a + b for a, b in zip(make_wave(length, 7.0, phase, 0.8), make_wave(length, 13.0, 0.3 * k, 0.25))]
        rows.append(Sample(normalize(add_noise(mixed, noise, 2000 + k)), "mixed_high", "synthetic"))

        spike = make_wave(length, 4.0, phase, 0.3)
        center = (7 * k) % length
        for j in range(length):
            spike[j] += math.exp(-((j - center) ** 2) / 10.0)
        rows.append(Sample(normalize(add_noise(spike, noise, 3000 + k)), "localized_spike", "synthetic"))
    return rows


def make_fixture_adapter_dataset(n_per_class: int = 24, length: int = 64, noise: float = 0.0) -> list[Sample]:
    """Deterministic ECG/Raman-like fixture for exercising external dataset adapter logic.

    This is not claimed as a real-world benchmark. It mimics a CSV adapter target:
    smooth baseline, localized peaks, and drifting oscillatory background.
    """

    rows: list[Sample] = []
    for k in range(n_per_class):
        drift = [0.02 * i / length for i in range(length)]
        raman_a = [0.2 * math.sin(2 * math.pi * 2 * i / length) + math.exp(-((i - 18 - (k % 3)) ** 2) / 12.0) for i in range(length)]
        raman_b = [0.15 * math.sin(2 * math.pi * 5 * i / length) + 0.8 * math.exp(-((i - 43 + (k % 4)) ** 2) / 18.0) for i in range(length)]
        ecg_like = [0.05 * math.sin(2 * math.pi * i / length) for i in range(length)]
        ecg_like[(9 * k) % length] += 2.0
        rows.append(Sample(normalize(add_noise([x + d for x, d in zip(raman_a, drift)], noise, 4000 + k)), "fixture_peak_a", "csv_adapter_fixture"))
        rows.append(Sample(normalize(add_noise([x + d for x, d in zip(raman_b, drift)], noise, 5000 + k)), "fixture_peak_b", "csv_adapter_fixture"))
        rows.append(Sample(normalize(add_noise(ecg_like, noise, 6000 + k)), "fixture_spike", "csv_adapter_fixture"))
    return rows


def load_csv_dataset(path: str | Path) -> list[Sample]:
    """Load CSV rows with columns: label,x0,x1,... or label,values.

    The values-column form stores whitespace-separated floats. This adapter is
    for real external datasets supplied by the user/repo; it is not exercised by
    default CI unless a fixture path is provided.
    """

    rows: list[Sample] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            label = row.get("label") or row.get("class") or "unknown"
            if row.get("values"):
                values = [float(x) for x in row["values"].replace(",", " ").split()]
            else:
                keys = sorted(k for k in row if k.startswith("x"))
                values = [float(row[k]) for k in keys]
            rows.append(Sample(normalize(values), label, "csv"))
    return rows


def dft_magnitudes(signal: Signal, keep: int = 16) -> FeatureVector:
    n = len(signal)
    mags: FeatureVector = []
    for k in range(min(keep, n)):
        real = sum(signal[t] * math.cos(2.0 * math.pi * k * t / n) for t in range(n))
        imag = -sum(signal[t] * math.sin(2.0 * math.pi * k * t / n) for t in range(n))
        mags.append(math.sqrt(real * real + imag * imag) / n)
    return mags


def haar_coefficients(signal: Signal) -> FeatureVector:
    current = list(signal)
    coeffs: FeatureVector = []
    while len(current) >= 2:
        approx: FeatureVector = []
        detail: FeatureVector = []
        for i in range(0, len(current), 2):
            a = (current[i] + current[i + 1]) / math.sqrt(2.0)
            d = (current[i] - current[i + 1]) / math.sqrt(2.0)
            approx.append(a)
            detail.append(d)
        coeffs.extend(detail)
        current = approx
    coeffs.extend(current)
    return coeffs


def inverse_haar(coeffs: FeatureVector, length: int) -> Signal:
    levels: list[int] = []
    n = length
    while n >= 2:
        levels.append(n // 2)
        n //= 2
    pos = 0
    details: list[FeatureVector] = []
    for count in levels:
        details.append(coeffs[pos : pos + count])
        pos += count
    current = coeffs[pos : pos + 1]
    for detail in reversed(details):
        expanded: FeatureVector = []
        for a, d in zip(current, detail):
            expanded.append((a + d) / math.sqrt(2.0))
            expanded.append((a - d) / math.sqrt(2.0))
        current = expanded
    return current[:length]


def energy(xs: Signal) -> float:
    return sum(x * x for x in xs)


def dwt_features(signal: Signal) -> FeatureVector:
    coeffs = haar_coefficients(signal)
    abs_coeffs = sorted((abs(x) for x in coeffs), reverse=True)
    total = sum(abs_coeffs) or 1.0
    return [energy(coeffs), mean(abs_coeffs[:8]), mean(abs_coeffs[8:24]), sum(abs_coeffs[:8]) / total, sum(abs_coeffs[:16]) / total]


def ffwt_hac_features(signal: Signal) -> FeatureVector:
    coeffs = haar_coefficients(signal)
    abs_coeffs = [abs(x) for x in coeffs]
    total = sum(abs_coeffs) or 1.0
    sorted_abs = sorted(abs_coeffs, reverse=True)
    persistence = [sum(sorted_abs[:k]) / total for k in (4, 8, 16, 32)]
    roughness = mean(abs(signal[i] - signal[i - 1]) for i in range(1, len(signal)))
    multi_scale_balance = stdev(persistence)
    sparsity = sum(1 for x in abs_coeffs if x > 0.15 * (max(abs_coeffs) or 1.0)) / len(abs_coeffs)
    zero_crossings = sum(1 for i in range(1, len(signal)) if signal[i - 1] * signal[i] < 0) / len(signal)
    return persistence + [roughness, multi_scale_balance, sparsity, zero_crossings]


def stats_features(signal: Signal) -> FeatureVector:
    return [mean(signal), stdev(signal), max(signal), min(signal), l2_norm(signal) / math.sqrt(len(signal))]


def features(signal: Signal, name: str) -> FeatureVector:
    if name == "FFT":
        return dft_magnitudes(signal, 16) + stats_features(signal)
    if name == "DWT":
        return dwt_features(signal) + stats_features(signal)
    if name == "FFWT_HAC":
        return ffwt_hac_features(signal) + stats_features(signal)
    if name == "FFWT_PLUS_FFT":
        return ffwt_hac_features(signal) + dft_magnitudes(signal, 16) + stats_features(signal)
    raise ValueError(f"unknown feature set: {name}")


def split_holdout(samples: list[Sample], test_fraction: float = 0.30, seed: int = 7) -> tuple[list[Sample], list[Sample]]:
    by_label: dict[str, list[Sample]] = {}
    for sample in samples:
        by_label.setdefault(sample.label, []).append(sample)
    rng = random.Random(seed)
    train: list[Sample] = []
    test: list[Sample] = []
    for label, rows in sorted(by_label.items()):
        rows = list(rows)
        rng.shuffle(rows)
        n_test = max(1, int(round(len(rows) * test_fraction)))
        test.extend(rows[:n_test])
        train.extend(rows[n_test:])
    return train, test


def centroid_classifier(train: list[Sample], feature_set: str) -> dict[str, FeatureVector]:
    vectors: dict[str, list[FeatureVector]] = {}
    for sample in train:
        vectors.setdefault(sample.label, []).append(features(sample.signal, feature_set))
    centroids: dict[str, FeatureVector] = {}
    for label, feats in vectors.items():
        dim = len(feats[0])
        centroids[label] = [mean(row[j] for row in feats) for j in range(dim)]
    return centroids


def squared_distance(a: FeatureVector, b: FeatureVector) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def classify(sample: Sample, centroids: dict[str, FeatureVector], feature_set: str) -> str:
    vec = features(sample.signal, feature_set)
    return min(centroids, key=lambda label: squared_distance(vec, centroids[label]))


def evaluate_classifier(samples: list[Sample], feature_set: str, dataset: str, noise: float) -> ClassifierResult:
    train, test = split_holdout(samples)
    centroids = centroid_classifier(train, feature_set)
    correct = sum(1 for sample in test if classify(sample, centroids, feature_set) == sample.label)
    return ClassifierResult(feature_set, dataset, noise, correct / len(test), len(train), len(test))


def compress_reconstruct_haar(signal: Signal, keep_fraction: float) -> tuple[Signal, int]:
    coeffs = haar_coefficients(signal)
    keep = max(1, int(round(len(coeffs) * keep_fraction)))
    threshold = sorted((abs(x) for x in coeffs), reverse=True)[keep - 1]
    sparse = [x if abs(x) >= threshold else 0.0 for x in coeffs]
    return inverse_haar(sparse, len(signal)), keep


def compression_metrics(samples: list[Sample], dataset: str, keep_fraction: float = 0.25) -> CompressionResult:
    errors: list[float] = []
    kept: list[float] = []
    for sample in samples:
        recon, count = compress_reconstruct_haar(sample.signal, keep_fraction)
        denom = l2_norm(sample.signal) or 1.0
        errors.append(l2_norm(vec_sub(sample.signal, recon)) / denom)
        kept.append(float(count))
    return CompressionResult("HAAR_DWT_TOPK", dataset, keep_fraction, mean(errors), mean(kept))


def build_report(noise_levels: list[float], include_fixture: bool = True) -> BenchmarkReport:
    feature_sets = ["FFT", "DWT", "FFWT_HAC", "FFWT_PLUS_FFT"]
    classification_results: list[ClassifierResult] = []
    compression_results: list[CompressionResult] = []
    datasets_seen: list[str] = []

    for noise in noise_levels:
        datasets = [("synthetic", make_synthetic_dataset(noise=noise))]
        if include_fixture:
            datasets.append(("csv_adapter_fixture", make_fixture_adapter_dataset(noise=noise)))
        for dataset_name, samples in datasets:
            datasets_seen.append(dataset_name)
            for feature_set in feature_sets:
                classification_results.append(evaluate_classifier(samples, feature_set, dataset_name, noise))
            if noise == noise_levels[0]:
                compression_results.append(compression_metrics(samples, dataset_name, 0.25))

    winners: list[dict] = []
    for dataset in sorted(set(result.dataset for result in classification_results)):
        for noise in noise_levels:
            rows = [r for r in classification_results if r.dataset == dataset and abs(r.noise - noise) < 1e-12]
            best = max(rows, key=lambda row: row.accuracy)
            winners.append({"dataset": dataset, "noise": noise, "winner": best.feature_set, "accuracy": best.accuracy})

    ablation: list[dict] = []
    for dataset in sorted(set(result.dataset for result in classification_results)):
        base = [r for r in classification_results if r.dataset == dataset and r.feature_set == "FFT" and r.noise == 0.0][0]
        for feature_set in feature_sets:
            row = [r for r in classification_results if r.dataset == dataset and r.feature_set == feature_set and r.noise == 0.0][0]
            ablation.append({"dataset": dataset, "feature_set": feature_set, "accuracy": row.accuracy, "delta_vs_fft": round(row.accuracy - base.accuracy, 6)})

    m_minus = [
        "Synthetic and fixture datasets do not prove general superiority.",
        "CSV adapter support is included, but external real datasets must be supplied and cited separately.",
        "FFWT-HAC is only promoted when it wins across multiple datasets/noise levels and tasks.",
        "Classification gain can trade off against reconstruction/compression error.",
        "DWT baseline is Haar-only; scattering/learned baselines remain future work.",
    ]

    return BenchmarkReport(
        version="ffwt-hac-cvcd-benchmark-v0.1",
        datasets=sorted(set(datasets_seen)),
        noise_sweep=noise_levels,
        classification_results=classification_results,
        compression_results=compression_results,
        winners_by_dataset_noise=winners,
        ablation_summary=ablation,
        oak_status="exploratory_stronger_benchmark_scaffold",
        oak_boundary="No general superiority claim over FFT/DWT/scattering without external datasets and reproduced results.",
        m_minus=m_minus,
    )


def write_json(report: BenchmarkReport, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def markdown_report(report: BenchmarkReport) -> str:
    lines = ["# FFWT-HAC-CVCD Benchmark v0.1", "", f"OAK status: `{report.oak_status}`", "", "## Classification results", ""]
    lines.append("| dataset | noise | feature_set | accuracy |")
    lines.append("|---|---:|---|---:|")
    for row in report.classification_results:
        lines.append(f"| {row.dataset} | {row.noise:.2f} | {row.feature_set} | {row.accuracy:.3f} |")
    lines += ["", "## Winners", "", "| dataset | noise | winner | accuracy |", "|---|---:|---|---:|"]
    for row in report.winners_by_dataset_noise:
        lines.append(f"| {row['dataset']} | {row['noise']:.2f} | {row['winner']} | {row['accuracy']:.3f} |")
    lines += ["", "## Compression / reconstruction", "", "| dataset | transform | keep_fraction | mean_relative_error |", "|---|---|---:|---:|"]
    for row in report.compression_results:
        lines.append(f"| {row.dataset} | {row.transform} | {row.keep_fraction:.2f} | {row.mean_relative_error:.4f} |")
    lines += ["", "## M-minus", ""] + [f"- {item}" for item in report.m_minus]
    lines += ["", "## OAK boundary", "", report.oak_boundary, ""]
    return "\n".join(lines)


def write_markdown(report: BenchmarkReport, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown_report(report), encoding="utf-8")
    return out


def parse_noise_levels(text: str) -> list[float]:
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run FFWT-HAC-CVCD benchmark v0.1")
    parser.add_argument("--output", default="reports/omega-ffwt-hac-cvcd/benchmark.json")
    parser.add_argument("--markdown-output", default="reports/omega-ffwt-hac-cvcd/benchmark.md")
    parser.add_argument("--noise-levels", default="0.0,0.05,0.10")
    parser.add_argument("--no-fixture", action="store_true")
    args = parser.parse_args()

    report = build_report(parse_noise_levels(args.noise_levels), include_fixture=not args.no_fixture)
    write_json(report, args.output)
    write_markdown(report, args.markdown_output)
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
