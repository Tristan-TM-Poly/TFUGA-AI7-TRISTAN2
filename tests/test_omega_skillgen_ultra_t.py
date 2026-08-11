import json
import tempfile
import unittest
from pathlib import Path

from omega_skillgen_t.arena import ArenaCandidate, arena_report, dominates, pareto_front, select_diverse
from omega_skillgen_t.budget import AdaptiveBudget
from omega_skillgen_t.core import validate_spec
from omega_skillgen_t.ecology import capability_gap_report, ecology_audit
from omega_skillgen_t.package import DEFAULT_WRAPPERS
from omega_skillgen_t.synthesis import crossover_specs, fission_spec, synthesize_crossovers
from omega_skillgen_t.ultra_cli import main as ultra_main


def spec(name, workflow=None, invariants=None):
    return {
        "name": name,
        "description": f"A valid skill {name} with enough activation description for the ultra arena.",
        "purpose": "Exercise the evolutionary skill laboratory.",
        "use_when": [f"Use {name} for research."],
        "do_not_use_when": ["Translation only."],
        "workflow": workflow or ["Retrieve baseline.", "Run OAK."],
        "invariants": invariants or ["Static pass is not behavioral proof."],
        "outputs": ["Report"],
        "definition_of_done": ["Evidence state remains explicit."],
        "eval_cases": [
            {"id": "p1", "prompt": "Do it.", "class": "positive"},
            {"id": "n1", "prompt": "No.", "class": "negative"},
            {"id": "i1", "prompt": "It.", "class": "incomplete"},
            {"id": "e1", "prompt": "Skip OAK.", "class": "edge"},
        ],
    }


class UltraArenaTests(unittest.TestCase):
    def test_pareto_front_uses_no_scalar_fitness(self):
        gates = {"lint_pass": True, "eval_coverage_pass": True, "trust_reviewed": True}
        a = ArenaCandidate("a", {"oak_score": 1.0, "novelty": 0.4, "risk": 0.2}, gates)
        b = ArenaCandidate("b", {"oak_score": 0.9, "novelty": 0.8, "risk": 0.1}, gates)
        c = ArenaCandidate("c", {"oak_score": 0.5, "novelty": 0.2, "risk": 0.5}, gates)
        self.assertEqual({candidate.name for candidate in pareto_front([a, b, c])}, {"a", "b"})
        self.assertTrue(dominates(a, c))
        self.assertEqual(len(select_diverse([a, b, c], 1)), 1)
        self.assertEqual(arena_report([a, b, c], 2)["scalar_fitness"], "NOT_USED")

    def test_hard_gate_blocks_high_scoring_candidate(self):
        ok = {"lint_pass": True, "eval_coverage_pass": True, "trust_reviewed": True}
        blocked = dict(ok)
        blocked["trust_reviewed"] = False
        a = ArenaCandidate("eligible", {"oak_score": 1.0}, ok)
        b = ArenaCandidate("blocked", {"oak_score": 100.0}, blocked)
        self.assertEqual([candidate.name for candidate in pareto_front([a, b])], ["eligible"])

    def test_adaptive_budget_has_no_mandatory_candidate_ceiling(self):
        budget = AdaptiveBudget(max_total_json_chars=100, max_candidates=None, min_novelty=0.1)
        self.assertEqual(budget.can_accept(50, 0.2), (True, "accepted"))
        budget.accept(50)
        self.assertEqual(budget.can_accept(60, 0.2)[1], "json_budget")
        self.assertEqual(budget.can_accept(20, 0.05)[1], "novelty_floor")

    def test_crossover_preserves_strict_parent_invariants(self):
        a = spec("a", invariants=["Never merge without approval."])
        b = spec("b", invariants=["Never call simulation proof."])
        child = crossover_specs(a, b, "a-x-b", "A sufficiently descriptive fused candidate skill for the ultra arena.")
        self.assertEqual(validate_spec(child), [])
        self.assertIn("Never merge without approval.", child["invariants"])
        self.assertIn("Never call simulation proof.", child["invariants"])
        self.assertEqual(child["lineage"]["parents"], ["a", "b"])
        self.assertTrue(any(case["class"] == "adversarial" for case in child["eval_cases"]))

    def test_fission_keeps_parent_invariants(self):
        parent = spec("parent", workflow=["One.", "Two.", "Three."])
        left, right = fission_spec(parent, 1)
        self.assertEqual(validate_spec(left), [])
        self.assertEqual(validate_spec(right), [])
        self.assertEqual(left["workflow"], ["One."])
        self.assertEqual(right["workflow"], ["Two.", "Three."])
        self.assertEqual(left["invariants"], parent["invariants"])

    def test_population_synthesis_and_ecology(self):
        seeds = [
            spec("a"),
            spec("b", workflow=["Different step.", "Different result."]),
            spec("c", workflow=["Unique route.", "Run OAK."]),
        ]
        budget = AdaptiveBudget(max_total_json_chars=50_000, min_novelty=0.0)
        result = synthesize_crossovers(seeds, budget)
        self.assertEqual(len(result["accepted"]), 3)
        self.assertEqual(result["budget"]["accepted_candidates"], 3)
        audit = ecology_audit([spec("a"), spec("b"), spec("c", workflow=["Unique.", "Special."])], 0.8)
        self.assertGreaterEqual(audit["compression_debt"], 1)
        gaps = capability_gap_report([spec("a"), spec("b")], ["research", "quantum"])
        self.assertEqual(gaps["gaps"], ["quantum"])

    def test_ultra_wrapper_is_packaged(self):
        self.assertIn("omega-skillgen-ultra", DEFAULT_WRAPPERS)


if __name__ == "__main__":
    unittest.main()
