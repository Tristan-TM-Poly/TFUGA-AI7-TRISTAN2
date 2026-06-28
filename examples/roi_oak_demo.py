"""Ω-ROI-OAK demo: translate technical gains into financial decision metrics."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from omega_vtp_t import (
    battery_revaluation_case,
    datacenter_pue_case,
    hft_risk_engine_case,
)


def show(label, report) -> None:
    print(f"\n{label}")
    print(f"  gross_expected_value: ${report.gross_expected_value:,.2f}")
    print(f"  verified_value:       ${report.verified_value:,.2f}")
    print(f"  total_cost:           ${report.total_cost:,.2f}")
    print(f"  expected_risk_loss:   ${report.expected_risk_loss:,.2f}")
    print(f"  risk_adjusted_value:  ${report.risk_adjusted_value:,.2f}")
    print(f"  ROI:                  {report.roi:.2f}x")
    print(f"  ROAK:                 {report.roak:.2f}x")
    print(f"  payback_years:        {report.payback_years}")
    print(f"  NPV:                  ${report.npv:,.2f}")
    print(f"  decision:             {report.decision}")
    print(f"  OAK:                  {report.oak_status}")


def main() -> None:
    dc = datacenter_pue_case(
        total_power_mw=20.0,
        current_pue=1.25,
        target_pue=1.08,
        electricity_cost_per_kwh=0.07,
        deployment_cost=250_000.0,
        verification_probability=0.8,
    ).evaluate(years=3)

    battery = battery_revaluation_case(
        acquisition_cost=1_500_000.0,
        recondition_cost=350_000.0,
        estimated_revalued_asset=4_200_000.0,
        validation_probability=0.55,
        safety_risk_loss=3_000_000.0,
    ).evaluate(years=1)

    hft = hft_risk_engine_case(
        daily_volume=50_000_000.0,
        edge_bps=2.0,
        trading_days=250,
        fill_probability=0.15,
        infrastructure_cost=1_000_000.0,
        tail_loss=5_000_000.0,
        compliance_cost=250_000.0,
    ).evaluate(years=1)

    print("Ω-ROI-OAK demo")
    show("Datacenter thermal optimization", dc)
    show("Battery/BESS revaluation", battery)
    show("HFT/regime risk engine", hft)


if __name__ == "__main__":
    main()
