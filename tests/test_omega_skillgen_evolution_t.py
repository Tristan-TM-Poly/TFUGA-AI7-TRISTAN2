import unittest

from omega_skillgen_t.core import validate_spec
from omega_skillgen_t.evolution import (
    infer_repair_actions,
    preservation_contracts_from_mplus,
    repair_from_mminus,
)
from omega_skillgen_t.package import DEFAULT_WRAPPERS


def base_spec():
    return {
        "name": "research-skill",
        "description": "A valid research skill description for testing evidence-driven repairs.",
        "purpose": "Test evidence-driven skill repair.",
        "use_when": ["Research audit."],
        "do_not_use_when": ["Translation only."],
        "workflow": ["Analyze claim."],
        "invariants": ["Static pass is not behavioral proof."],
        "outputs": ["Report"],
        "definition_of_done": ["Evidence state remains explicit."],
        "eval_cases": [
            {"id": "p", "prompt": "Do.", "class": "positive"},
            {"id": "n", "prompt": "No.", "class": "negative"},
            {"id": "i", "prompt": "It.", "class": "incomplete"},
            {"id": "e", "prompt": "Edge.", "class": "edge"},
        ],
    }


class EvolutionTests(unittest.TestCase):
    def test_failure_mode_infers_targeted_guard(self):
        record = {
            "failure_mode": "epistemic_overclaim",
            "repair": "strengthen proof/evidence guard",
        }
        self.assertTrue(
            any(action["kind"] == "invariant" for action in infer_repair_actions(record))
        )

    def test_mminus_repairs_generate_valid_candidate_and_regressions(self):
        records = [
            {
                "eval_id": "a1",
                "failure_mode": "epistemic_overclaim",
                "evidence": "plot called proof",
                "repair": "keep plot as evidence only",
            },
            {
                "eval_id": "b1",
                "failure_mode": "missing_baseline",
                "evidence": "baseline absent",
                "repair": "compare established baseline",
            },
        ]
        child = repair_from_mminus(base_spec(), records)
        self.assertEqual(validate_spec(child), [])
        self.assertEqual(child["lineage"]["failure_count"], 2)
        self.assertTrue(child["workflow"][0].lower().startswith("identify and compare"))
        self.assertEqual(len(child["eval_cases"]), 6)
        self.assertTrue(any("cause hypotheses" in invariant for invariant in child["invariants"]))

    def test_mplus_becomes_preservation_contract_not_new_proof(self):
        contracts = preservation_contracts_from_mplus(
            [
                {
                    "eval_id": "p1",
                    "evidence": "trace-17",
                    "dimensions": {"quality": 0.9},
                }
            ]
        )
        self.assertTrue(contracts[0]["must_preserve"])
        self.assertEqual(contracts[0]["evidence"], "trace-17")

    def test_evolution_wrapper_is_packaged(self):
        self.assertIn("omega-skillgen-evolution", DEFAULT_WRAPPERS)


if __name__ == "__main__":
    unittest.main()
