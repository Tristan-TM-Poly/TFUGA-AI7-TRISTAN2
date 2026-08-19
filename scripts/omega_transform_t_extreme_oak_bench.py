"""Extreme Ω-TRANSFORM-T OAKBench.

This benchmark adds:
- reconstruction sparse comparison;
- denoising comparison;
- anomaly-score evaluation;
- multichannel coherence sanity check.

It remains OAK-safe: numbers are evidence for this synthetic suite only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from omega_transform_t import (  # noqa: E402
    anomaly_score_bench,
    compare_amplitude_vs_fertility_selection,
    denoise_selection_bench,
    ffwtn,
    make_anomaly_signal,
    make_clean_noisy_signal,
    make_coupled_channels,
    make_multiscale_signal,
)


def main() -> None:
    signal = make_multiscale_signal()
    clean, noisy = make_clean_noisy_signal()
    anomaly_signal, anomaly_mask, anomaly_slice = make_anomaly_signal()
    channels = make_coupled_channels()

    reconstruction = [
        compare_amplitude_vs_fertility_selection(signal, levels=8, keep_fraction=keep)
        for keep in [0.05, 0.10, 0.20, 0.40]
    ]
    denoise = [
        denoise_selection_bench(clean, noisy, levels=8, keep_fraction=keep)
        for keep in [0.05, 0.10, 0.20, 0.40]
    ]
    anomaly = anomaly_score_bench(anomaly_signal, anomaly_mask, levels=7, top_fraction=0.05)
    coherence = ffwtn(channels, levels=7)

    output = {
        "reconstruction": reconstruction,
        "denoise": denoise,
        "anomaly": {
            **anomaly,
            "synthetic_anomaly_slice": [anomaly_slice.start, anomaly_slice.stop],
        },
        "multichannel_mean_abs_offdiag_coherence": coherence["mean_abs_offdiag_coherence"],
        "coherence_matrix": np.asarray(coherence["coherence_matrix"]).tolist(),
        "oak_warning": "Synthetic OAKBench is a gate, not a general proof.",
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
