import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_auto2_spectral_cleaning_p0.py"
VALID = ROOT / "fixtures" / "omega_auto2" / "spectral_cleaning" / "valid_cleaning_spectrum.json"
INVALID = ROOT / "fixtures" / "omega_auto2" / "spectral_cleaning" / "invalid_cleaning_spectrum.json"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_auto2_spectral_cleaning_p0", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaAuto2SpectralCleaningP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.valid = json.loads(VALID.read_text(encoding="utf-8"))
        cls.invalid = json.loads(INVALID.read_text(encoding="utf-8"))

    def test_human_locks_are_disabled_by_default(self):
        self.assertFalse(self.module.EXTERNAL_ACTIONS_ALLOWED)
        self.assertFalse(self.module.PRODUCTION_USE_ALLOWED)
        self.assertFalse(self.module.CUSTOMER_DATA_ALLOWED)

    def test_noise_estimation_returns_number(self):
        report = self.module.estimate_noise([1.0, 1.1, 1.2, 1.3])
        self.assertTrue(report["ok"])
        self.assertIn("noise_level", report)
        self.assertGreaterEqual(report["noise_level"], 0.0)

    def test_spike_removal_detects_synthetic_spike(self):
        intensity = self.valid["intensity"]
        report = self.module.remove_spikes(intensity, threshold=2.0)
        self.assertIn(3, report["spike_indices"])
        self.assertLess(report["cleaned"][3], intensity[3])

    def test_baseline_correction_matches_lengths(self):
        axis = self.valid["axis"]
        intensity = self.valid["intensity"]
        report = self.module.estimate_linear_baseline(axis, intensity)
        self.assertTrue(report["ok"])
        self.assertEqual(len(report["baseline"]), len(axis))
        self.assertEqual(len(report["corrected"]), len(axis))

    def test_clean_spectrum_valid_passes(self):
        report = self.module.clean_spectrum(self.valid, spike_threshold=2.0)
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["external_actions_allowed"])
        self.assertFalse(report["production_use_allowed"])
        self.assertIn(3, report["result"]["spike_indices"])
        self.assertEqual(report["next_action"], "ready_for_oakbench_p0")

    def test_clean_spectrum_invalid_fails(self):
        report = self.module.clean_spectrum(self.invalid)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["result"], {})
        self.assertGreater(report["residue_report"]["error_count"], 0)
        self.assertEqual(report["next_action"], "fix_spectrum_fixture")


if __name__ == "__main__":
    unittest.main()
