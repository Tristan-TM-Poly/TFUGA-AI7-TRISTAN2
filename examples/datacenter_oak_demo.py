"""Datacenter thermal OAK demo.

This demo creates a conservative thermal surrogate report and wraps it into the
unified OAK report builder for product/discovery discussions.
"""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from omega_vtp_t import (
    ThermalZoneState,
    build_unified_oak_report,
    datacenter_thermal_oak_report,
    estimate_optimized_zone,
)


def main() -> None:
    baseline = ThermalZoneState(
        rack_temperatures_c=(31.2, 33.4, 34.8, 32.1),
        airflow_proxy=(1.0, 0.9, 0.85, 1.1),
        cooling_power_kw=250.0,
        it_power_kw=1000.0,
    )
    optimized = estimate_optimized_zone(baseline, cooling_reduction_fraction=0.18)
    thermal = datacenter_thermal_oak_report(
        baseline,
        optimized,
        electricity_cost_per_kwh=0.07,
        deployment_cost=10_000.0,
        verification_probability=0.8,
    )
    report = build_unified_oak_report(
        name="datacenter_thermal_mvp",
        model={
            "baseline_pue": thermal.baseline_pue,
            "optimized_pue": thermal.optimized_pue,
            "pue_reduction": thermal.pue_reduction,
        },
        residuals=thermal.residuals,
        invariants={"oak_status": thermal.invariant_oak_status},
        finance={"decision": thermal.finance_decision, "estimated_annual_savings": thermal.estimated_annual_savings},
    )

    print("Ω Datacenter Thermal OAK Demo")
    print(f"Baseline PUE proxy:  {thermal.baseline_pue:.4f}")
    print(f"Optimized PUE proxy: {thermal.optimized_pue:.4f}")
    print(f"PUE reduction:       {thermal.pue_reduction:.4f}")
    print(f"Annual savings EV:   ${thermal.estimated_annual_savings:,.2f}")
    print(f"Thermal OAK:         {thermal.oak_status}")
    print(f"Unified decision:    {report.decision.status}")
    print(f"Confidence:          {report.decision.confidence:.2f}")


if __name__ == "__main__":
    main()
