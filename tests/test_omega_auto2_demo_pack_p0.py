import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_auto2_demo_pack_p0.py"
DEMO_REQUEST = ROOT / "fixtures" / "omega_auto2" / "demo_pack" / "demo_request.json"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_auto2_demo_pack_p0", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaAuto2DemoPackP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.request = json.loads(DEMO_REQUEST.read_text(encoding="utf-8"))

    def test_demo_report_passes(self):
        report = self.module.generate_demo_report(self.request)
        self.assertEqual(report["oak_status"], "PASS")
        self.assertEqual(report["demo_id"], "omega_auto2_demo_pack_p0")
        self.assertEqual(report["summary"]["demo_next_action"], "ready_for_review_pack_p0")

    def test_before_after_shape(self):
        report = self.module.generate_demo_report(self.request)
        before_after = report["before_after"]
        point_count = len(before_after["axis"])
        self.assertEqual(len(before_after["raw_intensity"]), point_count)
        self.assertEqual(len(before_after["spike_removed_intensity"]), point_count)
        self.assertEqual(len(before_after["baseline"]), point_count)
        self.assertEqual(len(before_after["baseline_corrected_intensity"]), point_count)
        self.assertIn(3, before_after["spike_indices"])

    def test_oak_disclaimer_locks_are_false(self):
        report = self.module.generate_demo_report(self.request)
        disclaimer = report["oak_disclaimer"]
        self.assertTrue(disclaimer["synthetic_only"])
        self.assertFalse(disclaimer["external_actions_allowed"])
        self.assertFalse(disclaimer["production_use_allowed"])
        self.assertFalse(disclaimer["customer_data_allowed"])
        self.assertFalse(disclaimer["scientific_or_regulatory_claim"])
        self.assertFalse(disclaimer["commercial_claim"])

    def test_output_file_can_be_written(self):
        report = self.module.generate_demo_report(self.request)
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "nested" / "demo_report.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            loaded = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(loaded["oak_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
