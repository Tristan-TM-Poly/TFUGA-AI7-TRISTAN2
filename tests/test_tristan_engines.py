"""Smoke tests for FTPCI-Omega, AIT-Pantheon and JKD-YY3-Tristan² engines.

These tests intentionally use only Python stdlib so they can run on free cloud
CI and local machines without dependency setup.
"""

from __future__ import annotations

import unittest

from sage_tristan.auto_meta_generator import run_generation
from sage_tristan.ait_pantheon import run_ait_cycle
from sage_tristan.jkd_yy3_tristan2 import run_jyt2


class AutoMetaGenerationTests(unittest.TestCase):
    def test_auto_meta_generation_is_deterministic_for_same_salt(self) -> None:
        first = run_generation(cycles=2, beam_width=4, salt="test-salt")
        second = run_generation(cycles=2, beam_width=4, salt="test-salt")
        self.assertEqual(first["top16"], second["top16"])
        self.assertEqual(len(first["top16"]), 4)
        self.assertEqual(len(first["negative_memory_bottom16"]), 4)

    def test_auto_meta_generation_produces_oak_note(self) -> None:
        result = run_generation(cycles=1, beam_width=4, salt="oak")
        self.assertIn("not a physical proof", result["oak_note"])
        self.assertGreater(result["evaluated_candidates_approx"], 0)


class AITPantheonTests(unittest.TestCase):
    def test_ait_pantheon_cycle_outputs_top_bottom_and_codex(self) -> None:
        result = run_ait_cycle("build verified AIT", cycles=1, salt="test-salt")
        self.assertEqual(len(result["top16"]), 16)
        self.assertEqual(len(result["bottom16"]), 16)
        self.assertIn("One-Page Codex", result["one_page_codex"])
        self.assertFalse(result["dense_enumeration"])

    def test_ait_pantheon_top_score_is_ordered(self) -> None:
        result = run_ait_cycle("score ordering", cycles=1, salt="ordering")
        scores = [candidate["score"] for candidate in result["top16"]]
        self.assertEqual(scores, sorted(scores, reverse=True))


class JKDYY3Tristan2Tests(unittest.TestCase):
    def test_jyt2_outputs_top1_codex(self) -> None:
        result = run_jyt2(cycles=1, salt="test-salt")
        self.assertEqual(len(result["top16"]), 16)
        self.assertEqual(len(result["bottom16"]), 16)
        self.assertIn("JKD-YY3-Tristan² Codex", result["codex_1p"])
        self.assertEqual(result["top1_jkd"], result["top16"][0])

    def test_jyt2_top_score_is_ordered(self) -> None:
        result = run_jyt2(cycles=1, salt="ordering")
        scores = [candidate["score"] for candidate in result["top16"]]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
