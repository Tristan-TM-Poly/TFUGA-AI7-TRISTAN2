import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_auto2_oakbench_p0.py"
MMINUS = ROOT / "configs" / "omega_auto2_mminus_registry.json"
SUITE = ROOT / "fixtures" / "omega_auto2" / "oakbench" / "p0_benchmark_suite.json"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_auto2_oakbench_p0", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaAuto2OAKBenchP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_mminus_registry_is_valid(self):
        registry = self.module.load_mminus_registry(MMINUS)
        self.assertTrue(registry["valid"])
        self.assertEqual(registry["duplicate_ids"], [])
        self.assertGreaterEqual(registry["entry_count"], 8)
        self.assertIn("api_gateway", registry["modules"])
        self.assertIn("spectral_cleaning", registry["modules"])

    def test_oakbench_suite_passes(self):
        report = self.module.run_suite(SUITE, MMINUS, repo_root=ROOT)
        self.assertEqual(report["oak_status"], "PASS")
        self.assertEqual(report["case_count"], 2)
        self.assertEqual(report["failed_count"], 0)
        self.assertFalse(report["external_actions_allowed"])
        self.assertFalse(report["production_use_allowed"])
        self.assertEqual(report["next_action"], "ready_for_demo_pack_p0")

    def test_each_case_has_expected_shape(self):
        report = self.module.run_suite(SUITE, MMINUS, repo_root=ROOT)
        for case in report["cases"]:
            self.assertIn("case_id", case)
            self.assertIn("actual_oak_status", case)
            self.assertIn("module_statuses", case)
            self.assertTrue(case["passed"])


if __name__ == "__main__":
    unittest.main()
