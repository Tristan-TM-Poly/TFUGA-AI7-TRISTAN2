import unittest

from omega_generative_closure_t.core import MaxMinVector, Rule
from omega_generative_closure_t.geometry import closure_gradient, pairwise_seed_curvature
from omega_generative_closure_t.maxmin import dominates
from omega_generative_closure_t.morphogenesis import (
    compile_morphogenesis_receipt,
    compile_residual_field,
    minimal_generating_basis,
    renormalize_seed_set,
)
from omega_meta_science_t.discovery import RepresentationRoute


class GenerativeClosureR03Tests(unittest.TestCase):
    def test_r02_gradient_and_pairwise_curvature(self):
        rules = (Rule.make("joint", ("A", "B"), ("X",)),)
        gains = closure_gradient(("A",), rules, ("B", "C"))
        self.assertEqual(gains[0].candidate, "B")
        self.assertEqual(gains[0].derived_added, frozenset({"X"}))
        curvature = pairwise_seed_curvature((), rules, "A", "B")
        self.assertEqual(curvature.curvature, 1)

    def test_extended_maxmin_axes_participate_in_dominance(self):
        stronger = MaxMinVector(
            verified_value=1.0,
            interoperability=1.0,
            synergy=1.0,
            transferability=1.0,
            risk=0.1,
        )
        weaker = MaxMinVector(
            verified_value=1.0,
            interoperability=0.0,
            synergy=0.0,
            transferability=0.0,
            risk=0.2,
        )
        self.assertTrue(dominates(stronger, weaker))

    def test_residual_field_exposes_blocked_prerequisite(self):
        rules = (
            Rule.make("derive-x", ("A",), ("X",)),
            Rule.make("derive-y", ("X", "B"), ("Y",)),
        )
        field = compile_residual_field(("A",), rules, ("Y", "Z"))
        self.assertEqual(field.missing, frozenset({"Y", "Z"}))
        self.assertIn(("derive-y", ("B",)), field.blocked_rules)
        self.assertEqual(field.unproduced, frozenset({"Z"}))

    def test_minimal_generating_basis_removes_redundant_seed(self):
        rules = (Rule.make("derive-c", ("A",), ("C",)),)
        report = minimal_generating_basis(("A", "B", "C"), rules)
        self.assertEqual(report.basis, frozenset({"A", "B"}))
        self.assertAlmostEqual(report.compression_ratio, 1.0 / 3.0)
        self.assertTrue(report.target <= report.reachable)

    def test_renormalization_is_idempotent_on_reduced_seed_universe(self):
        rules = (Rule.make("derive-c", ("A",), ("C",)),)
        receipt = renormalize_seed_set(("A", "B", "C"), rules)
        self.assertEqual(receipt.reduced_seeds, frozenset({"A", "B"}))
        self.assertFalse(receipt.lost_observables)
        self.assertTrue(receipt.stable_under_second_pass)

    def test_proof_carrying_morphogenesis_reuses_representation_arbitrage(self):
        routes = (
            RepresentationRoute("native", 10.0, 0.0, 0.0, 1.0),
            RepresentationRoute("compressed", 2.0, 1.0, 0.01, 0.99),
        )
        receipt = compile_morphogenesis_receipt(
            operator="RENORMALIZE",
            source_id="A0",
            target_id="A1",
            invariants_before=("observable:q",),
            invariants_after=("observable:q",),
            roundtrip_error=0.01,
            max_roundtrip_error=0.05,
            domain="software",
            provenance="test:R0.3",
            evidence_refs=("unit:test",),
            uncertainty=0.1,
            cost=1.0,
            risk=0.1,
            rollback="revert commit",
            representation_routes=routes,
        )
        self.assertEqual(receipt.oak_status, "PASS")
        self.assertEqual(receipt.representation.selected.route_id, "compressed")

    def test_morphogenesis_holds_on_lost_invariant_and_missing_evidence(self):
        receipt = compile_morphogenesis_receipt(
            operator="MERGE",
            source_id="A",
            target_id="B",
            invariants_before=("must-survive",),
            invariants_after=(),
            roundtrip_error=0.0,
            max_roundtrip_error=0.1,
            domain="software",
            provenance="test:R0.3",
            rollback="revert commit",
        )
        self.assertEqual(receipt.oak_status, "HOLD")
        self.assertIn("lost_invariant:must-survive", receipt.blockers)
        self.assertIn("missing_evidence_refs", receipt.blockers)


if __name__ == "__main__":
    unittest.main()
