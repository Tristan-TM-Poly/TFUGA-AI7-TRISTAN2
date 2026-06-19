from sage_tristan.omega_pspt_geometry import (
    ascii_plot_2d,
    boundary_vertices,
    cantor_product_points,
    cantor_word,
    menger_sponge_points,
    nearest_neighbor_edges,
    sierpinski_carpet_points,
    summarize_fractal,
    summarize_graph,
)


def test_cantor_word_middle_third_counts():
    assert cantor_word(0) == [1]
    assert sum(cantor_word(1)) == 2
    assert sum(cantor_word(2)) == 4


def test_cantor_product_points_counts():
    assert len(cantor_product_points(2, dims=2)) == 16
    assert len(cantor_product_points(1, dims=3)) == 8


def test_sierpinski_carpet_counts():
    assert len(sierpinski_carpet_points(0)) == 1
    assert len(sierpinski_carpet_points(1)) == 8
    assert len(sierpinski_carpet_points(2)) == 64


def test_menger_sponge_counts():
    assert len(menger_sponge_points(0)) == 1
    assert len(menger_sponge_points(1)) == 20


def test_nearest_neighbor_edges_square_cycle():
    points = {(0, 0), (1, 0), (0, 1), (1, 1)}
    edges = nearest_neighbor_edges(points)
    summary = summarize_graph(points)
    assert len(edges) == 4
    assert summary.cycle_rank == 1
    assert summary.components == 1


def test_boundary_vertices_detects_box_boundary():
    points = {(0, 0), (1, 0), (2, 0), (1, 1)}
    assert (1, 1) in boundary_vertices(points)


def test_summarize_fractal_returns_oak_ready_invariants():
    summary = summarize_fractal("sierpinski_carpet", 1)
    assert summary.occupied_sites == 8
    assert summary.graph.vertices == 8
    assert summary.estimated_fractal_dimension is not None


def test_ascii_plot_2d_contains_occupied_cells():
    plot = ascii_plot_2d({(0, 0), (1, 1)})
    assert "#" in plot
    assert "." in plot
