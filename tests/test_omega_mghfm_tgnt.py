"""Smoke tests for Omega-MGHFM-TGNT prototype engine."""

from __future__ import annotations

import unittest

from sage_tristan.omega_mghfm_tgnt import run_cycle


class OmegaMGHFMTGNTTests(unittest.TestCase):
    def test_cycle_outputs_mother_equation_and_layers(self) -> None:
        result = run_cycle(["prime tensor gaps", "LOG EXP codex", "OAK memory negative"])
        self.assertEqual(result["engine"], "Omega-MGHFM-TGNT")
        self.assertIn("X_next", result["mother_equation"])
        cycle = result["cycle"]
        self.assertIn("log_layers", cycle)
        self.assertIn("Lomega_minimal_fertile_signature", cycle["log_layers"])
        self.assertIn("cvcd", cycle)
        self.assertIn("jkd", cycle)
        self.assertIn("yy3", cycle)
        self.assertIn("tristan2", cycle)
        self.assertIn("tgnt", cycle)
        self.assertIn("oak", cycle)
        self.assertIn("exp", cycle)

    def test_cycle_has_oak_statuses_and_jkd_actions(self) -> None:
        result = run_cycle(["alpha beta", "beta gamma", "gamma delta"])
        statuses = result["cycle"]["oak"]["statuses"]
        self.assertTrue(any(value > 0 for value in statuses.values()))
        self.assertGreaterEqual(len(result["cycle"]["jkd"]["top_jkd_actions"]), 1)


if __name__ == "__main__":
    unittest.main()
