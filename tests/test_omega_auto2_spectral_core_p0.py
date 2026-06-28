import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_auto2_spectral_core_p0.py"
VALID = ROOT / "fixtures" / "omega_auto2" / "spectral_core" / "valid_spectrum.json"
INVALID = ROOT / "fixtures" / "omega_auto2" / "spectral_core" / "invalid_spectrum.json"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_auto2_spectral_core_p0", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaAuto2SpectralCoreP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.valid = json.loads(VALID.read_text(encoding="utf-8"))
        cls.invalid = json.loads(INVALID.read_text(encoding="utf-8"))

    def test_valid_axis_passes(self):
        result = self.module.validate_axis(self.valid["axis"], unit="nm")
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["summary"]["direction"], "increasing")

    def test_invalid_axis_fails(self):
        result = self.module.validate_axis(self.invalid["axis"], unit="unknown_unit")
        self.assertFalse(result["ok"])
        self.assertIn("unsupported_axis_unit:unknown_unit", result["errors"])
        self.assertTrue(any(error in result["errors"] for error in ["axis_not_monotonic", "axis_contains_duplicate_neighbors"]))

    def test_valid_schema_passes(self):
        result = self.module.validate_spectrum_schema(self.valid)
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])

    def test_invalid_schema_fails(self):
        result = self.module.validate_spectrum_schema(self.invalid)
        self.assertFalse(result["ok"])
        self.assertIn("spectrum_id_empty", result["errors"])
        self.assertIn("axis_intensity_length_mismatch", result["errors"])
        self.assertIn("intensity_value_not_finite_number:1", result["errors"])

    def test_oak_report_valid(self):
        report = self.module.oak_report(self.valid)
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["external_actions_allowed"])
        self.assertFalse(report["production_use_allowed"])
        self.assertEqual(report["residue_report"]["error_count"], 0)

    def test_oak_report_invalid(self):
        report = self.module.oak_report(self.invalid)
        self.assertEqual(report["status"], "FAIL")
        self.assertGreater(report["residue_report"]["error_count"], 0)
        self.assertEqual(report["next_action"], "fix_spectrum_fixture")


if __name__ == "__main__":
    unittest.main()
