import unittest

from omega_meta_hmg import (
    GeneratorGenome, MetaHMGEngine, Residual, FrozenBenchmark, VerificationStatus
)


class MetaHMGTests(unittest.TestCase):
    def setUp(self):
        self.engine = MetaHMGEngine()
        self.genome = GeneratorGenome("g", "reduce residual", ("EXP", "VERIFY", "COMPRESS"), budget=7)
        self.residuals = [Residual("r1", 8.0, 0.1), Residual("r2", 2.0, 0.2)]
        self.bench = FrozenBenchmark("r0", baseline_score=4.0, minimum_gain=0.1, max_risk=0.3, max_complexity=5.0)

    def test_residual_pressure_positive(self):
        self.assertGreater(self.engine.residualize(self.residuals), 10.0)

    def test_generation_does_not_mark_verified(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals)
        self.assertTrue(cs)
        self.assertTrue(all(c.payload["verified"] is False for c in cs))

    def test_representation_tournament(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals)
        winner, results = self.engine.tournament(cs, self.bench, self.engine.residualize(self.residuals))
        self.assertIsNotNone(winner)
        self.assertTrue(any(r.status == VerificationStatus.PASS for r in results))

    def test_generator_is_not_verifier(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals)
        winner, results = self.engine.tournament(cs, self.bench, self.engine.residualize(self.residuals))
        result = next(r for r in results if r.candidate_id == winner.candidate_id)
        cert = self.engine.certify(self.residuals, winner, result)
        self.assertNotEqual(winner.generator_id, cert.verifier_id)

    def test_fail_cannot_be_certified(self):
        strict = FrozenBenchmark("strict", baseline_score=10000)
        cs = self.engine.generate_candidates(self.genome, self.residuals)
        winner, results = self.engine.tournament(cs, strict, self.engine.residualize(self.residuals))
        self.assertIsNone(winner)
        with self.assertRaises(ValueError):
            self.engine.certify({}, cs[0], results[0])

    def test_certificate_is_hashed(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals)
        winner, results = self.engine.tournament(cs, self.bench, self.engine.residualize(self.residuals))
        result = next(r for r in results if r.candidate_id == winner.candidate_id)
        cert = self.engine.certify(self.residuals, winner, result)
        self.assertEqual(len(cert.receipt_hash), 64)

    def test_crystal_regeneration(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals)
        winner, results = self.engine.tournament(cs, self.bench, self.engine.residualize(self.residuals))
        result = next(r for r in results if r.candidate_id == winner.candidate_id)
        cert = self.engine.certify(self.residuals, winner, result)
        crystal = self.engine.distill(winner, cert)
        rebuilt = self.engine.regenerate(crystal, winner)
        self.assertEqual(rebuilt, winner)

    def test_meta_stop_rejects_meta_bloat(self):
        self.assertFalse(self.engine.meta_stop(1, 0, 0, 0, 2, 1, 1, 1))

    def test_meta_stop_accepts_net_gain(self):
        self.assertTrue(self.engine.meta_stop(5, 2, 2, 1, 1, .2, .2, .5))

    def test_negative_memory_records_total_failure(self):
        strict = FrozenBenchmark("strict", baseline_score=10000)
        cs = self.engine.generate_candidates(self.genome, self.residuals)
        self.engine.tournament(cs, strict, self.engine.residualize(self.residuals))
        self.assertEqual(len(self.engine.negative_memory), 1)


class MetaControllerTests(unittest.TestCase):
    def setUp(self):
        self.genome = GeneratorGenome("g-meta", "reduce residual", ("EXP", "VERIFY"), budget=4)
        self.residuals = [Residual("r1", 8.0, 0.1), Residual("r2", 2.0, 0.2)]

    def test_workflow_does_not_grant_external_write(self):
        from omega_meta_hmg import AuthorityEnvelope, MetaController
        wf = MetaController().compile_workflow("x", [Residual("r", 1)], AuthorityEnvelope())
        self.assertNotIn("PROPOSE_EXTERNAL_WRITE", wf.steps)

    def test_explicit_authority_can_add_write_proposal_only(self):
        from omega_meta_hmg import AuthorityEnvelope, MetaController
        a = AuthorityEnvelope(("READ", "SIMULATE", "TEST", "EXTERNAL_WRITE"), external_write=True)
        wf = MetaController().compile_workflow("x", [Residual("r", 1)], a)
        self.assertIn("PROPOSE_EXTERNAL_WRITE", wf.steps)

    def test_countergenerator_returns_competitors(self):
        from omega_meta_hmg import MetaController
        engine = MetaHMGEngine()
        c = engine.generate_candidates(self.genome, self.residuals)[0]
        self.assertEqual(len(MetaController().countergenerate(c)), 3)

    def test_unknown_unknown_question_generator_prioritizes_pressure(self):
        from omega_meta_hmg import MetaController
        qs = MetaController().generate_questions(self.residuals)
        self.assertEqual(qs[0].source_residual, "r1")

    def test_apoptosis_requires_regenerability(self):
        from omega_meta_hmg import MetaController, RegenerationDepth
        self.assertIsNone(MetaController().apoptosis("x", 0.0, False, RegenerationDepth.R2_ARTIFACT))

    def test_apoptosis_emits_forget_receipt(self):
        from omega_meta_hmg import MetaController, RegenerationDepth
        r = MetaController().apoptosis("x", 0.01, True, RegenerationDepth.R4_GENERATOR)
        self.assertIsNotNone(r)
        self.assertTrue(r.regenerable)


if __name__ == "__main__":
    unittest.main()
