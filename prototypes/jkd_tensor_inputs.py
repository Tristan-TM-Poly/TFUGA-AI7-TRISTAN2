#!/usr/bin/env python3
"""Synthetic tensor inputs for JKD Fusion Strike.

Generates two materially different realities that are evaluated by the same
jkd_strike function:

- Raman-like spectrum with baseline, Lorentzian peaks, and noise.
- Chess-like 8x8 matrices: initial structured board and chaotic random board.

Outputs reports/jkd/jkd_tensor_inputs_report.json.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from jkd_fusion_strike import jkd_strike  # noqa: E402

REPORT_DIR = ROOT / "reports" / "jkd"
REPORT_PATH = REPORT_DIR / "jkd_tensor_inputs_report.json"


def lorentzian(x: np.ndarray, x0: float, gamma: float, amplitude: float) -> np.ndarray:
    return amplitude * (gamma * gamma / ((x - x0) ** 2 + gamma * gamma))


def simulate_raman_tensor(points: int = 1024, noise_level: float = 0.05, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = np.linspace(0.0, 1000.0, points)
    baseline = 0.002 * x + 0.5 * np.sin(x / 200.0)
    peak_1 = lorentzian(x, x0=300.0, gamma=15.0, amplitude=5.0)
    peak_2 = lorentzian(x, x0=750.0, gamma=8.0, amplitude=8.0)
    noise = rng.normal(0.0, noise_level, points)
    return baseline + peak_1 + peak_2 + noise


def simulate_chess_tensor(state: str = "initial", seed: int = 17) -> np.ndarray:
    board = np.zeros((8, 8), dtype=float)
    if state == "initial":
        board[1, :] = 1.0
        board[6, :] = -1.0
        board[0, :] = [5.0, 3.0, 3.5, 9.0, 100.0, 3.5, 3.0, 5.0]
        board[7, :] = [-5.0, -3.0, -3.5, -9.0, -100.0, -3.5, -3.0, -5.0]
        return board
    if state == "chaotic":
        rng = np.random.default_rng(seed)
        pieces = np.array([0, 0, 0, 0, 1, -1, 3, -3, 5, -5, 9, -9], dtype=float)
        board = rng.choice(pieces, size=(8, 8))
        board[rng.integers(0, 8), rng.integers(0, 8)] = 100.0
        board[rng.integers(0, 8), rng.integers(0, 8)] = -100.0
        return board
    raise ValueError(f"unknown chess state: {state}")


def compact(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "verdict": result["verdict"],
        "oak_score": result["oak_score"],
        "shape": result["shape"],
        "flattened_size": result["flattened_size"],
        "permutation_control": result["permutation_control"],
        "selected_signatures": {
            "fractal_ratio": result["signatures_cvcd"].get("fractal_ratio"),
            "ffwt_energy_entropy": result["signatures_cvcd"].get("ffwt_energy_entropy"),
            "ffwt_mean_adjacent_coherence": result["signatures_cvcd"].get("ffwt_mean_adjacent_coherence"),
            "ffwt_dominant_level": result["signatures_cvcd"].get("ffwt_dominant_level"),
        },
    }


def main() -> Dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    tensors = {
        "raman_synthetic": simulate_raman_tensor(noise_level=0.08),
        "chess_initial": simulate_chess_tensor("initial"),
        "chess_chaotic": simulate_chess_tensor("chaotic"),
    }
    results = {name: compact(jkd_strike(tensor)) for name, tensor in tensors.items()}
    report = {
        "system": "TTM JKD Fusion Tensor Inputs",
        "method": "same jkd_strike function applied to Raman-like spectrum and chess-like matrices",
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
