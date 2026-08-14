import unittest
from omega_self_regenerating_hgfm_t import EpistemicNode, HyperedgeContract, SelfRegeneratingHGFM, RegenerationBench

class HGFMTests(unittest.TestCase):
    def build(self):
        h = SelfRegeneratingHGFM()
        for nid, kind in [("q","question"),("h","hypothesis"),("e","evidence"),("r","result")]:
            h.add_node(EpistemicNode(nid, kind, nid))
        h.add_edge(HyperedgeContract(
            "edge1", ("q","h","e"), ("r",), "test",
            verifier="pytest", falsifier="baseline beats candidate",
            evidence_refs=("evidence://demo",), uncertainty=0.1, status="verified"
        ))
        return h

    def test_evidence_cone(self):
        h = self.build()
        self.assertEqual(h.evidence_cone("r"), {"q","h","e","r"})

    def test_kernel_regeneration(self):
        h = self.build()
        h2 = SelfRegeneratingHGFM.regenerate_from_kernel(h.compress_to_kernel())
        self.assertEqual(set(h2.nodes), {"q","h","e","r"})
        self.assertEqual(len(h2.verified_edges()), 1)

    def test_regeneration_bench(self):
        b = RegenerationBench({"cap-a","cap-b","cap-c"})
        self.assertAlmostEqual(b.score({"cap-a","cap-c"}), 2/3)

    def test_growth_prefers_information_gain_per_cost(self):
        h = self.build()
        ranked = h.propose_growth([
            {"id":"slow","residual":1,"information_gain":1,"transferability":0,"cost":10,"risk":0,"debt":0},
            {"id":"fast","residual":1,"information_gain":1,"transferability":0,"cost":1,"risk":0,"debt":0},
        ])
        self.assertEqual(ranked[0]["candidate"]["id"], "fast")

    def test_oak2_reports_proof_carrying_ratio(self):
        h = self.build()
        report = h.oak2_audit()
        self.assertEqual(report["verified_edges"], 1)
        self.assertEqual(report["proof_carrying_ratio"], 1.0)

if __name__ == "__main__":
    unittest.main()
