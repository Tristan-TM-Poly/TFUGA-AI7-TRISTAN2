"""Run a minimal Ω-TRANSFORM-T OAKBench.

Usage:
    python scripts/omega_transform_t_oak_bench.py
"""

from __future__ import annotations

import json

import numpy as np

from omega_transform_t import compare_fwt_ffwt_thresholding, haar_fwt_1d, haar_ifwt_1d


def make_signal(n: int = 2048, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, n)
    x = np.sin(2 * np.pi * 5 * t) + 0.4 * np.sin(2 * np.pi * 80 * t)
    x += 0.25 * np.sin(2 * np.pi * (20 + 60 * t) * t)
    x[700:760] += 2.0 * np.hanning(60)
    x += 0.05 * rng.normal(size=n)
    return x


def main() -> None:
    x = make_signal()

    coeffs = haar_fwt_1d(x)
    xr = haar_ifwt_1d(coeffs)
    exact_error = float(np.linalg.norm(x - xr) / (np.linalg.norm(x) + 1e-12))
    print("Exact FWT reconstruction relative error:", exact_error)
    if exact_error >= 1e-10:
        raise SystemExit("FWT exact reconstruction check failed")

    reports = []
    for keep in [0.05, 0.10, 0.20, 0.40]:
        reports.append(compare_fwt_ffwt_thresholding(x, levels=8, keep_fraction=keep))

    print(json.dumps({"exact_fwt_error": exact_error, "reports": reports}, indent=2))


if __name__ == "__main__":
    main()
