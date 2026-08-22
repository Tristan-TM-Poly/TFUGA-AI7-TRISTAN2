import unittest

from omega_meta_hmg import GeneratorGenome, MetaHMGEngine, Residual, FrozenBenchmark, VerificationStatus


class MetaHMGTests(unittest.TestCase):
    def setUp(self):
        self.engine = MetaHMGEngine()
        self.genome = GeneratorGenome("g", "reduce residual", ("EXP", "VERIFY", "COMPRESS"), budget=7)
        self.residuals = [Residual("r1", 8.0, 0.1), Residual("r2", 2.0, 0.2)]
        self.bench = FrozenBenchmark("r0", 4.0, 0.1, 0.3, 5.0)

    def test_residual_pressure_positive(self): self.assertGreater(self.engine.residualize(self.residuals), 10.0)
    def test_generation_does_not_mark_verified(self): self.assertTrue(all(c.payload["verified"] is False for c in self.engine.generate_candidates(self.genome, self.residuals)))
    def test_representation_tournament(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals); w, rs = self.engine.tournament(cs, self.bench, self.engine.residualize(self.residuals)); self.assertIsNotNone(w); self.assertTrue(any(r.status == VerificationStatus.PASS for r in rs))
    def test_generator_is_not_verifier(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals); w, rs = self.engine.tournament(cs, self.bench, self.engine.residualize(self.residuals)); r = next(x for x in rs if x.candidate_id == w.candidate_id); cert = self.engine.certify(self.residuals, w, r); self.assertNotEqual(w.generator_id, cert.verifier_id)
    def test_fail_cannot_be_certified(self):
        b = FrozenBenchmark("strict", 10000); cs = self.engine.generate_candidates(self.genome, self.residuals); w, rs = self.engine.tournament(cs, b, self.engine.residualize(self.residuals)); self.assertIsNone(w); self.assertRaises(ValueError, self.engine.certify, {}, cs[0], rs[0])
    def test_certificate_is_hashed(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals); w, rs = self.engine.tournament(cs, self.bench, self.engine.residualize(self.residuals)); r = next(x for x in rs if x.candidate_id == w.candidate_id); self.assertEqual(len(self.engine.certify(self.residuals, w, r).receipt_hash), 64)
    def test_crystal_regeneration(self):
        cs = self.engine.generate_candidates(self.genome, self.residuals); w, rs = self.engine.tournament(cs, self.bench, self.engine.residualize(self.residuals)); r = next(x for x in rs if x.candidate_id == w.candidate_id); cert = self.engine.certify(self.residuals, w, r); self.assertEqual(self.engine.regenerate(self.engine.distill(w, cert), w), w)
    def test_meta_stop_rejects_meta_bloat(self): self.assertFalse(self.engine.meta_stop(1,0,0,0,2,1,1,1))
    def test_meta_stop_accepts_net_gain(self): self.assertTrue(self.engine.meta_stop(5,2,2,1,1,.2,.2,.5))
    def test_negative_memory_records_total_failure(self):
        b = FrozenBenchmark("strict", 10000); cs = self.engine.generate_candidates(self.genome, self.residuals); self.engine.tournament(cs, b, self.engine.residualize(self.residuals)); self.assertEqual(len(self.engine.negative_memory), 1)

if __name__ == "__main__": unittest.main()
