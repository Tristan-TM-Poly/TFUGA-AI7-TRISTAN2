import unittest

from omega_axiome_tristan_t import (
    AxiomGenome, ClaimPassport, EpistemicKind, EpistemicStatus, EvidenceItem, EvidenceType, Prediction,
    compile_failure_to_mminus, discriminating_predictions, mutate_axiom, oak_audit, rank_candidates,
    regeneration_receipt,
)


class AxiomeTristanTests(unittest.TestCase):
    def passport(self, **overrides):
        data = dict(
            claim_id="AX-T-001",
            statement="A bounded modular system can preserve service under a declared single-fault model.",
            kind=EpistemicKind.ENGINEERING_PRINCIPLE,
            domain="distributed-systems",
            definitions=("service=declared critical function remains available", "single-fault=model removes one declared component"),
            scope=("single-fault", "bounded-topology"),
            assumptions=("failure independence is not presumed",),
            evidence=(EvidenceItem("E1", EvidenceType.BENCHMARK, "fixture:baseline-a", ("single-fault", "bounded-topology"), True, 0.8),),
            counterevidence=(),
            uncertainty={"model": 0.3, "sampling": 0.2},
            falsifiers=("find a declared single-fault case where service loss exceeds the baseline criterion",),
            provenance=("conversation-derived-design:R0.1",),
            status=EpistemicStatus.TESTED,
            generator_id="generator-A",
            judge_id="judge-B",
        )
        data.update(overrides)
        return ClaimPassport(**data)

    def test_valid_tested_claim_passes(self):
        report = oak_audit(self.passport())
        self.assertTrue(report.passed)
        self.assertTrue(report.promotion_eligible)

    def test_generator_judge_collision_fails(self):
        report = oak_audit(self.passport(generator_id="same", judge_id="same"))
        self.assertFalse(report.passed)
        self.assertIn("GENERATOR_NE_JUDGE", {r.gate for r in report.results if not r.passed})

    def test_simulation_cannot_be_corroborated(self):
        sim = EvidenceItem("S1", EvidenceType.SIMULATION, "sim:toy", ("single-fault", "bounded-topology"), True, 1.0)
        self.assertFalse(oak_audit(self.passport(evidence=(sim,), status=EpistemicStatus.CORROBORATED)).passed)

    def test_replicated_requires_independent_replication(self):
        rep = EvidenceItem("R1", EvidenceType.REPLICATION, "lab:self", ("single-fault", "bounded-topology"), False, 1.0)
        self.assertFalse(oak_audit(self.passport(evidence=(rep,), status=EpistemicStatus.REPLICATED)).passed)

    def test_formal_status_requires_formal_proof(self):
        self.assertFalse(oak_audit(self.passport(kind=EpistemicKind.CONJECTURE, status=EpistemicStatus.FORMALLY_VERIFIED)).passed)

    def test_scope_overflow_is_blocked(self):
        weak = EvidenceItem("E1", EvidenceType.BENCHMARK, "fixture", ("single-fault",), True, 1.0)
        failed = {r.gate for r in oak_audit(self.passport(evidence=(weak,))).results if not r.passed}
        self.assertIn("CLAIM_SCOPE_LE_EVIDENCE_SCOPE", failed)

    def test_revenue_does_not_change_epistemic_result(self):
        a = oak_audit(self.passport(revenue_score=0.0))
        b = oak_audit(self.passport(revenue_score=10_000_000.0))
        self.assertEqual(a.passed, b.passed)
        self.assertEqual([r.passed for r in a.results], [r.passed for r in b.results])

    def test_digest_is_deterministic(self):
        self.assertEqual(self.passport().digest(), self.passport().digest())

    def test_mutations_are_non_authoritative_candidates(self):
        mutations = mutate_axiom(AxiomGenome(self.passport()))
        self.assertGreaterEqual(len(mutations), 2)
        self.assertTrue(all(m.generated_candidate for m in mutations))
        self.assertTrue(all(item["authoritative"] is False for item in rank_candidates(mutations)))

    def test_discriminating_prediction_found(self):
        left = AxiomGenome(self.passport(claim_id="L"), predictions=(Prediction("LP", "latency", "decreases", "load=50%"),))
        right = AxiomGenome(self.passport(claim_id="R"), predictions=(Prediction("RP", "latency", "increases", "load=50%"),))
        found = discriminating_predictions(left, right)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["variable"], "latency")

    def test_regeneration_is_probe_relative_not_global_proof(self):
        receipt = regeneration_receipt(AxiomGenome(self.passport()))
        self.assertTrue(receipt.equivalent_relative_to_probes)
        self.assertFalse(receipt.authoritative)
        self.assertEqual(receipt.epsilon_residual, 0)

    def test_failed_gates_compile_to_negative_memory(self):
        bad = self.passport(definitions=(), generator_id="x", judge_id="x")
        report = oak_audit(bad)
        entries = compile_failure_to_mminus(bad, report)
        self.assertGreaterEqual(len(entries), 2)
        self.assertTrue(all(e.source_claim_id == bad.claim_id for e in entries))

    def test_counterevidence_blocks_strong_promotion(self):
        counter = EvidenceItem("C1", EvidenceType.EXPERIMENT, "lab:counter", ("single-fault", "bounded-topology"), True, 0.9)
        self.assertFalse(oak_audit(self.passport(counterevidence=(counter,), status=EpistemicStatus.CORROBORATED)).passed)


if __name__ == "__main__":
    unittest.main()
