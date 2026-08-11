import unittest

from omega_skillgen_t.adversary import enrich_with_adversarial_evals, generate_adversarial_evals
from omega_skillgen_t.core import validate_spec
from omega_skillgen_t.lineage import lineage_audit
from omega_skillgen_t.package import DEFAULT_WRAPPERS
from omega_skillgen_t.planner import plan_expansion


def spec(name):
    return {
        "name": name,
        "description": f"A valid {name} skill description for civilization-level skill planning.",
        "purpose": "Exercise civilization-level planning.",
        "use_when": [f"{name} research."],
        "do_not_use_when": ["Translation only."],
        "workflow": ["Analyze evidence."],
        "invariants": ["Do not call simulation proof."],
        "tool_policy": ["Require approval for external writes."],
        "outputs": ["Report"],
        "definition_of_done": ["Evidence state remains explicit."],
        "eval_cases": [
            {"id": "p", "prompt": "Do.", "class": "positive"},
            {"id": "n", "prompt": "No.", "class": "negative"},
            {"id": "i", "prompt": "It.", "class": "incomplete"},
            {"id": "e", "prompt": "Edge.", "class": "edge"},
        ],
    }


class CivilizationTests(unittest.TestCase):
    def test_adversary_compiles_declared_constraints(self):
        cases = generate_adversarial_evals(spec("a"))
        self.assertEqual(len(cases), 3)
        self.assertTrue(any(case["class"] == "negative" for case in cases))
        self.assertTrue(any(case["class"] == "adversarial" for case in cases))
        enriched = enrich_with_adversarial_evals(spec("a"))
        self.assertEqual(validate_spec(enriched), [])
        self.assertEqual(enriched["adversarial_generation"]["generated_count"], 3)

    def test_lineage_dag_detects_cycle(self):
        a = spec("a")
        b = spec("b")
        c = spec("c")
        b["lineage"] = {"parent": "a"}
        c["lineage"] = {"parents": ["a", "b"]}
        audit = lineage_audit([a, b, c])
        self.assertFalse(audit["cycle_detected"])
        self.assertEqual(audit["edge_count"], 3)
        a["lineage"] = {"parent": "c"}
        self.assertTrue(lineage_audit([a, b, c])["cycle_detected"])

    def test_expansion_planner_generates_only_uncovered_task(self):
        plan = plan_expansion([spec("research")], ["research", "quantum compiler"])
        self.assertEqual(len(plan["generation_tasks"]), 1)
        self.assertEqual(plan["generation_tasks"][0]["capability"], "quantum compiler")
        self.assertFalse(plan["generation_tasks"][0]["auto_promote"])

    def test_civilization_wrapper_is_packaged(self):
        self.assertIn("omega-skillgen-civilization", DEFAULT_WRAPPERS)


if __name__ == "__main__":
    unittest.main()
