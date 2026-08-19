#!/usr/bin/env python3
"""Tests for the ServiceGraph-QC MVP."""

from __future__ import annotations

import unittest
from pathlib import Path

from oak_service_meter import parse_simple_yaml, score_service
from friction_map import recommend_action


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class ServiceGraphQCTests(unittest.TestCase):
    def test_examples_parse_and_score(self) -> None:
        examples = sorted(EXAMPLES.glob("*.yaml"))
        self.assertGreaterEqual(len(examples), 4)
        for path in examples:
            with self.subTest(path=path.name):
                data = parse_simple_yaml(path)
                self.assertIn("service_id", data)
                self.assertIn("service_name", data)
                self.assertIn("friction_points", data)
                report = score_service(data)
                self.assertGreaterEqual(report["oak_score"], 0)
                self.assertLessEqual(report["oak_score"], 100)
                self.assertRegex(report["maturity_level"], r"^L[0-7]$")

    def test_parser_supports_lists_and_maps(self) -> None:
        data = parse_simple_yaml(EXAMPLES / "saaq_renew_license.yaml")
        self.assertIsInstance(data["channels"], list)
        self.assertIsInstance(data["metric_inputs"], dict)
        self.assertIn("resolution", data["metric_inputs"])

    def test_friction_recommendations_are_actionable(self) -> None:
        action = recommend_action("statut de demande non visible")
        self.assertIn("où-est-ma-demande", action)
        fallback = recommend_action("friction inconnue")
        self.assertIn("cause racine", fallback)


if __name__ == "__main__":
    unittest.main()
