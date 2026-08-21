import unittest

from omega_capability_os_t.prospective_measurement import (
    FrozenMeasurementCriteria,
    ProspectiveExecutionReceipt,
    compare_prospective_cohorts,
)


class CapabilityOSProspectiveMeasurementR03Tests(unittest.TestCase):
    def criteria(self):
        return FrozenMeasurementCriteria("capability-os-r03", min_baseline_cases=2, min_transplant_cases=2)

    def receipt(self, execution_id, cohort, criteria, values, *, authority_widening=False):
        return ProspectiveExecutionReceipt(
            execution_id=execution_id,
            cohort=cohort,
            criteria_digest=criteria.digest(),
            measurements=dict(values),
            authority_widening=authority_widening,
            global_pass=True,
        )

    def values(self, repairs, ci, changes, regressions, tools, residuals, seconds):
        return {
            "repair_iterations": repairs,
            "ci_failures": ci,
            "persistent_changes": changes,
            "regressions": regressions,
            "tool_calls": tools,
            "residuals_remaining": residuals,
            "seconds_to_global_pass": seconds,
        }

    def test_promotes_only_when_transplant_is_noninferior_and_strictly_better(self):
        c = self.criteria()
        receipts = (
            self.receipt("b1", "baseline", c, self.values(4, 2, 7, 1, 18, 3, 600)),
            self.receipt("b2", "baseline", c, self.values(3, 2, 6, 1, 16, 2, 540)),
            self.receipt("t1", "transplant", c, self.values(2, 1, 6, 0, 13, 1, 420)),
            self.receipt("t2", "transplant", c, self.values(2, 1, 6, 0, 12, 1, 400)),
        )
        report = compare_prospective_cohorts(c, receipts)
        self.assertEqual(report.decision, "PROMOTE")
        self.assertTrue(report.improved_metrics)
        self.assertEqual(report.regressed_metrics, ())

    def test_regression_blocks_even_if_other_metrics_improve(self):
        c = self.criteria()
        receipts = (
            self.receipt("b1", "baseline", c, self.values(4, 2, 5, 0, 18, 2, 600)),
            self.receipt("b2", "baseline", c, self.values(4, 2, 5, 0, 18, 2, 600)),
            self.receipt("t1", "transplant", c, self.values(2, 1, 8, 0, 12, 1, 400)),
            self.receipt("t2", "transplant", c, self.values(2, 1, 8, 0, 12, 1, 400)),
        )
        report = compare_prospective_cohorts(c, receipts)
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("frozen_metric_regression", report.blockers)

    def test_mutating_criteria_digest_blocks_retroactive_scoring(self):
        c = self.criteria()
        altered = FrozenMeasurementCriteria("capability-os-r03", metrics=("repair_iterations",), min_baseline_cases=1, min_transplant_cases=1)
        receipts = (
            ProspectiveExecutionReceipt("b", "baseline", altered.digest(), {"repair_iterations": 2}),
            ProspectiveExecutionReceipt("t", "transplant", altered.digest(), {"repair_iterations": 1}),
        )
        report = compare_prospective_cohorts(c, receipts)
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("criteria_digest_mismatch", report.blockers)

    def test_authority_widening_blocks_promotion(self):
        c = FrozenMeasurementCriteria("auth", min_baseline_cases=1, min_transplant_cases=1)
        b = self.receipt("b", "baseline", c, self.values(2, 1, 3, 0, 8, 1, 300))
        t = self.receipt("t", "transplant", c, self.values(1, 0, 2, 0, 6, 0, 200), authority_widening=True)
        report = compare_prospective_cohorts(c, (b, t))
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("authority_widening_detected", report.blockers)


if __name__ == "__main__":
    unittest.main()
