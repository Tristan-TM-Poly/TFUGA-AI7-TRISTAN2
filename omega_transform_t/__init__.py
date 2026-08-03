"""Ω-TRANSFORM-T public prototype API."""

from .anomaly import fertility_anomaly_scores
from .ffwt import ffwt_1d, fractal_fertility_report, iffw_transform_1d
from .ffwtn import ffwtn, multichannel_ffwt_coherence, recursive_ffwt_1d
from .fwt import coeff_energy, flatten_coeffs, haar_fwt_1d, haar_ifwt_1d, threshold_coeffs
from .metrics import energy_ratio, relative_l2_error, robust_zscore, snr_db, topk_overlap
from .oak_bench import compare_fwt_ffwt_thresholding, oak_report
from .oak_extreme import anomaly_score_bench, compare_amplitude_vs_fertility_selection, denoise_selection_bench
from .selection import amplitude_select_coeffs, fertility_select_coeffs
from .synthetic import make_anomaly_signal, make_clean_noisy_signal, make_coupled_channels, make_multiscale_signal

__all__ = [
    "haar_fwt_1d",
    "haar_ifwt_1d",
    "threshold_coeffs",
    "flatten_coeffs",
    "coeff_energy",
    "ffwt_1d",
    "iffw_transform_1d",
    "fractal_fertility_report",
    "ffwtn",
    "recursive_ffwt_1d",
    "multichannel_ffwt_coherence",
    "oak_report",
    "compare_fwt_ffwt_thresholding",
    "compare_amplitude_vs_fertility_selection",
    "denoise_selection_bench",
    "anomaly_score_bench",
    "fertility_select_coeffs",
    "amplitude_select_coeffs",
    "fertility_anomaly_scores",
    "relative_l2_error",
    "snr_db",
    "energy_ratio",
    "robust_zscore",
    "topk_overlap",
    "make_multiscale_signal",
    "make_clean_noisy_signal",
    "make_anomaly_signal",
    "make_coupled_channels",
]
