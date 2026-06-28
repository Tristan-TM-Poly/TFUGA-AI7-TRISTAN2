import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_auto2_usage_events_p0.py"
VALID = ROOT / "fixtures" / "omega_auto2" / "usage_events" / "valid_event.json"
INVALID = ROOT / "fixtures" / "omega_auto2" / "usage_events" / "invalid_event.json"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_auto2_usage_events_p0", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaAuto2UsageEventsP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.valid = json.loads(VALID.read_text(encoding="utf-8"))
        cls.invalid = json.loads(INVALID.read_text(encoding="utf-8"))

    def test_valid_event_passes(self):
        result = self.module.validate_usage_event(self.valid)
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])

    def test_invalid_event_fails(self):
        result = self.module.validate_usage_event(self.invalid)
        self.assertFalse(result["ok"])
        self.assertIn("unsupported_unit_type:currency", result["errors"])
        self.assertIn("units_must_be_non_negative", result["errors"])

    def test_normalized_valid_event(self):
        result = self.module.normalize_usage_event(self.valid)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["oak_status"], "PASS")
        self.assertEqual(result["record"]["units"], 1.0)
        self.assertTrue(result["record"]["synthetic_only"])

    def test_invalid_event_returns_error_record(self):
        result = self.module.normalize_usage_event(self.invalid)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["oak_status"], "FAIL")
        self.assertEqual(result["record"], {})
        self.assertGreater(len(result["errors"]), 0)


if __name__ == "__main__":
    unittest.main()
