import unittest

from minimum_sufficient_basis import (
    Component,
    find_minimum_sufficient_basis,
    necessity_by_ablation,
)


class MinimumSufficientBasisTests(unittest.TestCase):
    def test_exact_minimum_cardinality_then_cost(self) -> None:
        components = [
            Component("a", frozenset({"x", "y"}), 3.0),
            Component("b", frozenset({"x"}), 1.0),
            Component("c", frozenset({"y"}), 1.0),
            Component("d", frozenset({"z"}), 1.0),
            Component("e", frozenset({"z"}), 2.0),
        ]
        result = find_minimum_sufficient_basis(components, {"x", "y", "z"})
        self.assertEqual(result.components, ("a", "d"))
        self.assertEqual(result.total_cost, 4.0)

    def test_tie_breaks_by_lower_cost(self) -> None:
        components = [
            Component("expensive", frozenset({"x", "y"}), 5.0),
            Component("cheap", frozenset({"x", "y"}), 1.0),
        ]
        result = find_minimum_sufficient_basis(components, {"x", "y"})
        self.assertEqual(result.components, ("cheap",))

    def test_ablation_exposes_local_necessity(self) -> None:
        selected = [
            Component("observe", frozenset({"measure", "trace"})),
            Component("verify", frozenset({"proof", "trace"})),
            Component("regenerate", frozenset({"restore", "trace"})),
        ]
        losses = necessity_by_ablation(selected, {"measure", "proof", "restore"})
        self.assertEqual(losses["observe"], frozenset({"measure"}))
        self.assertEqual(losses["verify"], frozenset({"proof"}))
        self.assertEqual(losses["regenerate"], frozenset({"restore"}))

    def test_redundant_component_has_empty_local_loss(self) -> None:
        selected = [
            Component("primary", frozenset({"x"})),
            Component("redundant", frozenset({"x"})),
        ]
        losses = necessity_by_ablation(selected, {"x"})
        self.assertEqual(losses["primary"], frozenset())
        self.assertEqual(losses["redundant"], frozenset())

    def test_unreachable_requirement_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unreachable"):
            find_minimum_sufficient_basis(
                [Component("a", frozenset({"x"}))],
                {"x", "missing"},
            )

    def test_exact_solver_refuses_oversized_instance(self) -> None:
        components = [Component(str(i), frozenset({str(i)})) for i in range(3)]
        with self.assertRaisesRegex(ValueError, "refuses"):
            find_minimum_sufficient_basis(components, {"0"}, max_components=2)


if __name__ == "__main__":
    unittest.main()
