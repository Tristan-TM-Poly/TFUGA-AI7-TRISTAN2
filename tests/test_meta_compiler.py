import unittest
from omega_tristan_meta.models import Claim, Evidence, Residual
from omega_tristan_meta.gates import claim_scope_gate, role_separation_gate, meta_stop_gate, persistent_structure_gate
from omega_tristan_meta.compiler import MetaCompiler
from omega_tristan_meta.mutation import invariant_mutation_probes

class MetaCompilerTests(unittest.TestCase):
    def test_claim_scope_passes_when_evidence_covers_claim(self):
        e = Evidence("E", "evidence", 0.8, "source")
        c = Claim("C", "claim", 0.6, "TESTED", ["E"])
        self.assertTrue(claim_scope_gate(c, [e]).passed)

    def test_claim_scope_fails_on_epistemic_inflation(self):
        e = Evidence("E", "evidence", 0.2, "source")
        c = Claim("C", "claim", 0.9, "TESTED", ["E"])
        self.assertFalse(claim_scope_gate(c, [e]).passed)

    def test_generator_cannot_be_judge(self):
        self.assertFalse(role_separation_gate("agent-x", "agent-x").passed)
        self.assertTrue(role_separation_gate("generator", "verifier").passed)

    def test_meta_stop(self):
        self.assertTrue(meta_stop_gate(1.0, 0.2, 0.1, 0.1).passed)
        self.assertFalse(meta_stop_gate(0.2, 0.2, 0.1, 0.0).passed)
        self.assertFalse(meta_stop_gate(9.0, 0.1, expressible_by_current_kernel=True).passed)

    def test_persistent_structure_gate(self):
        self.assertTrue(persistent_structure_gate(3, 3).passed)
        self.assertFalse(persistent_structure_gate(4, 3).passed)

    def test_reuses_canonical_residual_priority(self):
        r = Residual(
            residual_id="R",
            impact=1.0,
            uncertainty=0.8,
            dependency_centrality=0.5,
            expected_information_gain=0.9,
            downstream_leverage=2.0,
            cost=0.2,
            risk=0.1,
            complexity=0.1,
        )
        self.assertGreater(r.priority(), 0.0)

    def test_mutation_probes_detect_deliberate_breaks(self):
        self.assertTrue(all(invariant_mutation_probes().values()))

    def test_hard_promotion_gate(self):
        e = Evidence("E", "evidence", 0.8, "source")
        c = Claim("C", "claim", 0.6, "TESTED", ["E"])
        result = MetaCompiler().promotion_gate(c, [e], "generator", "verifier", 0.9, 0.2, 0.1)
        self.assertTrue(result.passed)

if __name__ == "__main__":
    unittest.main()
