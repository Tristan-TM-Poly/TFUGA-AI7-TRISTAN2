import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_auto2_api_gateway_p0.py"
VALID = ROOT / "fixtures" / "omega_auto2" / "api_gateway" / "valid_request.json"
INVALID = ROOT / "fixtures" / "omega_auto2" / "api_gateway" / "invalid_request.json"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_auto2_api_gateway_p0", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaAuto2ApiGatewayP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.valid = json.loads(VALID.read_text(encoding="utf-8"))
        cls.invalid = json.loads(INVALID.read_text(encoding="utf-8"))

    def test_valid_input_schema_passes(self):
        result = self.module.validate_input_envelope(self.valid)
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])

    def test_invalid_input_schema_fails(self):
        result = self.module.validate_input_envelope(self.invalid)
        self.assertFalse(result["ok"])
        self.assertIn("unsupported_operation:activate_billing", result["errors"])
        self.assertIn("field_must_be_object:payload", result["errors"])
        self.assertIn("request_id_empty", result["errors"])

    def test_oak_gate_detects_production_review_flag(self):
        oak = self.module.oak_gate(self.invalid)
        self.assertEqual(oak["status"], "FAIL")
        self.assertTrue(oak["review_required"])
        self.assertFalse(oak["external_actions_allowed"])
        self.assertFalse(oak["production_billing_allowed"])

    def test_gateway_core_returns_output_envelope(self):
        response = self.module.gateway_core(self.valid)
        self.assertEqual(response["request_id"], "req_synth_001")
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["oak_status"], "PASS")
        self.assertEqual(response["errors"], [])
        self.assertIn("result", response)
        self.assertIn("residue_report", response)
        self.assertEqual(response["next_action"], "ready_for_next_p0_card")

    def test_gateway_core_blocks_invalid_request(self):
        response = self.module.gateway_core(self.invalid)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["oak_status"], "FAIL")
        self.assertGreater(response["residue_report"]["error_count"], 0)
        self.assertEqual(response["next_action"], "fix_input")

    def test_custom_handler_is_used_for_allowed_operation(self):
        def handler(envelope):
            return {"custom": envelope["operation"]}

        response = self.module.gateway_core(self.valid, handlers={"validate_spectrum": handler})
        self.assertEqual(response["result"], {"custom": "validate_spectrum"})


if __name__ == "__main__":
    unittest.main()
