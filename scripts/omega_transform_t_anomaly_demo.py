"""Ω-TRANSFORM-T anomaly demo.

This script builds a synthetic signal with a localized anomaly and uses FFWT
fertility weights as an interpretable anomaly proxy. It is not a proof of
superiority; it is a reproducible target for future OAKBench work.
"""

from __future__ import annotations

import json

import numpy as np

from omega_transform_t import ffwt_1d, fractal_fertility_report


def make_signal(n: int = 1024, seed: int = 7) -> tuple[np.ndarray, slice]:
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, n)
    x = np.sin(2 * np.pi * 9 * t) + 0.35 * np.sin(2 * np.pi * 43 * t)
    anomaly = slice(n // 3, n // 3 + 32)
    x[anomaly] += 1.5 * np.hanning(anomaly.stop - anomaly.start)
    x += 0.06 * rng.normal(size=n)
    return x, anomaly


def strongest_fertility_level_summary(x: np.ndarray) -> dict[str, object]:
    coeffs = ffwt_1d(x, levels=7)
    report = fractal_fertility_report(coeffs)
    level_scores = report["fertility_by_level"]
    strongest = max(level_scores, key=lambda item: item["max_weight"])
    return {
        "transform": "FFWT-T/Haar-fractal-heuristic",
        "strongest_level": strongest,
        "oak_warning": "Fertility is an anomaly proxy, not a certified detector.",
        "full_report": report,
    }


def main() -> None:
    x, anomaly = make_signal()
    summary = strongest_fertility_level_summary(x)
    summary["synthetic_anomaly_slice"] = [anomaly.start, anomaly.stop]
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
