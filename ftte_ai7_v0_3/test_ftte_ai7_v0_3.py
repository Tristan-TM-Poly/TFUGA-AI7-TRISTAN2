import unittest
from ftte_ai7_v0_3 import top27, sierpinski_carpet, menger_sponge, iterate, adjacency_graph, lc_export, run_all

class TestFTTEAI7V03(unittest.TestCase):
    def test_top27_count(self):
        self.assertEqual(len(top27()), 27)

    def test_sierpinski_carpet_depth1(self):
        self.assertEqual(len(iterate(sierpinski_carpet(), 1)), 8)

    def test_menger_depth1(self):
        self.assertEqual(len(iterate(menger_sponge(), 1)), 20)

    def test_fractal_dimensions(self):
        self.assertGreater(sierpinski_carpet().theoretical_dimension, 1.8)
        self.assertGreater(menger_sponge().theoretical_dimension, 2.7)

    def test_graph_and_lc(self):
        graph = adjacency_graph(iterate(sierpinski_carpet(), 1))
        self.assertGreater(len(graph['nodes']), 0)
        self.assertGreater(lc_export(graph)['component_count'], 0)

    def test_run_all(self):
        result = run_all()
        self.assertEqual(result['status'], 'succeeded')
        self.assertFalse(result['stable_canon_allowed'])

if __name__ == '__main__':
    unittest.main()
