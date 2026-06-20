import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "omega_response_impact_analyzer.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_response_impact_analyzer", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ResponseImpactAnalyzerTests(unittest.TestCase):
    def test_high_diversity_scores_strong(self):
        mod = load_module()
        data = mod.ImpactInput(
            artifacts=[
                "scripts/a.py",
                "tests/test_a.py",
                ".github/workflows/a.yml",
                "docs/a.md",
                "ops/a/runbook.md",
                "configs/a.json",
                "schemas/a/schema.json",
                "interfaces/x/index.html",
            ],
            summary="OAK bounded prototype review license residue workflow publication data chatgpt",
            tests=["unit", "validator"],
            workflows=["ci"],
            residues=["heuristic only"],
        )
        report = mod.score_input(data, mod.DEFAULT_AXES)
        self.assertGreaterEqual(report["score"], 60)
        self.assertIn("code", report["categories"])
        self.assertIn("workflow", report["categories"])

    def test_empty_is_weak(self):
        mod = load_module()
        report = mod.score_input(mod.ImpactInput(artifacts=[]), mod.DEFAULT_AXES)
        self.assertEqual(report["rating"], "weak")
        self.assertEqual(report["artifact_count"], 0)


if __name__ == "__main__":
    unittest.main()
