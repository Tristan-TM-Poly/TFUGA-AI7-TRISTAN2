import unittest

from omega_generative_closure_t.reprovenance_replay import (
    FrozenSlice,
    counterfactual_replay,
    cross_run_reproducibility,
    historical_replay,
    provenance_independence,
    r10_promotion_gate,
)


class MetaTheoryR10ReprovenanceReplayTests(unittest.TestCase):
    def test_independent_slices_pass(self):
        report = provenance_independence(
            (
                FrozenSlice.make("a", ["source-a"], ["bench-a"]),
                FrozenSlice.make("b", ["source-b"], ["bench-b"]),
            ),
            training_provenance_ids=["train-a"],
        )
        self.assertEqual(report.oak_status, "PASS")

    def test_shared_provenance_and_benchmark_leakage_hold(self):
        report = provenance_independence(
            (
                FrozenSlice.make("a", ["shared"], ["train-a"]),
                FrozenSlice.make("b", ["shared"], ["bench-b"]),
            ),
            training_provenance_ids=["train-a"],
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("shared_provenance_detected", report.blockers)
        self.assertIn("benchmark_training_leakage_detected", report.blockers)

    def test_cross_run_reproducibility_passes_identical_frozen_cases(self):
        report = cross_run_reproducibility(
            {
                "run-a": {"c1": "SELECT", "c2": "HOLD"},
                "run-b": {"c1": "SELECT", "c2": "HOLD"},
            }
        )
        self.assertEqual(report.oak_status, "PASS")
        self.assertEqual(report.agreement_ratio, 1.0)

    def test_cross_run_instability_holds(self):
        report = cross_run_reproducibility(
            {
                "run-a": {"c1": "SELECT", "c2": "HOLD"},
                "run-b": {"c1": "HOLD", "c2": "HOLD"},
            }
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("cross_run_decision_instability", report.blockers)

    def test_historical_replay_blocks_unapproved_changes(self):
        report = historical_replay(
            {"c1": "SELECT", "c2": "HOLD"},
            {"c1": "HOLD", "c2": "HOLD"},
        )
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("unapproved_historical_decision_regression", report.blockers)

    def test_counterfactual_replay_requires_regression_budget(self):
        report = counterfactual_replay(((1.0, 1.2), (1.0, 0.8)))
        self.assertEqual(report.oak_status, "HOLD")
        self.assertIn("counterfactual_regression_budget_exceeded", report.blockers)

    def test_full_gate_promotes_only_all_pass(self):
        provenance = provenance_independence(
            (
                FrozenSlice.make("a", ["source-a"]),
                FrozenSlice.make("b", ["source-b"]),
            )
        )
        reproducibility = cross_run_reproducibility(
            {
                "run-a": {"c1": "SELECT"},
                "run-b": {"c1": "SELECT"},
            }
        )
        historical = historical_replay({"c1": "SELECT"}, {"c1": "SELECT"})
        counterfactual = counterfactual_replay(((1.0, 1.1), (1.0, 1.2)))
        gate = r10_promotion_gate(provenance, reproducibility, historical, counterfactual)
        self.assertEqual(gate.decision, "PROMOTE")
        self.assertFalse(gate.blockers)


if __name__ == "__main__":
    unittest.main()
