import unittest
from dataclasses import replace
from pathlib import Path

from omega_tristan_meta.representation_tournament import (
    COMPETITORS,
    load_corpus,
    run_tournament,
)
from omega_tristan_meta.source_anchor import verify_source_anchor, verify_source_anchors


CORPUS = Path("benchmarks/meta_morph_representation_r0_2/corpus.json")


class RepresentationTournamentTests(unittest.TestCase):
    def test_corpus_is_frozen_multi_domain_and_contains_adversary(self):
        cases = load_corpus(CORPUS)
        self.assertGreaterEqual(len({case.domain for case in cases}), 3)
        self.assertTrue(any(case.adversarial_for_morph_genome for case in cases))
        self.assertEqual(COMPETITORS, ("MORPH_GENOME", "DOMAIN_SPECIFIC", "MINIMAL_DICT", "NO_ABSTRACTION"))

    def test_source_refs_anchor_materialized_domains(self):
        cases = load_corpus(CORPUS)
        self.assertTrue(all(case.source_ref for case in cases))
        self.assertTrue(any("skill_civilization.py::SkillGenome" in case.source_ref for case in cases))
        self.assertTrue(any("scheduler.py::ScheduledTask" in case.source_ref for case in cases))
        self.assertTrue(any("models.py::ValueGenome" in case.source_ref for case in cases))
        checks = verify_source_anchors(cases, repo_root=Path("."))
        self.assertEqual(len(checks), len(cases))
        self.assertTrue(all(check.passed for check in checks), checks)

    def test_source_anchor_fails_closed_when_symbol_disappears(self):
        case = load_corpus(CORPUS)[0]
        broken = replace(case, source_ref="omega_tristan_meta/skill_civilization.py::DefinitelyMissingAnchor")
        check = verify_source_anchor(broken, repo_root=Path("."))
        self.assertTrue(check.file_exists)
        self.assertFalse(check.anchor_found)
        self.assertFalse(check.passed)
        self.assertEqual(check.reason, "anchor token not found")

    def test_source_anchor_rejects_repository_escape(self):
        case = load_corpus(CORPUS)[0]
        escaped = replace(case, source_ref="../outside.txt::secret")
        check = verify_source_anchor(escaped, repo_root=Path("."))
        self.assertFalse(check.passed)
        self.assertEqual(check.reason, "source_ref escapes repository root")

    def test_every_case_retains_every_competitor_result(self):
        cases = load_corpus(CORPUS)
        report = run_tournament(CORPUS)
        self.assertEqual(len(report.results), len(cases) * len(COMPETITORS))
        observed = {(result.case_id, result.competitor) for result in report.results}
        expected = {(case.id, competitor) for case in cases for competitor in COMPETITORS}
        self.assertEqual(observed, expected)

    def test_hard_gates_prevent_minimal_dict_from_hiding_missing_falsifiers(self):
        report = run_tournament(CORPUS)
        minimal = [result for result in report.results if result.competitor == "MINIMAL_DICT"]
        self.assertTrue(minimal)
        self.assertTrue(all(result.mutation_detection < 1.0 for result in minimal))
        self.assertTrue(all(not result.hard_gate_pass for result in minimal))

    def test_adversarial_case_makes_morph_genome_lose_pareto_front(self):
        cases = {case.id: case for case in load_corpus(CORPUS)}
        report = run_tournament(CORPUS)
        decisions = {decision.case_id: decision for decision in report.decisions}
        adversarial_ids = {case.id for case in cases.values() if case.adversarial_for_morph_genome}
        self.assertTrue(adversarial_ids)
        for case_id in adversarial_ids:
            self.assertNotIn("MORPH_GENOME", decisions[case_id].pareto_front)

    def test_decisions_expose_nonempty_pareto_front_of_hard_gate_passers(self):
        report = run_tournament(CORPUS)
        by_key = {(result.case_id, result.competitor): result for result in report.results}
        for decision in report.decisions:
            self.assertTrue(decision.pareto_front)
            for competitor in decision.pareto_front:
                self.assertTrue(by_key[(decision.case_id, competitor)].hard_gate_pass)
            self.assertIn(decision.winner, decision.pareto_front)

    def test_no_scalar_score_hides_tradeoffs(self):
        report = run_tournament(CORPUS)
        self.assertEqual(report.scalar_score, "NOT_USED")

    def test_frozen_corpus_narrows_or_prunes_generic_claim(self):
        report = run_tournament(CORPUS)
        self.assertIn(report.morph_genome_disposition, {"NARROW", "PRUNE_GENERIC_CLAIM"})
        self.assertFalse(report.global_pass)
        self.assertFalse(report.external_action_performed)
        self.assertFalse(report.auto_promoted)

    def test_memory_keeps_negative_and_open_question_without_fabricated_positive(self):
        report = run_tournament(CORPUS)
        self.assertEqual(set(report.memory), {"M+", "M-", "M?"})
        self.assertTrue(report.memory["M-"])
        self.assertTrue(report.memory["M?"])
        if not any("MORPH_GENOME" in decision.pareto_front for decision in report.decisions):
            self.assertEqual(report.memory["M+"], ())

    def test_report_digest_is_stable_despite_latency_measurement(self):
        first = run_tournament(CORPUS)
        second = run_tournament(CORPUS)
        self.assertEqual(first.stable_digest(), second.stable_digest())

    def test_evidence_class_stays_simulated_engineering(self):
        report = run_tournament(CORPUS)
        self.assertEqual(report.evidence_class, "SIMULATED_ENGINEERING_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
