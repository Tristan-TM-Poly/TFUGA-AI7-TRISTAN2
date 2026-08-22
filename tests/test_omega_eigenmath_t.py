import unittest

from omega_eigenmath_t import (
    AttackEngine,
    FormalizationReceipt,
    MathClaimStatus,
    MathematicalResidual,
    MetaImprovementReceipt,
    NoveltyStatus,
    ProblemGenome,
    ProofCourt,
    ProofDebtLedger,
    ProofObligation,
    RegenerationEngine,
    ResidualEngine,
    millennium_problem_genomes,
)
from omega_eigenmath_t.bench import EigenMathBenchR01


class EigenMathTests(unittest.TestCase):
    def setUp(self):
        self.problem = ProblemGenome("toy", "Toy", "P implies P")
        self.formalization = FormalizationReceipt(
            "human", "formal", "toy-kernel", "translator", "reviewer", ("scope", "assumptions"), ()
        )
        self.good = ProofObligation(
            obligation_id="proof-1",
            problem_id="toy",
            statement="P -> P",
            assumptions=(),
            dependencies=(),
            status=MathClaimStatus.INDEPENDENTLY_VERIFIED,
            producer_id="producer",
            verifier_id="verifier",
            falsifier_id="falsifier",
            provenance=("fixture",),
            tests=("replay",),
            proof_artifact="lambda p: p",
            formalization=self.formalization,
            independent_replay=("independent-replay",),
            novelty_status=NoveltyStatus.REPRODUCED,
        )

    def test_positive_claim_promotes(self):
        decision = ProofCourt().judge(self.problem, self.good)
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.final_status, MathClaimStatus.INDEPENDENTLY_VERIFIED)

    def test_generator_cannot_be_judge(self):
        claim = self.good.__class__(**{**self.good.__dict__, "verifier_id": "producer"})
        self.assertFalse(ProofCourt().judge(self.problem, claim).accepted)

    def test_formalization_requires_independent_review(self):
        receipt = self.formalization.__class__(**{**self.formalization.__dict__, "reviewer_id": "translator"})
        claim = self.good.__class__(**{**self.good.__dict__, "formalization": receipt})
        self.assertFalse(ProofCourt().judge(self.problem, claim).accepted)

    def test_formal_claim_requires_proof_artifact(self):
        claim = self.good.__class__(**{**self.good.__dict__, "proof_artifact": None})
        self.assertFalse(ProofCourt().judge(self.problem, claim).accepted)

    def test_independent_verification_requires_replay(self):
        claim = self.good.__class__(**{**self.good.__dict__, "independent_replay": ()})
        self.assertFalse(ProofCourt().judge(self.problem, claim).accepted)

    def test_millennium_bosses_are_locked(self):
        bosses = millennium_problem_genomes()
        self.assertEqual(len(bosses), 6)
        rh = [p for p in bosses if p.problem_id == "riemann"][0]
        claim = self.good.__class__(**{**self.good.__dict__, "problem_id": "riemann"})
        decision = ProofCourt().judge(rh, claim)
        self.assertFalse(decision.accepted)
        self.assertIn("BOSS_LOCKED_UNPROVEN", " ".join(decision.reasons))

    def test_attack_engine_detects_direct_circularity(self):
        claim = self.good.__class__(**{**self.good.__dict__, "dependencies": ("proof-1",)})
        patterns = {f.pattern for f in AttackEngine().attack(claim)}
        self.assertIn("direct_circularity", patterns)

    def test_residual_ranking_rewards_information_and_reduction(self):
        weak = MathematicalResidual("weak", "w", 0.2, 0.2, 1.0, 1.0)
        strong = MathematicalResidual("strong", "s", 1.0, 1.0, 1.0, 1.0, cost=0.2)
        self.assertEqual(ResidualEngine.rank([weak, strong])[0].residual_id, "strong")

    def test_proof_debt_switches_mode(self):
        ledger = ProofDebtLedger(10, 2, hidden_assumptions=1, unreplayed_proofs=1)
        self.assertEqual(ledger.mode(5), "VERIFY_ATTACK_COMPRESS")

    def test_meta_level_must_pay_rent(self):
        good = MetaImprovementReceipt("m1", 1.0, 0.2, 0.1, 0.1, False, ("holdout",), "g", "j")
        bad = MetaImprovementReceipt("m2", 0.3, 0.2, 0.1, 0.1, False, ("holdout",), "g", "j")
        self.assertTrue(good.promote_meta_level())
        self.assertFalse(bad.promote_meta_level())

    def test_meta_generator_cannot_judge_itself(self):
        receipt = MetaImprovementReceipt("m", 5.0, 0.1, 0.1, 0.1, False, ("holdout",), "same", "same")
        self.assertFalse(receipt.promote_meta_level())

    def test_independently_verified_claim_crystallizes(self):
        crystal = ProofCourt().crystallize(self.problem, self.good)
        self.assertIsNotNone(crystal)
        self.assertEqual(len(crystal.digest()), 64)

    def test_regeneration_closure(self):
        proof = ProofCourt().crystallize(self.problem, self.good)
        seed = RegenerationEngine.distill([proof], [])
        self.assertEqual(RegenerationEngine.closure(seed.proof_crystal_digests, seed.proof_crystal_digests), 1.0)

    def test_benchmark_all_passes(self):
        self.assertTrue(EigenMathBenchR01().all_pass())


if __name__ == "__main__":
    unittest.main()
