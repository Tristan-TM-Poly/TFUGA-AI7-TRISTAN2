import unittest

from omega_capability_os_t.cross_skill_transplant import SkillContext, evaluate_capability_transplant
from omega_generative_closure_t.reprovenance_replay import FrozenSlice
from omega_metatime import (
    CapabilityDelta,
    MetaTimeEngine,
    StrategyGenome,
    StudentBaselineTwin,
    TemporalCounters,
    TemporalRegime,
    TemporalState,
    temporal_measurement_capability,
)


class MetaTimeTests(unittest.TestCase):
    def setUp(self):
        self.engine = MetaTimeEngine()

    def test_density_and_proof_bandwidth(self):
        c = TemporalCounters(
            elapsed_hours=2,
            ideas=10,
            hypotheses=6,
            formalisms=4,
            validations=4,
            mastery_units=2,
        )
        self.assertEqual(c.verified_capability_velocity(), 3.0)
        self.assertAlmostEqual(c.proof_bandwidth(), 0.25)
        self.assertGreater(c.activity_density(), c.verified_capability_velocity())

    def test_omega_density_penalizes_debt(self):
        clean = CapabilityDelta(
            elapsed_hours=1,
            verified_gain=1,
            retention=1,
            transfer=1,
            reuse=1,
            regenerability=1,
            future_option_value=1,
        )
        debt = CapabilityDelta(
            elapsed_hours=1,
            verified_gain=1,
            retention=1,
            transfer=1,
            reuse=1,
            regenerability=1,
            future_option_value=1,
            epistemic_debt=3,
        )
        self.assertGreater(clean.omega_density(), debt.omega_density())

    def test_regime_controller_prefers_compression_under_branch_overlap(self):
        state = TemporalState(
            active_branches=12,
            branch_overlap=0.9,
            proof_bandwidth=0.8,
        )
        self.assertEqual(self.engine.choose_regime(state), TemporalRegime.COMPRESS)

    def test_low_proof_bandwidth_blocks_branching(self):
        self.assertFalse(
            self.engine.should_open_branch(
                expected_verified_gain=10,
                opportunity_cost=1,
                proof_bandwidth=0.1,
                active_branches=2,
            )
        )

    def test_generator_cannot_be_its_own_judge(self):
        bad = StrategyGenome(
            strategy_id="bad",
            expected_verified_gain=100,
            expected_information_gain=100,
            transfer=1,
            regenerability=1,
            future_work_eliminated=1,
            time_cost=1,
            generator_id="same",
            verifier_id="same",
        )
        good = StrategyGenome(
            strategy_id="good",
            expected_verified_gain=2,
            expected_information_gain=1,
            transfer=1,
            regenerability=1,
            future_work_eliminated=1,
            time_cost=1,
            generator_id="g",
            verifier_id="v",
        )
        self.assertEqual(self.engine.select_strategy([bad, good]).strategy_id, "good")

    def test_student_speedup_requires_quality_noninferiority(self):
        valid = StudentBaselineTwin(
            baseline_hours=10,
            candidate_hours=4,
            baseline_retention=0.8,
            candidate_retention=0.82,
            baseline_transfer=0.7,
            candidate_transfer=0.72,
            baseline_calibration=0.75,
            candidate_calibration=0.75,
        )
        invalid = StudentBaselineTwin(
            baseline_hours=10,
            candidate_hours=2,
            baseline_retention=0.8,
            candidate_retention=0.5,
            baseline_transfer=0.7,
            candidate_transfer=0.8,
            baseline_calibration=0.75,
            candidate_calibration=0.8,
        )
        self.assertEqual(valid.validated_speedup(), 2.5)
        self.assertIsNone(invalid.validated_speedup())

    def test_meta_stop_rule(self):
        self.assertFalse(
            self.engine.should_create_meta_level(
                verified_out_of_sample_gain=100,
                complexity_cost=1,
                risk_cost=1,
                debt_cost=1,
                expressible_by_current_kernel=True,
            )
        )
        self.assertTrue(
            self.engine.should_create_meta_level(
                verified_out_of_sample_gain=5,
                complexity_cost=1,
                risk_cost=1,
                debt_cost=1,
                expressible_by_current_kernel=False,
            )
        )

    def test_crystal_is_bounded_and_deterministic(self):
        crystal = self.engine.crystallize(
            period_id="2026-08-22",
            capabilities=["a", "b", "c", "d"],
            proofs=["p1", "p2", "p3", "p4"],
            failures=["f1"],
            reusable_primitives=["r1", "r2"],
            deleted_or_absorbed=["x"],
            next_frontier="next",
            provenance=["chat"],
        )
        self.assertEqual(crystal.capabilities, ("a", "b", "c"))
        self.assertEqual(len(crystal.digest()), 64)
        self.assertEqual(crystal.digest(), crystal.digest())

    def test_regeneration_and_generator_cover(self):
        closure = self.engine.regeneration_closure(
            ["goal", "verify", "crystallize"],
            ["goal", "verify"],
        )
        self.assertAlmostEqual(closure, 2 / 3)
        cover = self.engine.minimum_generator_cover(
            {"cap": {"a", "b", "c"}},
            {
                "g1": {"a", "b"},
                "g2": {"b", "c"},
                "g3": {"c"},
            },
        )
        produced = set().union(*(
            {"g1": {"a", "b"}, "g2": {"b", "c"}, "g3": {"c"}}[g]
            for g in cover
        ))
        self.assertTrue({"a", "b", "c"} <= produced)

    def test_temporal_measurement_transplants_through_capability_os(self):
        capability = temporal_measurement_capability()
        self.assertEqual(capability.authority, "read")
        contexts = (
            SkillContext.make("temporal-analysis", "temporal-analysis", ["temporal_state", "capability_delta"], ["temporal_metrics", "temporal_regime"], "read"),
            SkillContext.make("learning-time", "learning", ["evidence"], ["residual"], "read"),
        )
        report = evaluate_capability_transplant(
            capability,
            contexts,
            frozen_slices=(
                FrozenSlice.make("temporal-analysis", ["src-time-analysis"], ["bench-time-analysis"]),
                FrozenSlice.make("learning-time", ["src-learning-time"], ["bench-learning-time"]),
            ),
            training_provenance_ids=("train-metatime",),
            runs={
                "run-a": {"temporal": "PASS", "learning": "PASS"},
                "run-b": {"temporal": "PASS", "learning": "PASS"},
            },
            historical_expected={"temporal": "PASS", "learning": "PASS"},
            historical_candidate={"temporal": "PASS", "learning": "PASS"},
            counterfactual_observations=((0.4, 0.6), (0.5, 0.7), (0.7, 0.7)),
        )
        self.assertEqual(report.decision, "PROMOTE")
        self.assertEqual(report.transfer_ratio, 1.0)
        self.assertEqual(report.blockers, ())


if __name__ == "__main__":
    unittest.main()
