import operator

from omega_pure_math_t.bracket_spectrum import (
    edge_associator_field,
    rotation_graph,
    rotation_graph_connected,
)
from omega_pure_math_t.factor_tree import factor_tree_distance, minimum_factor_tree
from omega_pure_math_t.finite_classification import (
    invariant_collisions,
    invariant_is_complete,
    minimal_complete_invariant_families,
    orbit_partition,
)
from omega_pure_math_t.logexp_adapter import generator_round_trip, near_identity_log_gate


def test_associahedron_rotation_graph_for_four_leaves_is_pentagon():
    graph = rotation_graph(4)
    assert len(graph) == 5
    assert rotation_graph_connected(4)
    assert all(len(neighbors) == 2 for neighbors in graph.values())


def test_edge_associator_field_vanishes_for_associative_addition():
    field = edge_associator_field([1, 2, 3, 4], operator.add)
    assert field
    assert max(field.values()) == 0


def test_edge_associator_field_detects_subtraction():
    field = edge_associator_field([10, 3, 2, 1], operator.sub)
    assert any(value > 0 for value in field.values())


def test_finite_orbit_invariant_completeness_for_sign_action():
    objects = {-2, -1, 0, 1, 2}
    generators = [lambda x: -x]
    parts = orbit_partition(objects, generators)
    assert {frozenset(part) for part in parts} == {
        frozenset({-2, 2}),
        frozenset({-1, 1}),
        frozenset({0}),
    }
    assert invariant_is_complete(objects, generators, abs)
    assert invariant_collisions(objects, generators, lambda x: x % 2)


def test_minimal_complete_invariant_families_exact_finite_search():
    objects = {-2, -1, 0, 1, 2}
    generators = [lambda x: -x]
    minima = minimal_complete_invariant_families(
        objects,
        generators,
        {"abs": abs, "square": lambda x: x * x, "parity": lambda x: x % 2},
    )
    assert frozenset({"abs"}) in minima
    assert frozenset({"square"}) in minima


def test_exact_factor_tree_search_minimizes_leaf_count():
    tree = minimum_factor_tree(
        "X",
        bricks={"a", "b", "c"},
        rules={
            "X": (("Y", "c"), ("a", "b", "c")),
            "Y": (("a", "b"),),
        },
    )
    assert tree is not None
    assert tree.leaf_count() == 3
    assert tree.depth() >= 1
    assert factor_tree_distance(tree, tree) == 0


def test_logexp_adapter_round_trip_and_gate():
    result = generator_round_trip(((0.0, 0.05), (-0.05, 0.0)))
    assert result.generator_error < 1e-10
    assert result.transformation_error < 1e-10
    gate = near_identity_log_gate(((2.0, 0.0), (0.0, 2.0)))
    assert not gate.admissible_for_mercator
