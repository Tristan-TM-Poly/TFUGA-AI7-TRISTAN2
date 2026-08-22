import unittest

from omega_propagation import (
    Edge,
    PropagationGraph,
    epistemic_inflation,
    meta_level_justified,
    stop_rule,
)


class PropagationKernelTests(unittest.TestCase):
    def test_route_objective_can_prefer_fidelity_over_short_latency(self):
        graph = PropagationGraph(
            [
                Edge("A", "B", latency=1, fidelity=0.50, risk=0.1),
                Edge("B", "D", latency=1, fidelity=1.00, risk=0.1),
                Edge("A", "C", latency=2, fidelity=0.99, risk=0.1),
                Edge("C", "D", latency=2, fidelity=0.99, risk=0.1),
            ]
        )
        receipt = graph.best_route(
            "A", "D", fidelity_weight=10.0, latency_weight=0.1, risk_weight=1.0
        )
        self.assertEqual(receipt.path, ("A", "C", "D"))
        self.assertAlmostEqual(receipt.fidelity, 0.9801, places=6)

    def test_exact_minimum_cut_on_small_graph(self):
        graph = PropagationGraph(
            [
                Edge("S", "A"),
                Edge("S", "B"),
                Edge("A", "T"),
                Edge("B", "T"),
            ]
        )
        cut = graph.minimum_edge_cut("S", {"T"})
        self.assertEqual(len(cut), 2)
        self.assertNotIn("T", graph.reachable("S", removed_edges=cut))

    def test_epistemic_inflation(self):
        self.assertAlmostEqual(epistemic_inflation(0.4, 0.8, new_evidence=0.1), 0.3)
        self.assertAlmostEqual(epistemic_inflation(0.4, 0.5, new_evidence=0.1), 0.0)

    def test_meta_depth_requires_net_verified_gain(self):
        self.assertTrue(
            meta_level_justified(
                verified_capability_gain=4,
                transfer_gain=2,
                complexity_cost=1,
                risk_cost=1,
                compute_cost=1,
            )
        )
        self.assertFalse(
            meta_level_justified(
                verified_capability_gain=1,
                complexity_cost=1,
                risk_cost=1,
            )
        )

    def test_stop_rule_is_fail_closed(self):
        decision = stop_rule(
            marginal_value=2,
            risk=3,
            risk_budget=2,
            evidence=0.9,
            evidence_minimum=0.8,
        )
        self.assertTrue(decision.stop)
        self.assertIn("risk_budget_exceeded", decision.reasons)

    def test_capacity_and_fidelity_affect_delivery(self):
        graph = PropagationGraph(
            [
                Edge("A", "B", fidelity=0.8, gain=2.0, capacity=10),
                Edge("B", "C", fidelity=0.5, gain=1.0, capacity=6),
            ]
        )
        receipt = graph.best_route("A", "C", amount=8)
        self.assertAlmostEqual(receipt.delivered, 5.0)


if __name__ == "__main__":
    unittest.main()
