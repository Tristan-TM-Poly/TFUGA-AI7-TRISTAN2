import unittest
from omega_ttm_exec_t.epistemic import Claim,EpistemicStatus,EvidenceClass,evaluate_claim
from omega_ttm_exec_t.primitives import primitive_contract

class EpistemicTests(unittest.TestCase):
    def test_external_simulation_stays_hold(self):
        d=evaluate_claim(Claim("effect","external_system",EpistemicStatus.CERTIFIED,EvidenceClass.SIMULATION,0.1,external_world=True))
        self.assertFalse(d.accepted)
        self.assertEqual(d.reason,"simulation_cannot_certify_external_world_claim")
    def test_comparison_needs_baseline(self):
        d=evaluate_claim(Claim("better","software",EpistemicStatus.COMPARED,EvidenceClass.BENCHMARK,0.2))
        self.assertFalse(d.accepted)
        self.assertEqual(d.reason,"comparison_without_declared_baseline")
    def test_primitive_reuse(self):
        self.assertEqual(primitive_contract("PROVE")["canonical_opcode"],"PROVE")
        self.assertFalse(primitive_contract("COMPRESS")["new_isa_instruction"])

if __name__=="__main__": unittest.main()
