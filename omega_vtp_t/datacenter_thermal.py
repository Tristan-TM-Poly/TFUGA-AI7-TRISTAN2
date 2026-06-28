"""Datacenter thermal MVP for Ω-DE-TensorProd∞ + Ω-ROI-OAK.

This is a lightweight, auditable surrogate model for product discovery. It does
not replace CFD. It estimates thermal/cooling savings and produces OAK-ready
metrics for pilots and A/B tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .invariant_guards import InvariantCheck, invariant_report
from .residual_decomposition import ResidualComponent, decompose_residuals, residual_dict
from .roi_oak import datacenter_pue_case


@dataclass(frozen=True)
class ThermalZoneState:
    rack_temperatures_c: tuple[float, ...]
    airflow_proxy: tuple[float, ...]
    cooling_power_kw: float
    it_power_kw: float

    @property
    def average_temperature_c(self) -> float:
        return float(np.mean(self.rack_temperatures_c))

    @property
    def max_temperature_c(self) -> float:
        return float(np.max(self.rack_temperatures_c))

    @property
    def pue_proxy(self) -> float:
        return float((self.it_power_kw + self.cooling_power_kw) / max(self.it_power_kw, 1e-12))


@dataclass(frozen=True)
class ThermalOptimizationReport:
    baseline_pue: float
    optimized_pue: float
    pue_reduction: float
    hotspot_reduction_c: float
    estimated_annual_savings: float
    residuals: dict[str, float | str | bool]
    invariant_oak_status: str
    finance_decision: str
    oak_status: str


def hotspot_risk_score(temperatures_c: Sequence[float], *, threshold_c: float = 35.0) -> float:
    temps = np.asarray(temperatures_c, dtype=float)
    if temps.size == 0:
        return 0.0
    excess = np.maximum(0.0, temps - threshold_c)
    return float(np.mean(excess * excess))


def estimate_optimized_zone(
    baseline: ThermalZoneState,
    *,
    cooling_reduction_fraction: float,
    temperature_penalty_c: float = 0.2,
) -> ThermalZoneState:
    """Estimate a conservative post-control thermal state."""

    if not 0.0 <= cooling_reduction_fraction < 1.0:
        raise ValueError("cooling_reduction_fraction must be in [0, 1)")
    new_cooling = baseline.cooling_power_kw * (1.0 - cooling_reduction_fraction)
    temps = tuple(float(t + temperature_penalty_c * cooling_reduction_fraction * 10.0) for t in baseline.rack_temperatures_c)
    return ThermalZoneState(
        rack_temperatures_c=temps,
        airflow_proxy=baseline.airflow_proxy,
        cooling_power_kw=float(new_cooling),
        it_power_kw=baseline.it_power_kw,
    )


def datacenter_thermal_oak_report(
    baseline: ThermalZoneState,
    optimized: ThermalZoneState,
    *,
    electricity_cost_per_kwh: float,
    deployment_cost: float,
    verification_probability: float = 0.7,
    max_temperature_limit_c: float = 40.0,
) -> ThermalOptimizationReport:
    """Create an OAK/ROI report for a datacenter thermal pilot."""

    if electricity_cost_per_kwh < 0:
        raise ValueError("electricity_cost_per_kwh must be nonnegative")
    baseline_pue = baseline.pue_proxy
    optimized_pue = optimized.pue_proxy
    pue_reduction = baseline_pue - optimized_pue
    total_power_mw = (baseline.it_power_kw + baseline.cooling_power_kw) / 1000.0
    finance_case = datacenter_pue_case(
        total_power_mw=total_power_mw,
        current_pue=baseline_pue,
        target_pue=optimized_pue,
        electricity_cost_per_kwh=electricity_cost_per_kwh,
        deployment_cost=deployment_cost,
        verification_probability=verification_probability,
    )
    finance = finance_case.evaluate(years=1)

    baseline_hotspot = hotspot_risk_score(baseline.rack_temperatures_c)
    optimized_hotspot = hotspot_risk_score(optimized.rack_temperatures_c)
    hotspot_reduction = baseline_hotspot - optimized_hotspot

    residual_report = decompose_residuals(
        [
            ResidualComponent("pue_not_improved", max(0.0, -pue_reduction), 1e-9),
            ResidualComponent("hotspot_risk_increase", max(0.0, -hotspot_reduction), 1e-6),
            ResidualComponent("max_temperature_excess", max(0.0, optimized.max_temperature_c - max_temperature_limit_c), 0.1),
        ]
    )

    invariants = invariant_report(
        [
            InvariantCheck(
                name="temperature_limit",
                expected=f"max_temperature <= {max_temperature_limit_c}",
                measured_error=max(0.0, optimized.max_temperature_c - max_temperature_limit_c),
                tolerance=0.1,
                passed=optimized.max_temperature_c <= max_temperature_limit_c + 0.1,
            ),
            InvariantCheck(
                name="it_power_preserved",
                expected="it_power unchanged in surrogate",
                measured_error=abs(optimized.it_power_kw - baseline.it_power_kw),
                tolerance=1e-9,
                passed=abs(optimized.it_power_kw - baseline.it_power_kw) <= 1e-9,
            ),
        ]
    )

    if finance.decision in {"deploy", "pilot"} and residual_report.oak_status == "certified" and invariants.oak_status == "certified":
        oak_status = "pilot_candidate"
    elif residual_report.oak_status.startswith("residual_high") or invariants.oak_status.startswith("invariant_violation"):
        oak_status = "no_go_m_minus"
    else:
        oak_status = "research_only"

    return ThermalOptimizationReport(
        baseline_pue=baseline_pue,
        optimized_pue=optimized_pue,
        pue_reduction=float(pue_reduction),
        hotspot_reduction_c=float(hotspot_reduction),
        estimated_annual_savings=finance.gross_expected_value,
        residuals=residual_dict(residual_report),
        invariant_oak_status=invariants.oak_status,
        finance_decision=finance.decision,
        oak_status=oak_status,
    )
