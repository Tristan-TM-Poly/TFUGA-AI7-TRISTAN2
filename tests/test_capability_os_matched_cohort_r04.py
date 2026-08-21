import unittest

from omega_capability_os_t.matched_cohort import (
    MatchedExecution,
    SequentialCriteria,
    compare_matched_cohorts,
)
from omega_capability_os_t.prospective_measurement import (
    FrozenMeasurementCriteria,
    ProspectiveExecutionReceipt,
)


class CapabilityOSMatchedCohortR04Tests(unittest.TestCase):
    def criteria(self):
        return FrozenMeasurementCriteria(
            experiment_id="prospective-r04",
            metrics=("repair_iterations", "ci_failures"),
        )

    def receipt(self, execution_id, cohort, criteria, repair, ci, authority=False):
        return ProspectiveExecutionReceipt(
            execution_id=execution_id,
            cohort=cohort,
            criteria_digest=criteria.digest(),
            measurements={"repair_iterations": repair, "ci_failures": ci},
            authority_widening=authority,
            global_pass=True,
        )

    def matched(self, receipt, family="repo", difficulty="m", risk="low"):
        return MatchedExecution(
            receipt,
            {"task_family": family, "difficulty_band": difficulty, "risk_band": risk},
        )

    def test_promotes_when_matched_pairs_show_uncertainty_bounded_improvement(self):
        c = self.criteria()
        rows = []
        for i, (b, t) in enumerate(((5, 2), (6, 3), (7, 4))):
            strata = {"task_family": "repo", "difficulty_band": str(i), "risk_band": "low"}
            rows.append(MatchedExecution(self.receipt(f"b{i}", "baseline", c, b, 2, False), strata))
            rows.append(MatchedExecution(self.receipt(f"t{i}", "transplant", c, t, 1, False), strata))
        report = compare_matched_cohorts(c, SequentialCriteria(min_pairs=3, max_pairs=5), rows)
        self.assertEqual(report.decision, "PROMOTE")
        self.assertEqual(report.pair_count, 3)
        self.assertEqual(report.blockers, ())

    def test_holds_when_pairs_are_insufficient(self):
        c = self.criteria()
        rows = (
            self.matched(self.receipt("b", "baseline", c, 5, 2)),
            self.matched(self.receipt("t", "transplant", c, 4, 1)),
        )
        report = compare_matched_cohorts(c, SequentialCriteria(min_pairs=2, max_pairs=4), rows)
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("insufficient_matched_pairs", report.blockers)

    def test_missing_stratum_blocks_matching(self):
        c = self.criteria()
        b = MatchedExecution(self.receipt("b", "baseline", c, 4, 1), {"task_family": "repo"})
        t = MatchedExecution(self.receipt("t", "transplant", c, 3, 1), {"task_family": "repo"})
        report = compare_matched_cohorts(c, SequentialCriteria(min_pairs=1), (b, t))
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("missing_match_stratum", report.blockers)

    def test_criteria_mutation_blocks_court(self):
        c = self.criteria()
        bad = ProspectiveExecutionReceipt(
            "t", "transplant", "mutated", {"repair_iterations": 1, "ci_failures": 0}
        )
        report = compare_matched_cohorts(
            c,
            SequentialCriteria(min_pairs=1),
            (self.matched(self.receipt("b", "baseline", c, 3, 1)), self.matched(bad)),
        )
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("criteria_digest_mismatch", report.blockers)

    def test_authority_widening_is_noncompensatory(self):
        c = self.criteria()
        rows = (
            self.matched(self.receipt("b", "baseline", c, 10, 5)),
            self.matched(self.receipt("t", "transplant", c, 0, 0, True)),
        )
        report = compare_matched_cohorts(c, SequentialCriteria(min_pairs=1), rows)
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("authority_widening_detected", report.blockers)

    def test_stops_at_max_pairs_when_uncertainty_does_not_clear(self):
        c = self.criteria()
        rows = []
        for i, (b, t) in enumerate(((3, 4), (4, 3), (3, 4))):
            strata = {"task_family": "repo", "difficulty_band": str(i), "risk_band": "low"}
            rows.append(MatchedExecution(self.receipt(f"b{i}", "baseline", c, b, 1), strata))
            rows.append(MatchedExecution(self.receipt(f"t{i}", "transplant", c, t, 1), strata))
        report = compare_matched_cohorts(c, SequentialCriteria(min_pairs=2, max_pairs=3), rows)
        self.assertEqual(report.decision, "STOP")
        self.assertTrue(report.blockers)


if __name__ == "__main__":
    unittest.main()
