import unittest

from omega_thesis_factory_t.core import example_seed
from omega_thesis_factory_t.monograph512 import (
    DEFAULT_BUDGET,
    PAGE_TREE_DEPTH,
    TARGET_DYADS,
    TARGET_PAGES,
    allocate_frontier,
    build_monograph_plan,
    frontier_512,
    frontier_dyads_256,
    validate_budget,
)


class TestMonograph512(unittest.TestCase):
    def setUp(self):
        self.seed = example_seed()

    def test_target_is_binary_frontier(self):
        self.assertEqual(TARGET_PAGES, 2**PAGE_TREE_DEPTH)
        self.assertEqual(len(frontier_512(self.seed)), 512)

    def test_frontier_is_256_complete_log_exp_dyads(self):
        dyads = frontier_dyads_256(self.seed)
        self.assertEqual(TARGET_DYADS, 256)
        self.assertEqual(len(dyads), 256)
        self.assertEqual(len({d.parent_id for d in dyads}), 256)
        self.assertTrue(all("/LOG9" in d.log_node_id for d in dyads))
        self.assertTrue(all("/EXP9" in d.exp_node_id for d in dyads))

    def test_budget_is_exact(self):
        validate_budget()
        self.assertEqual(sum(x.pages for x in DEFAULT_BUDGET), 512)

    def test_allocation_is_bijective(self):
        rows = allocate_frontier(self.seed)
        self.assertEqual(len(rows), 512)
        self.assertEqual({row["planned_page"] for row in rows}, set(range(1, 513)))
        self.assertEqual(len({row["page_node_id"] for row in rows}), 512)

    def test_plan_does_not_overclaim(self):
        plan = build_monograph_plan(self.seed)
        self.assertEqual(plan["dyad_count"], 256)
        self.assertTrue(plan["compiled_page_count_is_source_of_truth"])
        self.assertEqual(plan["structural_plan_status"], "PASS")
        self.assertEqual(plan["scientific_validation_status"], "NOT_IMPLIED")
        self.assertIn("page allocation is not scientific evidence", plan["oak_invariants"])
        self.assertIn("512 planning nodes are not 512 compiled PDF pages", plan["oak_invariants"])


if __name__ == "__main__":
    unittest.main()
