import unittest

from omega_vtp_t import (
    CostComponent,
    FinancialCase,
    RiskComponent,
    ValueComponent,
    battery_revaluation_case,
    datacenter_pue_case,
    hft_risk_engine_case,
    npv,
    payback_period,
)


class ROIOAKTests(unittest.TestCase):
    def test_npv_and_payback(self):
        self.assertAlmostEqual(npv([-100.0, 60.0, 60.0], 0.0), 20.0)
        self.assertAlmostEqual(payback_period(100.0, 25.0), 4.0)
        self.assertIsNone(payback_period(100.0, 0.0))

    def test_basic_financial_case_deploy(self):
        case = FinancialCase(
            name="verified_savings",
            values=(ValueComponent("savings", 1000.0, 1.0, verified=True),),
            costs=(CostComponent("deploy", 100.0),),
            risks=(RiskComponent("risk", 0.1, 100.0),),
        )
        report = case.evaluate(roak_deploy_threshold=4.5)
        self.assertEqual(report.decision, "deploy")
        self.assertGreater(report.roak, 4.5)
        self.assertGreater(report.npv, 0.0)

    def test_datacenter_template(self):
        case = datacenter_pue_case(
            total_power_mw=20.0,
            current_pue=1.25,
            target_pue=1.08,
            electricity_cost_per_kwh=0.07,
            deployment_cost=250_000.0,
            verification_probability=1.0,
        )
        report = case.evaluate(years=1)
        self.assertGreater(report.gross_expected_value, 1_000_000.0)
        self.assertIn(report.decision, {"deploy", "pilot"})

    def test_battery_template_can_be_no_go_if_risky(self):
        case = battery_revaluation_case(
            acquisition_cost=1_500_000.0,
            recondition_cost=500_000.0,
            estimated_revalued_asset=4_200_000.0,
            validation_probability=0.25,
            safety_risk_loss=10_000_000.0,
        )
        report = case.evaluate()
        self.assertEqual(report.decision, "no_go_m_minus")

    def test_hft_template_is_risk_adjusted(self):
        case = hft_risk_engine_case(
            daily_volume=50_000_000.0,
            edge_bps=2.0,
            trading_days=250,
            fill_probability=0.2,
            infrastructure_cost=1_000_000.0,
            tail_loss=5_000_000.0,
            compliance_cost=250_000.0,
        )
        report = case.evaluate()
        self.assertGreaterEqual(report.expected_risk_loss, 0.0)
        self.assertIn(report.decision, {"deploy", "pilot", "research_only", "no_go_m_minus"})


if __name__ == "__main__":
    unittest.main()
