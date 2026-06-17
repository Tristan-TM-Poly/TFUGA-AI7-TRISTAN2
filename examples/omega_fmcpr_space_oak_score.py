"""Omega-FMCPR-Space OAK scoring seed.

Scores a spacecraft FMCPR concept by useful multifunction per kg, with OAK
penalties for thermal, energy, contamination, radiation, impact, spectroscopy,
and fluid/ECLSS risks. This is a roadmap scorer, not a flight qualification tool.

Run:
    python examples/omega_fmcpr_space_oak_score.py
"""

from __future__ import annotations

from dataclasses import dataclass


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class SpaceFMCPRPoint:
    name: str
    subsystem_mass_kg: float
    control_mass_kg: float
    heat_rejection_w: float
    control_heat_rejection_w: float
    sensor_power_saved_w: float
    te_net_power_w: float
    spectroscopy_score: float
    fluid_purification_score: float
    mechanical_score: float
    contamination_score: float
    radiation_score: float
    mmod_score: float


@dataclass(frozen=True)
class SpaceFMCPRScore:
    name: str
    heat_rejection_per_kg: float
    control_heat_rejection_per_kg: float
    thermal_gain_per_kg: float
    multifunction_score: float
    oak_status: str
    total_score: float


def score_space(point: SpaceFMCPRPoint) -> SpaceFMCPRScore:
    if point.subsystem_mass_kg <= 0 or point.control_mass_kg <= 0:
        raise ValueError("masses must be positive")

    qkg = point.heat_rejection_w / point.subsystem_mass_kg
    qkg_control = point.control_heat_rejection_w / point.control_mass_kg
    thermal_gain = qkg / max(qkg_control, 1e-9)

    # Mission-useful multifunction proxy.
    function_terms = [
        clamp01(thermal_gain / 2.0),
        clamp01(max(point.te_net_power_w, 0.0) / 1.0),
        clamp01(point.sensor_power_saved_w / 1.0),
        clamp01(point.spectroscopy_score),
        clamp01(point.fluid_purification_score),
        clamp01(point.mechanical_score),
    ]
    multifunction = sum(function_terms) / len(function_terms)

    risk_terms = [
        clamp01(point.contamination_score),
        clamp01(point.radiation_score),
        clamp01(point.mmod_score),
    ]
    risk_gate = min(risk_terms)

    if thermal_gain > 1.0 and risk_gate > 0.7 and multifunction > 0.6:
        oak = "VALIDATED_PROXY_READY_FOR_COUPON_TEST"
    elif thermal_gain > 1.0 and risk_gate > 0.5:
        oak = "MARGINAL_NEEDS_TVAC_AND_CONTROLS"
    else:
        oak = "REJECTED_OR_UNPROVEN_FOR_SPACE"

    total = 0.65 * multifunction + 0.35 * risk_gate
    return SpaceFMCPRScore(point.name, qkg, qkg_control, thermal_gain, multifunction, oak, total)


def main() -> None:
    scenarios = [
        SpaceFMCPRPoint(
            name="S0 radiative coupon",
            subsystem_mass_kg=0.25,
            control_mass_kg=0.25,
            heat_rejection_w=18.0,
            control_heat_rejection_w=12.0,
            sensor_power_saved_w=0.0,
            te_net_power_w=0.0,
            spectroscopy_score=0.0,
            fluid_purification_score=0.0,
            mechanical_score=0.6,
            contamination_score=0.8,
            radiation_score=0.6,
            mmod_score=0.6,
        ),
        SpaceFMCPRPoint(
            name="S2 Raman fluid audit branch",
            subsystem_mass_kg=0.60,
            control_mass_kg=1.10,
            heat_rejection_w=20.0,
            control_heat_rejection_w=20.0,
            sensor_power_saved_w=0.4,
            te_net_power_w=-0.05,
            spectroscopy_score=0.85,
            fluid_purification_score=0.65,
            mechanical_score=0.55,
            contamination_score=0.75,
            radiation_score=0.65,
            mmod_score=0.55,
        ),
        SpaceFMCPRPoint(
            name="Overclaimed all-in-one satellite skin",
            subsystem_mass_kg=0.20,
            control_mass_kg=4.00,
            heat_rejection_w=100.0,
            control_heat_rejection_w=80.0,
            sensor_power_saved_w=2.0,
            te_net_power_w=3.0,
            spectroscopy_score=0.9,
            fluid_purification_score=0.8,
            mechanical_score=0.9,
            contamination_score=0.25,
            radiation_score=0.20,
            mmod_score=0.30,
        ),
    ]
    for scenario in scenarios:
        print(score_space(scenario))


if __name__ == "__main__":
    main()
