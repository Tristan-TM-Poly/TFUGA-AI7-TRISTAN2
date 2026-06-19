from sage_tristan.omega_pspt_spectral import (
    adjacency_sets,
    count_triangles,
    cvcd_spectral_features,
    gershgorin_bounds,
    inverse_participation_ratio,
    spectral_summary,
    tight_binding_matrix,
)


def test_triangle_count():
    edges = [((0,), (1,)), ((1,), (2,)), ((0,), (2,))]
    adjacency = adjacency_sets(edges)
    assert count_triangles(adjacency) == 1


def test_spectral_summary_triangle_moments():
    edges = [((0,), (1,)), ((1,), (2,)), ((0,), (2,))]
    summary = spectral_summary(edges)
    assert summary.nodes == 3
    assert summary.edges == 3
    assert summary.trace_a2 == 6
    assert summary.trace_a3 == 6


def test_tight_binding_matrix_and_bounds():
    nodes = [(0,), (1,)]
    matrix = tight_binding_matrix(nodes, [((0,), (1,))], hopping=-1.0)
    assert matrix == [[0.0, -1.0], [-1.0, 0.0]]
    low, high = gershgorin_bounds(matrix)
    assert low <= -1.0
    assert high >= 1.0


def test_inverse_participation_ratio_limits():
    localized = inverse_participation_ratio([1.0, 0.0, 0.0, 0.0])
    uniform = inverse_participation_ratio([1.0, 1.0, 1.0, 1.0])
    assert localized > uniform
    assert abs(localized - 1.0) < 1e-9


def test_cvcd_spectral_features_are_compact():
    summary = spectral_summary([((0,), (1,)), ((1,), (2,))])
    features = cvcd_spectral_features(summary)
    assert "edge_density_proxy" in features
    assert "degree_variance" in features
