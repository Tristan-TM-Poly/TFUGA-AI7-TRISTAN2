"""Synthetic datasets for Ω-TRANSFORM-T OAKBench."""

from __future__ import annotations

import numpy as np


def make_multiscale_signal(n: int = 2048, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, n)
    x = np.sin(2 * np.pi * 5 * t) + 0.4 * np.sin(2 * np.pi * 80 * t)
    x += 0.25 * np.sin(2 * np.pi * (20 + 60 * t) * t)
    x[700:760] += 2.0 * np.hanning(60)
    x += 0.05 * rng.normal(size=n)
    return x


def make_clean_noisy_signal(n: int = 2048, seed: int = 11, noise_sigma: float = 0.2) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, n)
    clean = (
        np.sin(2 * np.pi * 6 * t)
        + 0.35 * np.sin(2 * np.pi * 35 * t)
        + 0.18 * np.sin(2 * np.pi * (12 + 50 * t) * t)
    )
    noisy = clean + noise_sigma * rng.normal(size=n)
    return clean, noisy


def make_anomaly_signal(n: int = 1024, seed: int = 7) -> tuple[np.ndarray, np.ndarray, slice]:
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, n)
    x = np.sin(2 * np.pi * 9 * t) + 0.35 * np.sin(2 * np.pi * 43 * t)
    anomaly = slice(n // 3, n // 3 + 32)
    mask = np.zeros(n, dtype=bool)
    mask[anomaly] = True
    x[anomaly] += 1.5 * np.hanning(anomaly.stop - anomaly.start)
    x += 0.06 * rng.normal(size=n)
    return x, mask, anomaly


def make_coupled_channels(n: int = 1024, seed: int = 123) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, n)
    base = np.sin(2 * np.pi * 13 * t) + 0.25 * np.sin(2 * np.pi * 55 * t)
    x0 = base + 0.02 * rng.normal(size=t.size)
    x1 = 0.9 * base + 0.02 * rng.normal(size=t.size)
    x2 = rng.normal(size=t.size)
    return np.vstack([x0, x1, x2])
