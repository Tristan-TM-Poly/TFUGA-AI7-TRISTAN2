import unittest

from omega_thesis_factory_t.core import example_seed
from omega_thesis_factory_t.monograph512 import TARGET_PAGES, PAGE_TREE_DEPTH, build_monograph_plan


class TestOmegaSkillgenThesis512(unittest.TestCase):
    def test_512_monograph_contract(self):
        plan = build_monograph_plan(example_seed())
        self.assertEqual(TARGET_PAGES, 512)
        self.assertEqual(PAGE_TREE_DEPTH, 9)
        self.assertEqual(plan["target_pages"], 512)
        self.assertEqual(len(plan["allocation"]), 512)
        self.assertEqual(plan["scientific_validation_status"], "NOT_IMPLIED")
        self.assertTrue(plan["compiled_page_count_is_source_of_truth"])


if __name__ == "__main__":
    unittest.main()
