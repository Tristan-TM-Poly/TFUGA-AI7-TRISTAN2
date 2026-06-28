import json
import pathlib
import unittest

from omega_auto2_p0 import OAKEnvelope, combine_oak_status, run_p0_pipeline
from omega_auto2_p0.oak import OAK_FAIL, OAK_PASS, OAK_REVIEW_REQUIRED


ROOT = pathlib.Path(__file__).resolve().parents[1]
VALID_REQUEST = ROOT / "fixtures" / "omega_auto2" / "api_gateway" / "valid_request.json"
INVALID_REQUEST = ROOT / "fixtures" / "omega_auto2" / "api_gateway" / "invalid_request.json"


class OmegaAuto2P0IntegrationTests(unittest.TestCase):
    def test_combine_oak_status_is_conservative(self):
        self.assertEqual(combine_oak_status([OAK_PASS, OAK_PASS]), OAK_PASS)
        self.assertEqual(combine_oak_status([OAK_PASS, OAK_REVIEW_REQUIRED]), OAK_REVIEW_REQUIRED)
        self.assertEqual(combine_oak_status([OAK_PASS, OAK_FAIL]), OAK_FAIL)

    def test_oak_envelope_defaults_lock_external_actions(self):
        envelope = OAKEnvelope(oak_status=OAK_PASS)
        self.assertFalse(envelope.external_actions_allowed)
        self.assertFalse(envelope.production_use_allowed)
        self.assertEqual(envelope.to_dict()["oak_status"], OAK_PASS)

    def test_valid_request_runs_full_p0_pipeline(self):
        request = json.loads(VALID_REQUEST.read_text(encoding="utf-8"))
        report = run_p0_pipeline(request)
        self.assertEqual(report["oak_status"], OAK_PASS)
        self.assertEqual(report["module_statuses"]["gateway"], OAK_PASS)
        self.assertEqual(report["module_statuses"]["spectral_core"], OAK_PASS)
        self.assertEqual(report["module_statuses"]["usage_events"], OAK_PASS)
        self.assertFalse(report["external_actions_allowed"])
        self.assertFalse(report["production_use_allowed"])
        self.assertEqual(report["next_action"], "ready_for_spectral_cleaning_p0")

    def test_invalid_request_stops_at_gateway(self):
        request = json.loads(INVALID_REQUEST.read_text(encoding="utf-8"))
        report = run_p0_pipeline(request)
        self.assertEqual(report["oak_status"], OAK_FAIL)
        self.assertEqual(report["module_statuses"]["gateway"], OAK_FAIL)
        self.assertEqual(report["spectral_core"], {})
        self.assertEqual(report["usage_events"], {})
        self.assertEqual(report["next_action"], "fix_gateway_input")


if __name__ == "__main__":
    unittest.main()
