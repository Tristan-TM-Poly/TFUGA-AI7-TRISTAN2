import unittest

from omega_morphogenesis import (
    AuthorityEnvelope,
    CapabilityCrystal,
    EpistemicStatus,
    MorphogenesisKernel,
    ProofCarryingTransformation,
    Residual,
    TransformationMetrics,
)


class OmegaMorphogenesisTests(unittest.TestCase):
    def setUp(self):
        self.kernel = MorphogenesisKernel()

    def valid_tx(self, **overrides):
        data = dict(
            transformation_id="tx-1",
            before_hash="before",
            after_hash="after",
            generator_id="generator-a",
            verifier_id="verifier-b",
            action="test",
            authority=AuthorityEnvelope.from_actions("test"),
            input_status=EpistemicStatus.HYPOTHESIS,
            output_status=EpistemicStatus.SIMULATED,
            evidence_status=EpistemicStatus.SIMULATED,
            provenance=("source:unit-test",),
            tests=("test:unit",),
            risk_score=0.1,
            metrics=TransformationMetrics(
                verified_gain=2,
                information_gain=1,
                transfer=1,
                regenerability=1,
                optionality=1,
                future_work_eliminated=2,
                complexity=0.2,
                risk=0.1,
                complexity_rent=0.5,
            ),
        )
        data.update(overrides)
        return ProofCarryingTransformation(**data)

    def test_valid_transformation_passes(self):
        decision = self.kernel.validate(self.valid_tx())
        self.assertTrue(decision.accepted)
        self.assertTrue(decision.persist)

    def test_generator_cannot_be_its_own_judge(self):
        decision = self.kernel.validate(self.valid_tx(verifier_id="generator-a"))
        self.assertFalse(decision.accepted)
        self.assertTrue(any("Generator != Judge" in r for r in decision.reasons))

    def test_epistemic_inflation_fails_closed(self):
        decision = self.kernel.validate(
            self.valid_tx(
                output_status=EpistemicStatus.OBSERVED,
                evidence_status=EpistemicStatus.SIMULATED,
            )
        )
        self.assertFalse(decision.accepted)
        self.assertTrue(any("epistemic inflation" in r for r in decision.reasons))

    def test_authority_is_not_capability(self):
        decision = self.kernel.validate(
            self.valid_tx(
                action="publish",
                authority=AuthorityEnvelope.from_actions("test", "propose"),
            )
        )
        self.assertFalse(decision.accepted)
        self.assertTrue(any("authority" in r for r in decision.reasons))

    def test_high_risk_mutation_requires_rollback_or_compensation(self):
        decision = self.kernel.validate(
            self.valid_tx(
                action="write",
                authority=AuthorityEnvelope.from_actions("write"),
                risk_score=0.9,
                rollback=None,
                compensation=None,
            )
        )
        self.assertFalse(decision.accepted)
        self.assertTrue(any("rollback or compensation" in r for r in decision.reasons))

    def test_do_nothing_baseline_can_win(self):
        weak = self.valid_tx(
            metrics=TransformationMetrics(
                verified_gain=0.1,
                information_gain=0.1,
                transfer=0.1,
                regenerability=0.1,
                optionality=0.1,
                complexity=5,
                risk=2,
            )
        )
        self.assertIsNone(self.kernel.select_candidate([weak], baseline_utility=1.0))

    def test_residual_ranking_rewards_information_and_leverage(self):
        low = Residual("low", 1, 1, 1, 1, cost=2)
        high = Residual("high", 2, 1, 1, 2, downstream_leverage=2, cost=1)
        ranked = self.kernel.rank_residuals([low, high])
        self.assertEqual(ranked[0].residual_id, "high")

    def test_meta_stop_blocks_redundant_meta_level(self):
        self.assertFalse(self.kernel.should_create_meta_level(100, 1, True))
        self.assertFalse(self.kernel.should_create_meta_level(1, 2, False))
        self.assertTrue(self.kernel.should_create_meta_level(3, 2, False))

    def test_regeneration_closure(self):
        score = self.kernel.regeneration_closure({"kernel", "tests", "schema"}, {"kernel", "tests"})
        self.assertAlmostEqual(score, 2 / 3)

    def test_blast_radius_is_transitive(self):
        graph = {"claim-a": ["sim-b", "doc-c"], "sim-b": ["product-d"]}
        self.assertEqual(
            self.kernel.evidence_dependency_blast_radius(graph, "claim-a"),
            ("doc-c", "product-d", "sim-b"),
        )

    def test_capability_crystal_digest_is_deterministic(self):
        crystal = CapabilityCrystal(
            name="verify-claim",
            contract="verify one claim",
            inputs=("claim",),
            outputs=("receipt",),
            generator="omega",
            evidence=("benchmark",),
            tests=("unit",),
        )
        self.assertEqual(crystal.digest(), crystal.digest())
        self.assertEqual(len(crystal.digest()), 64)


if __name__ == "__main__":
    unittest.main()
