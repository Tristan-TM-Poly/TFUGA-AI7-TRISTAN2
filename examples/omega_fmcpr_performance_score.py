"""Omega-FMCPR performance and OAK scoring seed.

This script scores a fractal mycelial cooling / purification / catalysis / Raman
reactor concept. It is not a CFD, electrochemistry, Raman, or thermal solver.
It separates useful performance from artifacts and energy costs.

Run:
    python examples/omega_fmcpr_performance_score.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FMCPRPoint:
    name: str
    delta_t_fractal: float
    delta_t_control: float
    seebeck_eff_v_per_k: float
    internal_resistance_ohm: float
    load_resistance_ohm: float
    pump_power_w: float
    field_power_w: float
    sensor_power_w: float
    purification_in: float
    purification_out: float
    purification_control_out: float
    raman_snr_gain: float
    byproduct_penalty: float
    fouling_penalty: float


@dataclass(frozen=True)
class FMCPRScore:
    name: str
    delta_t_gain: float
    delta_v: float
    load_current: float
    load_power: float
    net_power: float
    purification_efficiency: float
    purification_gain_vs_control: float
    raman_snr_gain: float
    safety_score: float
    robustness_score: float
    oak_status: str
    total_score: float


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score(point: FMCPRPoint) -> FMCPRScore:
    if point.internal_resistance_ohm <= 0 or point.load_resistance_ohm <= 0:
        raise ValueError("resistances must be positive")
    if point.purification_in <= 0:
        raise ValueError("purification_in must be positive")

    delta_t_gain = point.delta_t_fractal / max(point.delta_t_control, 1e-9)
    delta_v = point.seebeck_eff_v_per_k * point.delta_t_fractal
    total_r = point.internal_resistance_ohm + point.load_resistance_ohm
    current = delta_v / total_r
    load_power = current * current * point.load_resistance_ohm
    net_power = load_power - point.pump_power_w - point.field_power_w - point.sensor_power_w

    eta = (point.purification_in - point.purification_out) / point.purification_in
    eta_control = (point.purification_in - point.purification_control_out) / point.purification_in
    purification_gain = eta / max(eta_control, 1e-9)

    safety_score = clamp01(1.0 - point.byproduct_penalty)
    robustness_score = clamp01(1.0 - point.fouling_penalty)

    oak_checks = [
        delta_t_gain > 1.0,
        eta > eta_control,
        point.raman_snr_gain > 1.0,
        safety_score > 0.7,
        robustness_score > 0.5,
    ]
    if all(oak_checks) and net_power >= 0:
        oak = "VALIDATED_PROXY_NET_POSITIVE"
    elif all(oak_checks):
        oak = "VALIDATED_PROXY_FUNCTIONAL_BUT_NET_POWER_NEGATIVE"
    elif eta > eta_control and point.raman_snr_gain > 1.0:
        oak = "MARGINAL_NEEDS_CONTROLS"
    else:
        oak = "REJECTED_OR_UNPROVEN"

    total = (
        0.20 * clamp01(delta_t_gain / 3.0)
        + 0.20 * clamp01(purification_gain / 3.0)
        + 0.20 * clamp01(point.raman_snr_gain / 5.0)
        + 0.15 * safety_score
        + 0.15 * robustness_score
        + 0.10 * (1.0 if net_power >= 0 else 0.3)
    )

    return FMCPRScore(
        name=point.name,
        delta_t_gain=delta_t_gain,
        delta_v=delta_v,
        load_current=current,
        load_power=load_power,
        net_power=net_power,
        purification_efficiency=eta,
        purification_gain_vs_control=purification_gain,
        raman_snr_gain=point.raman_snr_gain,
        safety_score=safety_score,
        robustness_score=robustness_score,
        oak_status=oak,
        total_score=total,
    )


def main() -> None:
    scenarios = [
        FMCPRPoint(
            name="P0 passive Raman branch",
            delta_t_fractal=1.0,
            delta_t_control=0.8,
            seebeck_eff_v_per_k=0.0,
            internal_resistance_ohm=10.0,
            load_resistance_ohm=10.0,
            pump_power_w=0.01,
            field_power_w=0.0,
            sensor_power_w=0.02,
            purification_in=1.0,
            purification_out=0.65,
            purification_control_out=0.78,
            raman_snr_gain=1.6,
            byproduct_penalty=0.05,
            fouling_penalty=0.10,
        ),
        FMCPRPoint(
            name="P3 AC electro-catalytic branch",
            delta_t_fractal=4.0,
            delta_t_control=1.5,
            seebeck_eff_v_per_k=0.00025,
            internal_resistance_ohm=5.0,
            load_resistance_ohm=5.0,
            pump_power_w=0.02,
            field_power_w=0.05,
            sensor_power_w=0.02,
            purification_in=1.0,
            purification_out=0.25,
            purification_control_out=0.55,
            raman_snr_gain=3.2,
            byproduct_penalty=0.15,
            fouling_penalty=0.25,
        ),
        FMCPRPoint(
            name="Overdriven high-field branch",
            delta_t_fractal=8.0,
            delta_t_control=2.0,
            seebeck_eff_v_per_k=0.00025,
            internal_resistance_ohm=5.0,
            load_resistance_ohm=5.0,
            pump_power_w=0.05,
            field_power_w=0.90,
            sensor_power_w=0.05,
            purification_in=1.0,
            purification_out=0.20,
            purification_control_out=0.50,
            raman_snr_gain=2.0,
            byproduct_penalty=0.55,
            fouling_penalty=0.65,
        ),
    ]
    for scenario in scenarios:
        print(score(scenario))


if __name__ == "__main__":
    main()
