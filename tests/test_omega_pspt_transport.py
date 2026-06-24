from sage_tristan.omega_pspt_geometry import nearest_neighbor_edges
from sage_tristan.omega_pspt_transport import (
    boundary_terminals,
    effective_resistance,
    normalized_conductance_score,
    summarize_transport,
    terminal_supernode_edges,
)


def test_effective_resistance_single_edge():
    edges = [((0,), (1,))]
    assert abs(effective_resistance(edges, (0,), (1,)) - 1.0) < 1e-9


def test_effective_resistance_two_parallel_paths():
    edges = [((0,), (1,)), ((0,), (2,)), ((2,), (1,))]
    resistance = effective_resistance(edges, (0,), (1,))
    assert resistance < 1.0


def test_boundary_terminals_for_square():
    points = {(0, 0), (1, 0), (0, 1), (1, 1)}
    left, right = boundary_terminals(points, axis=0)
    assert len(left) == 2
    assert len(right) == 2


def test_terminal_supernodes_make_network_solvable():
    points = {(0, 0), (1, 0), (0, 1), (1, 1)}
    edges = nearest_neighbor_edges(points)
    augmented, source, sink = terminal_supernode_edges(points, edges, axis=0)
    assert source != sink
    assert len(augmented) > len(edges)


def test_summarize_transport_square_has_positive_conductance():
    points = {(0, 0), (1, 0), (0, 1), (1, 1)}
    edges = nearest_neighbor_edges(points)
    summary = summarize_transport(points, edges, axis=0)
    assert summary.effective_resistance > 0
    assert summary.effective_conductance > 0


def test_normalized_conductance_score_positive():
    points = {(0, 0), (1, 0), (0, 1), (1, 1)}
    edges = nearest_neighbor_edges(points)
    summary = summarize_transport(points, edges, axis=0)
    score = normalized_conductance_score(summary, occupied_sites=4, bounding_size=4)
    assert score > 0
