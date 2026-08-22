import unittest
from pathlib import Path

from omega_tristan_meta.representation_tournament import (
    COMPETITORS,
    evaluate_representation,
    load_corpus,
    pareto_front,
    run_tournament,
)

CORPUS = Path("benchmarks/meta_representation_r02.json")


class RepresentationTournamentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = load_corpus(CORPUS)
        cls.report = run_tournament(cls.tasks)

    def test_frozen_corpus_has_three_domains_and_four_competitors(self):
        self.assertGreaterEqual(len({task.domain for task in self.tasks}), 3)
        self.assertEqual(len(COMPETITORS), 4)

    def test_every_competitor_preserves_hard_probes(self):
        for task in self.tasks:
            for competitor in COMPETITORS:
                self.assertTrue(evaluate_representation(task, competitor).hard_gate_pass)

    def test_adversarial_case_makes_morph_genome_lose(self):
        adversarial = [task for task in self.tasks if task.adversarial]
        self.assertTrue(adversarial)
        for task in adversarial:
            results = [evaluate_representation(task, competitor) for competitor in COMPETITORS]
            self.assertNotIn("morph_genome", pareto_front(results))

    def test_cross_domain_cases_keep_tradeoff_visible(self):
        non_adversarial = [task for task in self.tasks if not task.adversarial]
        self.assertTrue(non_adversarial)
        self.assertTrue(any(
            "morph_genome" in pareto_front([evaluate_representation(task, competitor) for competitor in COMPETITORS])
            for task in non_adversarial
        ))

    def test_no_scalar_fitness(self):
        self.assertEqual(self.report["scalar_score"], "NOT_USED")

    def test_memory_contains_positive_negative_and_open_question(self):
        self.assertTrue(self.report["memory"]["M+"])
        self.assertTrue(self.report["memory"]["M-"])
        self.assertTrue(self.report["memory"]["M?"])

    def test_report_is_deterministic(self):
        self.assertEqual(self.report, run_tournament(self.tasks))

    def test_receipt_digest_is_content_addressed(self):
        self.assertEqual(len(self.report["receipt_digest"]), 64)
        int(self.report["receipt_digest"], 16)

    def test_simulation_boundary_is_explicit(self):
        self.assertEqual(self.report["evidence_class"], "SIMULATED_ENGINEERING")
        self.assertIn("Simulation != Reality", self.report["hard_gates"])

    def test_validity_domain_is_explicit(self):
        self.assertTrue(all(item["validity_domain"] for item in self.report["decisions"]))

    def test_acceptance_status_passes_frozen_engineering_court(self):
        self.assertEqual(self.report["status"], "PASS")
        self.assertTrue(self.report["morph_lost_adversarial"])


if __name__ == "__main__":
    unittest.main()
