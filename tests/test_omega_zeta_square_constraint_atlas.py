import unittest

from omega_zeta_square_t.constraint_atlas import build_constraint_atlas


class TestConstraintAtlas(unittest.TestCase):
    def test_size_two_atlas_has_expected_raw_and_unique_counts(self):
        atlas = build_constraint_atlas(max_size=2, shifts=(0, 1))
        self.assertEqual(atlas["raw_occurrence_count"], 8)
        self.assertEqual(atlas["unique_polynomial_count"], 6)
        self.assertEqual(atlas["duplicate_occurrence_count"], 2)
        self.assertGreater(atlas["compression_ratio"], 1.0)
        self.assertFalse(atlas["proves_rh"])
        self.assertTrue(atlas["oak"]["structural_cvcd_only"])

    def test_duplicate_p1_and_p2_constraints_are_grouped(self):
        atlas = build_constraint_atlas(max_size=2, shifts=(0, 1))
        occurrence_sets = [
            {
                (item["full_size"], item["shift"], tuple(item["indices"]))
                for item in group["occurrences"]
            }
            for group in atlas["constraints"]
        ]
        self.assertIn({(1, 0, (0,)), (2, 0, (0,))}, occurrence_sets)
        self.assertIn({(1, 1, (0,)), (2, 1, (0,))}, occurrence_sets)

    def test_every_unique_constraint_has_xi_integer_form(self):
        atlas = build_constraint_atlas(max_size=2)
        self.assertTrue(atlas["constraints"])
        for group in atlas["constraints"]:
            xi = group["xi_integer_polynomial"]
            self.assertGreaterEqual(xi["common_integer_scale"], 1)
            self.assertGreaterEqual(xi["d0_power_denominator"], 1)
            self.assertTrue(xi["terms"])

    def test_invalid_size_rejected(self):
        with self.assertRaises(ValueError):
            build_constraint_atlas(max_size=6)


if __name__ == "__main__":
    unittest.main()
