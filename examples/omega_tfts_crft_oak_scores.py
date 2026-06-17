"""CRFT v2 OAK scoring seed.

This script is a lightweight numerical scaffold for the Corps Radiatif Fractal de
Tristan. It does not run full-wave EM. It separates geometric fertility from
useful radiative performance with an OAK bottleneck score.

Run:
    python examples/omega_tfts_crft_oak_scores.py
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class CRFTDesignPoint:
    n: int
    epsilon_eff: float
    mu_eff: float = 1.0
    mode_gain: float = 1.0
    match_gain: float = 1.0
    outcoupling: float = 1.0
    thermal_stability: float = 1.0
    fabrication_score: float = 1.0


@dataclass(frozen=True)
class CRFTScores:
    n: int
    surface_volume_gain_menger_asymptotic: float
    dielectric_frequency_ratio: float
    impedance_proxy: float
    multiplicative_design_score: float
    oak_bottleneck_score: float
    useful_score_with_fabrication: float


def clamp01(x: float) -> float:
    """Clamp a scalar into [0, 1]."""
    return max(0.0, min(1.0, x))


def score_design(point: CRFTDesignPoint) -> CRFTScores:
    """Compute simple CRFT v2 scores.

    Geometry proxy:
        G_SV ~ 3^n for ideal Menger surface/volume asymptotics.

    Dielectric resonance proxy:
        f_material / f_vacuum = 1 / sqrt(epsilon_eff * mu_eff)

    Impedance proxy:
        Z ~ sqrt(mu_eff / epsilon_eff)

    Multiplicative score:
        G_SV * G_epsilon * G_mode * G_match * G_out * G_thermal

    OAK bottleneck score:
        G_SV * min(G_mode, G_match, G_out, G_thermal)

    Useful score:
        OAK bottleneck score times fabrication_score.
    """

    if point.n < 0:
        raise ValueError("n must be non-negative")
    if point.epsilon_eff <= 0:
        raise ValueError("epsilon_eff must be positive")
    if point.mu_eff <= 0:
        raise ValueError("mu_eff must be positive")

    g_sv = 3.0 ** point.n
    dielectric_frequency_ratio = 1.0 / sqrt(point.epsilon_eff * point.mu_eff)
    impedance_proxy = sqrt(point.mu_eff / point.epsilon_eff)

    # Frequency compression gain is represented as inverse frequency ratio.
    g_epsilon = 1.0 / dielectric_frequency_ratio

    g_mode = max(0.0, point.mode_gain)
    g_match = clamp01(point.match_gain)
    g_out = clamp01(point.outcoupling)
    g_thermal = clamp01(point.thermal_stability)
    g_fab = clamp01(point.fabrication_score)

    multiplicative = g_sv * g_epsilon * g_mode * g_match * g_out * g_thermal
    bottleneck = g_sv * min(g_mode, g_match, g_out, g_thermal)
    useful = bottleneck * g_fab

    return CRFTScores(
        n=point.n,
        surface_volume_gain_menger_asymptotic=g_sv,
        dielectric_frequency_ratio=dielectric_frequency_ratio,
        impedance_proxy=impedance_proxy,
        multiplicative_design_score=multiplicative,
        oak_bottleneck_score=bottleneck,
        useful_score_with_fabrication=useful,
    )


def main() -> None:
    scenarios = [
        CRFTDesignPoint(n=1, epsilon_eff=4.0, mode_gain=2.0, match_gain=0.8, outcoupling=0.7, thermal_stability=0.9, fabrication_score=0.9),
        CRFTDesignPoint(n=3, epsilon_eff=10.0, mode_gain=8.0, match_gain=0.4, outcoupling=0.2, thermal_stability=0.8, fabrication_score=0.5),
        CRFTDesignPoint(n=5, epsilon_eff=30.0, mode_gain=30.0, match_gain=0.15, outcoupling=0.05, thermal_stability=0.4, fabrication_score=0.2),
    ]

    for scenario in scenarios:
        print(score_design(scenario))


if __name__ == "__main__":
    main()
