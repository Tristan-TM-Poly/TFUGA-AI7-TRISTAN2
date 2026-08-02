import pytest

from omega_logexp_morph_t.advanced import (
    active_factorization,
    build_morph_codex,
    commutator_graph,
    kronecker_sum,
    magnus_second_order_piecewise,
    polar_log_2d,
)
from omega_logexp_morph_t.core import (
    BranchLedger,
    matrix,
    matrix_exponential,
    relative_reconstruction_error,
)


def test_active_factorization_reconstructs_rectangular_rank_one_map():
    transformation = matrix(((1, 2, 3), (2, 4, 6)))
    factor = active_factorization(transformation)
    assert factor.active_rank == 1
    assert factor.reconstruction_error < 1.0e-12
    assert factor.reconstruct() == transformation


def test_active_factorization_reconstructs_rank_two_map():
    transformation = matrix(
        ((1, 0, 2), (0, 1, 3), (1, 1, 5), (2, -1, 1))
    )
    factor = active_factorization(transformation)
    assert factor.active_rank == 2
    assert factor.reconstruction_error < 1.0e-10


def test_polar_log_2d_reconstructs_orientation_preserving_map():
    transformation = matrix(((1.2, -0.3), (0.4, 0.9)))
    decomposition = polar_log_2d(transformation)
    assert decomposition.reconstruction_error < 1.0e-10
    assert relative_reconstruction_error(
        transformation, decomposition.reconstruct()
    ) < 1.0e-10
    assert all(value > 0.0 for value in decomposition.singular_values)


def test_polar_log_2d_rejects_reflection_sector():
    with pytest.raises(ValueError, match="positive determinant"):
        polar_log_2d(matrix(((-1, 0), (0, 1))))


def test_commutator_graph_distinguishes_commuting_and_coupled_generators():
    diagonal_a = matrix(((1, 0), (0, 2)))
    diagonal_b = matrix(((3, 0), (0, 4)))
    rotation = matrix(((0, -1), (1, 0)))
    edges = commutator_graph(
        {
            "diagonal-a": diagonal_a,
            "diagonal-b": diagonal_b,
            "rotation": rotation,
        }
    )
    strengths = {
        (edge.left, edge.right): edge.normalized_strength for edge in edges
    }
    assert strengths[("diagonal-a", "diagonal-b")] == pytest.approx(0.0)
    assert strengths[("diagonal-a", "rotation")] > 0.0


def test_kronecker_sum_exponential_matches_diagonal_spectrum():
    left = matrix(((0.1, 0), (0, -0.2)))
    right = matrix(((0.3, 0), (0, 0.4)))
    combined = matrix_exponential(kronecker_sum(left, right))
    expected_diagonal = (
        2.718281828459045**0.4,
        2.718281828459045**0.5,
        2.718281828459045**0.1,
        2.718281828459045**0.2,
    )
    for index, expected in enumerate(expected_diagonal):
        assert combined[index][index] == pytest.approx(expected, rel=1.0e-10)


def test_second_order_magnus_reduces_to_sum_when_generators_commute():
    first = matrix(((0.1, 0), (0, 0.2)))
    second = matrix(((0.3, 0), (0, -0.1)))
    omega = magnus_second_order_piecewise((first, second), step=0.5)
    assert omega == matrix(((0.2, 0.0), (0.0, 0.05)))


def test_codex_exposes_kernel_cokernel_and_oak_boundary():
    transformation = matrix(((1, 2, 3), (2, 4, 6)))
    codex = build_morph_codex(
        transformation,
        branch_ledger=BranchLedger(continuity_verified=True),
    )
    assert codex.signature.rank == 1
    assert codex.signature.kernel_dimension == 2
    assert codex.signature.cokernel_dimension == 1
    assert "non-trivial-kernel" in codex.singular_sector
    assert codex.residuals["active_factorization"] < 1.0e-12
    assert "do not by themselves" in codex.validity["warning"]


def test_zero_map_codex_is_explicitly_singular():
    codex = build_morph_codex(matrix(((0, 0), (0, 0))))
    assert "zero-map" in codex.singular_sector
    assert codex.signature.rank == 0
