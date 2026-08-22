from fractions import Fraction
import json
from pathlib import Path
import unittest

from omega_zeta_square_t import (
    EvidenceKind,
    IntervalEvidence,
    RationalInterval,
    cvcd_support_report,
    export_obligation_bundle,
    minimal_dependency_supports,
    obligations_from_proof_graph,
    validate_interval_evidence,
)


GRAPH_PATH = Path("specs/omega_zeta_square_t/proof_graph.json")


class TestIntervalProvenanceGate(unittest.TestCase):
    def test_supplied_interval_stays_conditional(self):
        item = IntervalEvidence(
            quantity="xi(1/2)",
            enclosure=RationalInterval(Fraction(49, 100), Fraction(51, 100)),
            kind=EvidenceKind.SUPPLIED,
        )
        verdict = validate_interval_evidence([item])
        self.assertTrue(verdict.admissible_for_rigorous_propagation)
        self.assertFalse(verdict.analytically_certified_inputs)
        self.assertEqual(
            verdict.promotion_cap,
            "RIGOROUS_PROPAGATION_CONDITIONAL_ON_INPUTS_ONLY",
        )
        self.assertFalse(verdict.proves_rh)

    def test_certified_source_requires_method_and_reference(self):
        item = IntervalEvidence(
            quantity="xi''(1/2)",
            enclosure=RationalInterval(Fraction(1, 10), Fraction(1, 5)),
            kind=EvidenceKind.ANALYTIC_CERTIFIED_INTERVAL,
        )
        verdict = validate_interval_evidence([item])
        self.assertFalse(verdict.admissible_for_rigorous_propagation)
        self.assertTrue(any("requires method" in error for error in verdict.errors))
        self.assertTrue(any("requires reference" in error for error in verdict.errors))

    def test_certified_bundle_is_still_finite_consequence_only(self):
        items = [
            IntervalEvidence(
                quantity="xi(1/2)",
                enclosure=RationalInterval(Fraction(49, 100), Fraction(51, 100)),
                kind=EvidenceKind.ANALYTIC_CERTIFIED_INTERVAL,
                method="validated quadrature with explicit tail bound",
                reference="proof-obligation:test-fixture",
            ),
            IntervalEvidence(
                quantity="xi''(1/2)",
                enclosure=RationalInterval(Fraction(1, 100), Fraction(2, 100)),
                kind=EvidenceKind.FORMAL_VERIFIED_INTERVAL,
                method="formal interval lemma",
                reference="proof-obligation:test-fixture-2",
            ),
        ]
        verdict = validate_interval_evidence(items)
        self.assertTrue(verdict.admissible_for_rigorous_propagation)
        self.assertTrue(verdict.analytically_certified_inputs)
        self.assertEqual(verdict.promotion_cap, "CERTIFIED_INPUTS_FINITE_CONSEQUENCES_ONLY")
        self.assertFalse(verdict.proves_rh)


class TestProofObligations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))

    def test_bundle_exposes_only_current_open_and_conjectural_work(self):
        obligations = obligations_from_proof_graph(self.graph)
        ids = {item.obligation_id for item in obligations}
        self.assertIn("obl.rh", ids)
        self.assertNotIn("obl.r7_stieltjes_rh_bridge", ids)
        self.assertNotIn("obl.off_line_finite_certificate", ids)
        self.assertIn("obl.tail_analytic_bounds", ids)
        self.assertIn("obl.analytic_xi_interval_source", ids)
        bundle = export_obligation_bundle(obligations)
        self.assertFalse(bundle["solution_claimed"])
        self.assertEqual(bundle["obligation_count"], len(obligations))
        self.assertTrue(bundle["oak"]["formal_stub_is_not_proof"])

    def test_lean_stubs_are_comments_not_fake_theorems(self):
        bundle = export_obligation_bundle(obligations_from_proof_graph(self.graph))
        self.assertTrue(all(stub.startswith("/- OAK PROOF OBLIGATION") for stub in bundle["lean_comment_stubs"]))


class TestCvcdSupportCompression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))

    def test_rh_support_is_structural_only(self):
        supports = minimal_dependency_supports(self.graph, "rh")
        self.assertTrue(supports)
        self.assertTrue(all(item.proves_target is False for item in supports))
        report = cvcd_support_report(self.graph, "rh")
        self.assertTrue(report["structural_only"])
        self.assertFalse(report["proves_target"])
        self.assertIn("criterion equivalent", report["oak"]["warning"])

    def test_non_promoting_edge_does_not_turn_finite_hankel_into_global_support(self):
        supports = minimal_dependency_supports(self.graph, "hankel_all_orders")
        leaf_sets = [set(item.leaves) for item in supports]
        self.assertFalse(any("finite_hankel" in leaves for leaves in leaf_sets))


if __name__ == "__main__":
    unittest.main()
