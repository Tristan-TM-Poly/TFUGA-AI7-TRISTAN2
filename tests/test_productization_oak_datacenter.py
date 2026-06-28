import unittest

from omega_vtp_t.datacenter_thermal import (
    ThermalZoneState,
    datacenter_thermal_oak_report,
    estimate_optimized_zone,
    hotspot_risk_score,
)
from omega_vtp_t.oak_report_builder import build_unified_oak_report


class ProductizationOAKDatacenterTests(unittest.TestCase):
    def test_hotspot_risk_score(self):
        self.assertEqual(hotspot_risk_score([30.0, 31.0], threshold_c=35.0), 0.0)
        self.assertGreater(hotspot_risk_score([30.0, 40.0], threshold_c=35.0), 0.0)

    def test_datacenter_thermal_oak_report(self):
        baseline = ThermalZoneState(
            rack_temperatures_c=(31.0, 32.0, 33.0),
            airflow_proxy=(1.0, 1.0, 1.0),
            cooling_power_kw=250.0,
            it_power_kw=1000.0,
        )
        optimized = estimate_optimized_zone(baseline, cooling_reduction_fraction=0.2)
        report = datacenter_thermal_oak_report(
            baseline,
            optimized,
            electricity_cost_per_kwh=0.07,
            deployment_cost=10_000.0,
            verification_probability=1.0,
        )
        self.assertGreater(report.pue_reduction, 0.0)
        self.assertGreater(report.estimated_annual_savings, 0.0)
        self.assertIn(report.oak_status, {"pilot_candidate", "research_only", "no_go_m_minus"})

    def test_unified_oak_report(self):
        report = build_unified_oak_report(
            name="test_case",
            model={"degree": 3},
            residuals={"oak_status": "certified"},
            invariants={"oak_status": "certified"},
            finance={"decision": "pilot"},
            mminus=(),
        )
        self.assertEqual(report.decision.status, "pilot_candidate")
        self.assertGreaterEqual(report.decision.confidence, 0.5)
        self.assertEqual(report.to_dict()["name"], "test_case")


if __name__ == "__main__":
    unittest.main()
