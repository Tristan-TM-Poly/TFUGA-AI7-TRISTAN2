import unittest
from omega_intent_t.models import WorkUnit
from omega_cognitive_computer_t import CognitiveComputer
from omega_ttm_exec_t.compile import compile_report
from omega_ttm_exec_t.execute import execute_report
from omega_ttm_exec_t.epistemic import Claim,EpistemicStatus,EvidenceClass

class IntegrationTests(unittest.TestCase):
    def wu(self):
        return WorkUnit("WU-TTM-EXEC-TEST","software","Produce and validate an artifact",("REQ-1",),(),("artifact.json",),("unit_test",),"python")
    @staticmethod
    def resolver(cap,inputs):
        return {t:{"producer":cap.capability_id} for t in cap.produces}
    def test_compile_reuses_canonical_layers(self):
        r=compile_report(CognitiveComputer.default(),self.wu())
        self.assertEqual(r["capability_plan"]["status"],"READY")
        self.assertEqual(r["reuse_contract"]["workunit"],"omega_intent_t.models.WorkUnit")
        self.assertFalse(r["reuse_contract"]["parallel_cognitive_isa_created"])
    def test_fresh_complete_receipt_passes_structural_gate(self):
        r=execute_report(CognitiveComputer.default(),self.wu(),resolver=self.resolver,candidate_sha="abc",evidence_sha="abc",claims=(Claim("artifact completed","software",EpistemicStatus.TESTED,EvidenceClass.SOFTWARE_TEST,0.2),),compile_report_fn=compile_report)
        self.assertEqual(r["execution"]["execution_status"],"COMPLETE")
        self.assertEqual(r["oak"]["status"],"PASS")
        self.assertTrue(any(x.get("memory")=="M+" for x in r["memory"]))
    def test_missing_freshness_holds(self):
        r=execute_report(CognitiveComputer.default(),self.wu(),resolver=self.resolver,compile_report_fn=compile_report)
        self.assertEqual(r["oak"]["status"],"HOLD")
        self.assertTrue(any(x.get("kind")=="freshness_hold" for x in r["memory"]))

if __name__=="__main__": unittest.main()
