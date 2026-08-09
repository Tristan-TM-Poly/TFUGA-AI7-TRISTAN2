import pytest

from omega_pure_math_t import (
    DimensionFunctional,
    FiniteTheory,
    HGFM,
    HypergraphLevel,
    Inference,
    ProofHypergraph,
    RepresentationGraph,
    RepresentationScore,
    ScaleMap,
    channel_dimension_conservation,
    compose_scale_maps,
    dimension_spectrum,
    expected_proof_cost,
    geometric_residual_bound,
    growth_dimension,
    log_modulus_grid,
    pareto_front,
    proof_free_energy,
    proof_partition_function,
    residual_tower,
    scale_coherence_defect,
    second_tensor_power_spectrum,
    source_density,
    symmetric_difference_distance,
    theory_intersection,
    uniformly_contracting,
)


def test_tensor_spectrum_preserves_standard_dimension_split():
    spectrum = second_tensor_power_spectrum(4)
    assert spectrum.tensor_product_dimension == 16
    assert spectrum.by_name("symmetric").dimension == 10
    assert spectrum.by_name("alternating").dimension == 6
    assert channel_dimension_conservation(spectrum)


def test_trace_channel_requires_explicit_opt_in():
    plain = second_tensor_power_spectrum(3)
    with pytest.raises(KeyError):
        plain.by_name("trace")
    metric_enriched = second_tensor_power_spectrum(3, include_trace_channel=True)
    assert metric_enriched.by_name("trace").dimension == 1


def test_representation_pareto_front_and_shortest_loss():
    scores = [
        RepresentationScore("raw", 0, 10, 0, 0, 10),
        RepresentationScore("compressed", 1, 2, 1, 1, 2),
        RepresentationScore("bad", 2, 12, 2, 2, 12),
    ]
    assert {item.name for item in pareto_front(scores)} == {"raw", "compressed"}
    graph = RepresentationGraph()
    graph.add_edge("raw", "mid", 0.2)
    graph.add_edge("mid", "compact", 0.3)
    graph.add_edge("raw", "compact", 1.0)
    assert graph.shortest_loss("raw", "compact") == pytest.approx(0.5)


def test_proof_hypergraph_closure_and_thermodynamics():
    proof = ProofHypergraph(axioms={"A", "B"})
    proof.add_inference(Inference(("A", "B"), "C", "combine", cost=2))
    proof.add_inference(Inference(("C",), "T", "finish", cost=1))
    assert proof.proves("T")
    assert proof.minimum_derivation_cost("T") == 3
    z = proof_partition_function([3, 5], beta=1)
    assert z > 0
    assert proof_free_energy([3, 5], beta=1) < 3
    assert 3 < expected_proof_cost([3, 5], beta=1) < 5


def test_residual_tower_contracts_geometrically():
    history = residual_tower(8.0, lambda r, _: 0.5 * r, steps=4)
    assert [step.next_residual for step in history] == [4.0, 2.0, 1.0, 0.5]
    assert uniformly_contracting(history)
    assert geometric_residual_bound(8, 0.5, 4) == 0.5


def test_dimension_spectrum_keeps_functionals_distinct():
    spec = dimension_spectrum(
        [[1, 0], [0, 1]],
        [
            DimensionFunctional("rows", len, "matrices"),
            DimensionFunctional("entries", lambda x: sum(len(row) for row in x), "matrices"),
        ],
    )
    assert spec.as_dict() == {"rows": 2.0, "entries": 4.0}


def test_hgfm_scale_coherence_and_growth_diagnostic():
    fine = HypergraphLevel(
        1.0,
        frozenset({"a", "b", "c", "d"}),
        frozenset({frozenset({"a", "b"}), frozenset({"c", "d"})}),
    )
    middle = HypergraphLevel(
        2.0,
        frozenset({"u", "v"}),
        frozenset({frozenset({"u", "v"})}),
    )
    coarse = HypergraphLevel(4.0, frozenset({"z"}), frozenset())
    first = ScaleMap(0, 1, (("a", "u"), ("b", "u"), ("c", "v"), ("d", "v")))
    second = ScaleMap(1, 2, (("u", "z"), ("v", "z")))
    hgfm = HGFM((fine, middle, coarse), (first, second))
    assert len(hgfm.levels) == 3
    composed = compose_scale_maps(first, second)
    assert scale_coherence_defect(composed, {k: "z" for k in "abcd"}) == 0
    assert growth_dimension([1, 2, 4], [1, 2, 4]) == pytest.approx(1.0)


def test_theory_evolution_distance_and_intersection():
    left = FiniteTheory("L", axioms=frozenset({"A", "B"}), theorems=frozenset({"T"}))
    right = left.remove_axiom("B", name="R")
    assert symmetric_difference_distance(left, right) == 1
    common = theory_intersection(left, right, name="common")
    assert common.axioms == frozenset({"A"})


def test_zero_tomography_grid_and_density_are_finite_interior():
    xs = [-1.0, -0.5, 0.0, 0.5, 1.0]
    ys = [-1.0, -0.5, 0.0, 0.5, 1.0]
    grid = log_modulus_grid(lambda z: z - 0.1, xs, ys, floor=1e-12)
    density = source_density(grid)
    assert len(density.values) == 5
    assert len(density.values[0]) == 5
    assert density.values[2][2] == density.values[2][2]
