"""R0.3 tests for irreducible bases, contractions and Young combinatorics."""

from __future__ import annotations

from math import comb, factorial

import pytest

from omega_tensor_repair_t.contractions import (
    ContractionPlan,
    ContractionStep,
    TensorState,
    contract_pair,
    double_trace_rank4,
    trace_matrix_tensor,
)
from omega_tensor_repair_t.higher_order import DenseTensor, outer_many
from omega_tensor_repair_t.irreducible_basis import (
    analyze_square_irreducible,
    basis_orthonormality_error,
    square_irreducible_basis,
)
from omega_tensor_repair_t.linalg import almost_equal, as_matrix
from omega_tensor_repair_t.young import (
    YoungDiagram,
    column_antisymmetrize,
    partitions,
    row_symmetrize,
    young_dimension_atlas,
    young_operator,
)


@pytest.mark.parametrize("size", range(1, 9))
def test_irreducible_basis_cardinality_and_sectors(size: int) -> None:
    basis = square_irreducible_basis(size)
    assert len(basis) == size * size
    assert sum(element.sector == "symmetric_traceless" for element in basis) == size * (size + 1) // 2 - 1
    assert sum(element.sector == "isotropic" for element in basis) == 1
    assert sum(element.sector == "antisymmetric" for element in basis) == size * (size - 1) // 2


@pytest.mark.parametrize("size", range(1, 8))
def test_irreducible_basis_is_orthonormal(size: int) -> None:
    assert basis_orthonormality_error(square_irreducible_basis(size)) <= 2e-14


@pytest.mark.parametrize("size", range(1, 7))
def test_irreducible_analysis_reconstructs_deterministic_matrix(size: int) -> None:
    matrix = as_matrix(
        ((row + 1) * 1.25 - (col + 2) * 0.75 + ((row * col) % 3) for col in range(size))
        for row in range(size)
    )
    result = analyze_square_irreducible(matrix)
    assert result.reconstruction_error <= 1e-11
    assert almost_equal(result.reconstruction, matrix, tolerance=1e-11)
    assert len(result.full_coordinates) == size * size


def test_irreducible_analysis_rejects_non_square_matrix() -> None:
    with pytest.raises(ValueError):
        analyze_square_irreducible(as_matrix(((1, 2, 3), (4, 5, 6))))


@pytest.mark.parametrize("size", range(1, 9))
def test_matrix_tensor_trace(size: int) -> None:
    values = tuple(float(index + 1) for index in range(size * size))
    tensor = DenseTensor((size, size), values)
    expected = sum(values[index * size + index] for index in range(size))
    assert trace_matrix_tensor(tensor) == expected


def test_contract_pair_rank_three() -> None:
    tensor = DenseTensor((2, 3, 2), tuple(float(index) for index in range(12)))
    output, receipt = contract_pair(tensor, 0, 2, label="outer-trace")
    assert output.shape == (3,)
    assert output.data == (7.0, 11.0, 15.0)
    assert receipt.input_shape == (2, 3, 2)
    assert receipt.output_shape == (3,)
    assert receipt.summed_dimension == 2


def test_contract_pair_rejects_unequal_axes() -> None:
    tensor = DenseTensor((2, 3), tuple(float(index) for index in range(6)))
    with pytest.raises(ValueError):
        contract_pair(tensor, 0, 1)


def test_contraction_plan_to_scalar() -> None:
    tensor = DenseTensor(
        (2, 2, 2, 2),
        tuple(float(index + 1) for index in range(16)),
    )
    plan = ContractionPlan(
        (
            ContractionStep(0, 1, "trace-a"),
            ContractionStep(0, 1, "trace-b"),
        )
    )
    result = plan.apply(tensor)
    assert result.output.shape == tuple()
    assert result.output.scalar == double_trace_rank4(tensor)
    assert len(result.receipts) == 2


def test_tensor_state_scalar_contract() -> None:
    state = TensorState(tuple(), (3.5,))
    assert state.scalar == 3.5
    assert state.rank == 0
    with pytest.raises(ValueError):
        state.to_dense()


@pytest.mark.parametrize(
    ("order", "expected"),
    ((1, 1), (2, 2), (3, 3), (4, 5), (5, 7), (6, 11), (7, 15)),
)
def test_partition_counts(order: int, expected: int) -> None:
    assert len(partitions(order)) == expected


@pytest.mark.parametrize("order", range(1, 8))
def test_hook_length_identity(order: int) -> None:
    diagrams = partitions(order)
    assert sum(diagram.standard_tableau_count() ** 2 for diagram in diagrams) == factorial(order)


@pytest.mark.parametrize("dimension", range(1, 8))
@pytest.mark.parametrize("order", range(1, 7))
def test_symmetric_power_dimension(dimension: int, order: int) -> None:
    diagram = YoungDiagram((order,))
    assert diagram.schur_dimension(dimension) == comb(dimension + order - 1, order)


@pytest.mark.parametrize("dimension", range(1, 8))
@pytest.mark.parametrize("order", range(1, 7))
def test_exterior_power_dimension(dimension: int, order: int) -> None:
    diagram = YoungDiagram(tuple(1 for _ in range(order)))
    expected = comb(dimension, order) if order <= dimension else 0
    assert diagram.schur_dimension(dimension) == expected


def test_young_diagram_validation() -> None:
    with pytest.raises(ValueError):
        YoungDiagram(tuple())
    with pytest.raises(ValueError):
        YoungDiagram((1, 2))
    with pytest.raises(ValueError):
        YoungDiagram((2, 0))


def test_one_row_young_operator_matches_full_symmetrization() -> None:
    tensor = outer_many(((1.0, 2.0), (3.0, -1.0), (2.0, 4.0)))
    diagram = YoungDiagram((3,))
    assert young_operator(tensor, diagram).data == pytest.approx(tensor.symmetrize().data)
    assert row_symmetrize(tensor, diagram).data == pytest.approx(tensor.symmetrize().data)


def test_one_column_young_operator_matches_full_antisymmetrization() -> None:
    tensor = DenseTensor((3, 3, 3), tuple(float((index * 7) % 13 - 6) for index in range(27)))
    diagram = YoungDiagram((1, 1, 1))
    assert young_operator(tensor, diagram).data == pytest.approx(tensor.antisymmetrize().data)
    assert column_antisymmetrize(tensor, diagram).data == pytest.approx(tensor.antisymmetrize().data)


def test_mixed_young_operator_preserves_shape_and_is_deterministic() -> None:
    tensor = DenseTensor((2, 2, 2), tuple(float(index - 3) for index in range(8)))
    diagram = YoungDiagram((2, 1))
    first = young_operator(tensor, diagram)
    second = young_operator(tensor, diagram)
    assert first.shape == tensor.shape
    assert first.data == second.data


@pytest.mark.parametrize("order", range(1, 7))
@pytest.mark.parametrize("dimension", range(1, 7))
def test_young_dimension_atlas_is_complete(order: int, dimension: int) -> None:
    atlas = young_dimension_atlas(order, dimension)
    assert len(atlas) == len(partitions(order))
    assert all(entry["boxes"] == order for entry in atlas)
    assert all(entry["schur_dimension"] >= 0 for entry in atlas)
