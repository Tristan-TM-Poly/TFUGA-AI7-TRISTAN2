import unittest

from omega_skillgen_t.core import validate_spec
from omega_skillgen_t.discovery_bridge import record_to_skill_spec
from omega_skillgen_t.cvcd import extract_primitives
from omega_skillgen_t.registry import validate_transition


class OmegaSkillGenBridgeTests(unittest.TestCase):
    def test_generator_record_compiles_to_valid_skillspec(self):
        record = {
            "id": "gen-42",
            "domain": "physics",
            "family": "spectral",
            "scale": "meso",
            "representation": "tensor",
            "status": "candidate",
            "invariant": "preserve energy",
            "risk": "medium",
            "parameter_count": 4,
            "supports_inverse": True,
            "oak_gate": "benchmark-required",
            "benchmark_ids": ["b1", "b2"],
        }
        spec = record_to_skill_spec(record)
        self.assertEqual(validate_spec(spec), [])
        self.assertEqual(spec["generator_discovery_provenance"]["id"], "gen-42")
        self.assertIn("preserve energy", spec["invariants"][0])

    def test_cvcd_extracts_shared_primitives(self):
        specs = [
            {"name":"a","workflow":["Run OAK.","Compare baseline."],"invariants":["Static pass is not proof."]},
            {"name":"b","workflow":["Run OAK.","Compare baseline."],"invariants":["Static pass is not proof."]},
        ]
        result = extract_primitives(specs, min_support=2)
        self.assertEqual(len(result["workflow_primitives"]), 2)
        self.assertEqual(len(result["invariant_primitives"]), 1)

    def test_promotion_states_cannot_be_skipped(self):
        self.assertEqual(validate_transition("DRAFT", "STATIC_PASS", {"lint_pass": True}), [])
        self.assertTrue(validate_transition("STATIC_PASS", "BEHAVIORAL_PASS", {"behavioral_eval_pass": True}))
        self.assertTrue(validate_transition("EVAL_READY", "TRUST_REVIEWED", {}))
        self.assertEqual(validate_transition("EVAL_READY", "TRUST_REVIEWED", {"trust_reviewed": True}), [])

    def test_rollback_requires_reason(self):
        self.assertTrue(validate_transition("BEHAVIORAL_PASS", "EVAL_READY", {}))
        self.assertEqual(validate_transition("BEHAVIORAL_PASS", "EVAL_READY", {"rollback_reason": "new regression"}), [])


if __name__ == "__main__":
    unittest.main()
