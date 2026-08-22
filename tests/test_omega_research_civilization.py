import unittest

from omega_morphogenesis import EpistemicStatus, Residual
from omega_research_civilization import (
    ClaimRecord,
    CompilationPolicy,
    ResearchCivilizationKernel,
    ResearchUnitKind,
)


class ResearchCivilizationKernelTests(unittest.TestCase):
    def setUp(self):
        self.kernel = ResearchCivilizationKernel()

    def test_compile_is_deterministic_and_minimal_by_default(self):
        first = self.kernel.compile("How do we discriminate model A from model B?")
        second = self.kernel.compile("How do we discriminate model A from model B?")
        self.assertEqual(first.digest(), second.digest())
        self.assertEqual(len(first.materialized_units()), 3)
        self.assertEqual(
            {unit.role for unit in first.materialized_units()},
            {"generator", "falsifier", "verifier"},
        )

    def test_residual_adds_solver_without_forcing_university(self):
        residual = Residual("r1", 1, 1, 1, 1, downstream_leverage=1)
        plan = self.kernel.compile("Resolve r1", [residual])
        kinds = {unit.kind for unit in plan.materialized_units()}
        self.assertIn(ResearchUnitKind.AIT, kinds)
        self.assertNotIn(ResearchUnitKind.UNIVERSITY, kinds)

    def test_meta_depth_gate_prevents_unbounded_recursion(self):
        policy = CompilationPolicy(max_depth=1, minimum_spawn_margin=0.1)
        self.assertFalse(
            self.kernel.should_spawn_subcivilization(
                expected_verified_gain=100,
                complexity_rent=0,
                compute_cost=0,
                depth=1,
                policy=policy,
            )
        )
        self.assertFalse(
            self.kernel.should_spawn_subcivilization(
                expected_verified_gain=0.2,
                complexity_rent=0.1,
                compute_cost=0.1,
                depth=0,
                policy=policy,
            )
        )

    def test_high_complexity_creates_lazy_candidates_not_infinite_tree(self):
        plan = self.kernel.compile("Hard coupled problem", complexity_signal=0.95)
        self.assertLessEqual(len(plan.materialized_units()), plan.policy.max_materialized_units)
        self.assertGreaterEqual(len(plan.potential_units()), 1)
        self.assertTrue(all(unit.depth <= plan.policy.max_depth for unit in plan.units))

    def test_generator_falsifier_verifier_must_be_distinct(self):
        claim = ClaimRecord(
            "c1",
            "candidate claim",
            producer_id="same",
            falsifier_id="critic",
            verifier_id="same",
            output_status=EpistemicStatus.OBSERVED,
            evidence_status=EpistemicStatus.OBSERVED,
            provenance=("measurement:1",),
            tests=("test:1",),
        )
        decision = self.kernel.judge_claim(claim)
        self.assertFalse(decision.accepted)
        self.assertFalse(decision.verified)

    def test_simulation_is_not_verified_reality_evidence(self):
        claim = ClaimRecord(
            "c2",
            "simulation supports mechanism",
            producer_id="generator",
            falsifier_id="falsifier",
            verifier_id="verifier",
            output_status=EpistemicStatus.SIMULATED,
            evidence_status=EpistemicStatus.SIMULATED,
            provenance=("sim:hash",),
            tests=("seed-replay",),
        )
        decision = self.kernel.judge_claim(claim)
        self.assertTrue(decision.accepted)
        self.assertFalse(decision.verified)

    def test_observed_independent_claim_can_be_verified(self):
        claim = ClaimRecord(
            "c3",
            "instrument response observed",
            producer_id="generator",
            falsifier_id="falsifier",
            verifier_id="verifier",
            output_status=EpistemicStatus.OBSERVED,
            evidence_status=EpistemicStatus.OBSERVED,
            provenance=("dataset:sha256:abc",),
            tests=("replicate-protocol",),
        )
        decision = self.kernel.judge_claim(claim)
        self.assertTrue(decision.accepted)
        self.assertTrue(decision.verified)

    def test_epistemic_inflation_is_rejected(self):
        claim = ClaimRecord(
            "c4",
            "claim overpromoted",
            producer_id="generator",
            falsifier_id="falsifier",
            verifier_id="verifier",
            output_status=EpistemicStatus.OBSERVED,
            evidence_status=EpistemicStatus.SIMULATED,
            provenance=("sim:hash",),
            tests=("sim-test",),
        )
        self.assertFalse(self.kernel.judge_claim(claim).accepted)

    def test_prune_keeps_irreducible_scientific_control_roles(self):
        residual = Residual("r1", 1, 1, 1, 1)
        plan = self.kernel.compile("Resolve r1", [residual])
        pruned = self.kernel.prune(plan, {"ait-solver": -1.0})
        roles = {unit.role for unit in pruned.units}
        self.assertTrue({"generator", "falsifier", "verifier"}.issubset(roles))
        self.assertNotIn("ait-solver", {unit.unit_id for unit in pruned.units})

    def test_distill_and_regenerate_closes_materialized_structure(self):
        plan = self.kernel.compile("Round trip")
        claim = ClaimRecord(
            "verified-1",
            "observed result",
            producer_id="vt-generator",
            falsifier_id="vt-falsifier",
            verifier_id="independent-verifier",
            output_status=EpistemicStatus.OBSERVED,
            evidence_status=EpistemicStatus.OBSERVED,
            provenance=("dataset:1",),
            tests=("protocol:1",),
        )
        seed = self.kernel.distill(plan, [claim])
        rebuilt = self.kernel.regenerate(seed)
        self.assertEqual(self.kernel.regeneration_closure(plan, rebuilt), 1.0)
        self.assertEqual(len(seed.verified_claims), 1)
        self.assertEqual(plan.question, rebuilt.question)

    def test_unverified_claim_is_not_persisted_in_seed(self):
        plan = self.kernel.compile("Simulation-only")
        claim = ClaimRecord(
            "sim-1",
            "simulated result",
            producer_id="vt-generator",
            falsifier_id="vt-falsifier",
            verifier_id="independent-verifier",
            output_status=EpistemicStatus.SIMULATED,
            evidence_status=EpistemicStatus.SIMULATED,
            provenance=("simulation:1",),
            tests=("replay",),
        )
        seed = self.kernel.distill(plan, [claim])
        self.assertEqual(seed.verified_claims, ())

    def test_low_value_residual_keeps_solver_lazy(self):
        residual = Residual("low", 0.01, 0.01, 0.01, 0.01)
        plan = self.kernel.compile("Low value residual", [residual])
        solver = next(unit for unit in plan.units if unit.unit_id == "ait-solver")
        self.assertFalse(solver.materialized)

    def test_lazy_candidates_are_excluded_from_book0(self):
        plan = self.kernel.compile("Hard coupled problem", complexity_signal=0.95)
        seed = self.kernel.distill(plan, [])
        seed_ids = {item[0] for item in seed.unit_blueprints}
        self.assertNotIn("virtual-university-1", seed_ids)
        self.assertNotIn("simulation-lab-1", seed_ids)

    def test_verified_claim_receipt_preserves_independent_roles_and_tests(self):
        plan = self.kernel.compile("Audit claim")
        claim = ClaimRecord(
            "receipt-1",
            "observed claim",
            producer_id="vt-generator",
            falsifier_id="vt-falsifier",
            verifier_id="independent-verifier",
            output_status=EpistemicStatus.OBSERVED,
            evidence_status=EpistemicStatus.OBSERVED,
            provenance=("dataset:receipt",),
            tests=("protocol:receipt",),
        )
        receipt = self.kernel.distill(plan, [claim]).verified_claims[0]
        self.assertEqual(receipt[4:7], ("vt-generator", "vt-falsifier", "independent-verifier"))
        self.assertEqual(receipt[7], ("dataset:receipt",))
        self.assertEqual(receipt[8], ("protocol:receipt",))

    def test_regenerate_rejects_missing_control_role(self):
        plan = self.kernel.compile("Mutation test")
        seed = self.kernel.distill(plan, [])
        mutated = seed.__class__(
            question=seed.question,
            residual_ids=seed.residual_ids,
            unit_blueprints=tuple(b for b in seed.unit_blueprints if b[2] != "verifier"),
            verified_claims=seed.verified_claims,
            policy=seed.policy,
            source_plan_hash=seed.source_plan_hash,
            version=seed.version,
        )
        with self.assertRaises(ValueError):
            self.kernel.regenerate(mutated)

    def test_regenerate_rejects_missing_parent(self):
        plan = self.kernel.compile("Parent test")
        seed = self.kernel.distill(plan, [])
        child = (
            "child",
            ResearchUnitKind.AIT.value,
            "solver",
            1,
            ("solve",),
            "missing-parent",
        )
        mutated = seed.__class__(
            question=seed.question,
            residual_ids=seed.residual_ids,
            unit_blueprints=seed.unit_blueprints + (child,),
            verified_claims=seed.verified_claims,
            policy=seed.policy,
            source_plan_hash=seed.source_plan_hash,
            version=seed.version,
        )
        with self.assertRaises(ValueError):
            self.kernel.regenerate(mutated)

    def test_regenerate_rejects_depth_above_policy(self):
        policy = CompilationPolicy(max_depth=0)
        plan = self.kernel.compile("Depth seed", policy=policy)
        seed = self.kernel.distill(plan, [])
        mutated_blueprints = list(seed.unit_blueprints)
        first = list(mutated_blueprints[0])
        first[3] = 1
        mutated_blueprints[0] = tuple(first)
        mutated = seed.__class__(
            question=seed.question,
            residual_ids=seed.residual_ids,
            unit_blueprints=tuple(mutated_blueprints),
            verified_claims=seed.verified_claims,
            policy=seed.policy,
            source_plan_hash=seed.source_plan_hash,
            version=seed.version,
        )
        with self.assertRaises(ValueError):
            self.kernel.regenerate(mutated)


if __name__ == "__main__":
    unittest.main()
