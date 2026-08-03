from __future__ import annotations

from itertools import product
from math import isclose

import pytest

from omega_tensor_repair_t.benchmark_r02 import run_benchmark_r02
from omega_tensor_repair_t.clebsch_gordan import su2_clebsch_gordan
from omega_tensor_repair_t.factorization import low_rank_approximation
from omega_tensor_repair_t.higher_order import DenseTensor, outer_many, permutation_sign
from omega_tensor_repair_t.hypergraph import bundle_hypergraph, tower_hypergraph
from omega_tensor_repair_t.projectors import analyze_2d
from omega_tensor_repair_t.symmetry import default_rank2_tower_2d


@pytest.mark.parametrize("left,right", product(range(1, 11), repeat=2))
def test_su2_dimension_branching(left: int, right: int) -> None:
    branch = su2_clebsch_gordan(left, right)
    assert branch.exact
    assert branch.outputs[0].dimension == left + right - 1
    assert branch.outputs[-1].dimension == abs(left - right) + 1
    assert all(
        a.dimension - b.dimension == 2
        for a, b in zip(branch.outputs, branch.outputs[1:])
    )


def test_known_su2_examples() -> None:
    assert [item.dimension for item in su2_clebsch_gordan(2, 2).outputs] == [3, 1]
    assert [item.dimension for item in su2_clebsch_gordan(2, 3).outputs] == [4, 2]
    assert [item.dimension for item in su2_clebsch_gordan(3, 3).outputs] == [5, 3, 1]


def test_permutation_sign() -> None:
    assert permutation_sign((0, 1, 2)) == 1
    assert permutation_sign((1, 0, 2)) == -1
    assert permutation_sign((2, 1, 0)) == -1


def test_dense_tensor_axis_permutation_round_trip() -> None:
    tensor = DenseTensor((2, 3, 2), tuple(float(index) for index in range(12)))
    permuted = tensor.permute_axes((2, 0, 1))
    restored = permuted.permute_axes((1, 2, 0))
    assert restored == tensor


def test_full_symmetrizer_and_antisymmetrizer_are_idempotent() -> None:
    tensor = outer_many(((1.0, 2.0), (-1.0, 3.0), (0.5, 4.0)))
    symmetric = tensor.symmetrize()
    antisymmetric = tensor.antisymmetrize()
    assert symmetric.subtract(symmetric.symmetrize()).norm_squared() <= 1e-24
    assert antisymmetric.subtract(antisymmetric.antisymmetrize()).norm_squared() <= 1e-24


def test_antisymmetrizer_vanishes_when_dimension_is_too_small() -> None:
    tensor = outer_many(((1.0, 2.0), (-1.0, 3.0), (0.5, 4.0)))
    assert tensor.antisymmetrize().norm_squared() <= 1e-24


def test_rank_one_factorization_exact_fixture() -> None:
    matrix = ((3.0, 6.0), (-1.5, -3.0), (0.5, 1.0))
    result = low_rank_approximation(matrix, 1)
    assert result.residual_norm <= 1e-10
    assert isclose(result.captured_energy_fraction, 1.0, abs_tol=1e-12)


def test_low_rank_residual_decreases_monotonically() -> None:
    matrix = ((4.0, 1.0, 0.0), (1.0, 3.0, 0.5), (0.0, 0.5, 2.0))
    results = [low_rank_approximation(matrix, rank) for rank in range(4)]
    assert all(
        a.residual_norm + 1e-10 >= b.residual_norm
        for a, b in zip(results, results[1:])
    )
    assert results[-1].residual_norm <= 1e-8


def test_hypergraph_is_deterministic_and_traceable() -> None:
    bundle = analyze_2d((1.0, 2.0), (3.0, -1.0))
    first = bundle_hypergraph(bundle).to_dict()
    second = bundle_hypergraph(bundle).to_dict()
    assert first == second
    assert first["sha256"]
    assert any(
        edge["relation"] == "tensor-product"
        for edge in first["hyperedges"]
    )


def test_tower_hypergraph_has_two_branching_edges() -> None:
    graph = tower_hypergraph(default_rank2_tower_2d()).to_dict()
    assert len(graph["nodes"]) == 5
    assert len(graph["hyperedges"]) == 2


def test_r02_benchmark_is_deterministic_and_certified() -> None:
    first = run_benchmark_r02()
    second = run_benchmark_r02()
    assert first == second
    assert first["status"] == "CERTIFIED_EXTENDED_SOFTWARE_FIXTURES_R0_2"
    assert first["claims"]["optimal_svd_claimed"] is False
