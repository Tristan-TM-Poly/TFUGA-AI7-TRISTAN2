import unittest

from omega_management_t.ladder import ARTIFACT_CLASSES, evaluate_ladder


class LadderTests(unittest.TestCase):
    def test_power_of_two_targets(self):
        result = evaluate_ladder(3, ARTIFACT_CLASSES[:8])
        self.assertEqual(result.target, 8)
        self.assertEqual(result.next_target, 16)
        self.assertEqual(len(result.covered), 8)
        self.assertEqual(len(result.missing), 8)

    def test_n_plus_one_full_coverage_can_be_saturation_candidate(self):
        result = evaluate_ladder(
            3,
            ARTIFACT_CLASSES,
            verified_gain_n=10.0,
            verified_gain_next=10.05,
            cost_next=10.0,
            epsilon=0.01,
        )
        self.assertEqual(result.missing, ())
        self.assertTrue(result.saturation_candidate)

    def test_missing_surface_blocks_saturation(self):
        result = evaluate_ladder(
            3,
            ARTIFACT_CLASSES[:-1],
            verified_gain_n=10.0,
            verified_gain_next=10.0,
            cost_next=1.0,
        )
        self.assertFalse(result.saturation_candidate)

    def test_bad_cost_fails_closed(self):
        with self.assertRaises(ValueError):
            evaluate_ladder(2, [], verified_gain_n=1, verified_gain_next=1, cost_next=0)


if __name__ == "__main__":
    unittest.main()
