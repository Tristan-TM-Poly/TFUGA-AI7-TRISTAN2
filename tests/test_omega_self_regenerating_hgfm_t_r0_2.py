import unittest
from omega_self_regenerating_hgfm_t import *

class R02Tests(unittest.TestCase):
    def base(self):
        h = SelfRegeneratingHGFM()
        for nid, kind in [
            ("q","question"),("h1","claim"),("h2","claim"),
            ("e","evidence"),("r","result"),("micro","fine"),("macro","coarse")
        ]:
            h.add_node(EpistemicNode(nid, kind, nid))
        return h

    def test_causal_contract(self):
        h = self.base()
        e = CausalHyperedge(
            "c1", ("h1","e"), ("r",), "intervene",
            verifier="v", falsifier="f", evidence_refs=("ev",),
            status="verified", intervention="do(x=1)", outcome="r",
            counterfactual_ref="w0"
        )
        h.add_edge(e)
        self.assertTrue(e.causal_complete())
        self.assertEqual(h.oak2_audit()["causal_completeness_ratio"], 1.0)

    def test_experiment_multiplexing(self):
        h = self.base()
        h.add_experiment(ExperimentHyperedge(
            "exp1", ("h1","h2"), ("y",), ("base",), 0.9, 1.0, 0.1, True
        ))
        self.assertEqual(h.best_experiment().experiment_id, "exp1")
        self.assertGreater(h.best_experiment().multiplex_ratio(), 1.0)

    def test_fractal_zoom_coarsegrain(self):
        h = self.base()
        h.scale_map.add("micro", "macro")
        self.assertEqual(h.scale_map.coarse_grain({"micro"}), {"macro"})
        self.assertEqual(h.scale_map.zoom("macro"), {"micro"})

    def test_counterfactual_world_comparison(self):
        h = self.base()
        h.add_world(CounterfactualWorld("w0","do(nothing)",(),{"score":0.2}))
        h.add_world(CounterfactualWorld("w1","do(x=1)",(),{"score":0.8}))
        self.assertEqual(h.compare_worlds("score")[0][0], "w1")

    def test_m_minus_prunes_subgraph_pattern(self):
        h = self.base()
        h.m_minus.record("bad motif","det","avoid","transfer",("h1","badop"))
        with self.assertRaises(ValueError):
            h.add_edge(HyperedgeContract("bad",("h1",),("r",),"badop"))

    def test_kernel_regenerates_causal_edge(self):
        h = self.base()
        e = CausalHyperedge(
            "c1", ("h1","e"), ("r",), "intervene",
            verifier="v", falsifier="f", evidence_refs=("ev",),
            status="verified", intervention="do(x=1)", outcome="r",
            counterfactual_ref="w0"
        )
        h.add_edge(e)
        k = h.compress_to_kernel()
        h2 = SelfRegeneratingHGFM.regenerate_from_kernel(k)
        self.assertIsInstance(h2.edges["c1"], CausalHyperedge)

if __name__ == "__main__":
    unittest.main()
