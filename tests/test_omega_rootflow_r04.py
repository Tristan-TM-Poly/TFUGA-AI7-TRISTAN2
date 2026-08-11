import json

import numpy as np

from omega_rootflow_t import (
    build_spectral_hgfm,
    canonical_puiseux_fit,
    compose_permutations,
    cubic_degree_collapse_path,
    generate_monodromy_group,
    inverse_permutation,
    permutation_cycles,
    track_projective_path,
)
from omega_rootflow_t.cli import main


def test_projective_degree_flow_tracks_one_branch_to_infinity() -> None:
    path = cubic_degree_collapse_path(33)
    result = track_projective_path(path)
    assert result.status == "OAK_PASS_PROJECTIVE_DEGREE_FLOW"
    assert result.degree_transition_count == 1
    assert result.steps[0].infinity_multiplicity == 0
    assert result.steps[-1].infinity_multiplicity == 1
    assert sum(root.at_infinity for root in result.final_roots) == 1
    finite = sorted(root.affine.real for root in result.final_roots if root.affine is not None)
    assert np.allclose(finite, [-1.0, 1.0], atol=1e-10)
    assert result.steps[-1].maximum_homogeneous_residual < 1e-10
    assert result.theorem_claimed is False


def test_projective_flow_compactifies_large_affine_root() -> None:
    path = cubic_degree_collapse_path(65)
    result = track_projective_path(path)
    assert 0.0 < result.maximum_branch_step < 1.0
    assert result.final_roots[-1].at_infinity or any(root.at_infinity for root in result.final_roots)


def test_canonical_puiseux_double_and_triple_collision_exponents() -> None:
    double = canonical_puiseux_fit(2)
    triple = canonical_puiseux_fit(3)
    assert np.isclose(double.exponent, 0.5, atol=2e-8)
    assert np.isclose(triple.exponent, 1.0 / 3.0, atol=2e-8)
    assert double.inferred_reciprocal_integer == 2
    assert triple.inferred_reciprocal_integer == 3
    assert double.r_squared > 0.999999
    assert triple.r_squared > 0.999999
    assert double.theorem_claimed is False


def test_permutation_primitives_are_consistent() -> None:
    p = (1, 0, 2)
    q = (0, 2, 1)
    assert compose_permutations(p, inverse_permutation(p)) == (0, 1, 2)
    assert permutation_cycles(p) == ((0, 1),)
    assert compose_permutations(p, q) != compose_permutations(q, p)


def test_two_transpositions_generate_s3() -> None:
    group = generate_monodromy_group([(1, 0, 2), (0, 2, 1)])
    assert group.degree == 3
    assert group.order == 6
    assert group.transitive
    assert group.orbit_of_zero == (0, 1, 2)
    assert group.status == "OAK_PASS_MONODROMY_GROUP_CLOSURE"
    assert group.theorem_claimed is False


def test_square_root_transposition_generates_order_two_group() -> None:
    group = generate_monodromy_group([(1, 0)])
    assert group.order == 2
    assert group.transitive
    assert (0, 1) in group.elements
    assert (1, 0) in group.elements


def test_spectral_hgfm_preserves_constant_projective_fiber_cardinality() -> None:
    graph = build_spectral_hgfm(cubic_degree_collapse_path(5))
    payload = graph.to_dict()
    assert payload["schema"] == "omega-rootflow-spectral-hgfm-r0.4"
    assert graph.status == "OAK_PASS_SPECTRAL_HGFM_COMPILE"
    assert graph.invariants["sample_count"] == 5
    assert graph.invariants["nominal_root_count"] == 3
    assert graph.invariants["constant_fiber_cardinality"] is True
    assert graph.invariants["degree_transition_count"] == 1
    assert graph.invariants["infinity_transition_edges"] == 1
    assert len(graph.hyperedges) == 5
    assert len(graph.nodes) == 20
    assert len(graph.edges) == 16
    assert graph.theorem_claimed is False


def test_r04_cli_projective_puiseux_group_and_hgfm(tmp_path) -> None:
    outputs = {
        "pflow": tmp_path / "pflow.json",
        "puiseux": tmp_path / "puiseux.json",
        "group": tmp_path / "group.json",
        "hgfm": tmp_path / "hgfm.json",
    }
    assert main(["projective-flow-demo", "--samples", "17", "--output", str(outputs["pflow"])]) == 0
    assert main(["puiseux-demo", "--multiplicity", "3", "--output", str(outputs["puiseux"])]) == 0
    assert main(["monodromy-group-demo", "--output", str(outputs["group"])]) == 0
    assert main(["hgfm-demo", "--samples", "5", "--output", str(outputs["hgfm"])]) == 0

    pflow = json.loads(outputs["pflow"].read_text(encoding="utf-8"))
    puiseux = json.loads(outputs["puiseux"].read_text(encoding="utf-8"))
    group = json.loads(outputs["group"].read_text(encoding="utf-8"))
    hgfm = json.loads(outputs["hgfm"].read_text(encoding="utf-8"))
    assert pflow["version"] == "R0.5"
    assert pflow["result"]["degree_transition_count"] == 1
    assert puiseux["result"]["inferred_reciprocal_integer"] == 3
    assert group["group"]["order"] == 2
    assert hgfm["graph"]["invariants"]["constant_fiber_cardinality"] is True
