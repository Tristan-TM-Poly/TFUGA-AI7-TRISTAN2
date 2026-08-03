from __future__ import annotations

from itertools import product
from math import isclose

import pytest

from omega_tensor_repair_t.benchmark import run_benchmark
from omega_tensor_repair_t.blocks import BlockPartition
from omega_tensor_repair_t.compiler import compile_spec
from omega_tensor_repair_t.frames import identity_frame
from omega_tensor_repair_t.linalg import as_matrix, frobenius_norm, outer, subtract, trace
from omega_tensor_repair_t.oak import audit_bundle, audit_square, audit_tower
from omega_tensor_repair_t.projectors import (
    analyze_2d,
    decompose_square,
    dimension_identity,
    reconstruct_square,
)
from omega_tensor_repair_t.repair import repair_symmetry, repair_trace
from omega_tensor_repair_t.symmetry import default_rank2_tower_2d, group_average


def test_exact_2d_channel_dimensions_and_reconstruction() -> None:
    bundle = analyze_2d((1.0, 2.0), (3.0, 4.0))
    assert bundle.full_dimension == 4
    assert bundle.channel("full").dimension == 4
    assert bundle.channel("symmetric").dimension == 3
    assert bundle.channel("symmetric_traceless").dimension == 2
    assert bundle.channel("trace").dimension == 1
    assert bundle.channel("antisymmetric").dimension == 1
    assert bundle.residual_norm <= 1e-12
    assert audit_bundle(bundle).passed


def test_q_coordinates_have_expected_semantics() -> None:
    bundle = analyze_2d((1.0, 0.0), (0.0, 1.0))
    assert isclose(bundle.channel("trace").values[0], 0.0, abs_tol=1e-12)
    assert bundle.channel("antisymmetric").values[0] > 0.0


def test_many_2d_outer_products_round_trip() -> None:
    values = (-3.0, -1.0, 0.0, 0.5, 2.0)
    for fixture in product(values, repeat=4):
        bundle = analyze_2d(fixture[:2], fixture[2:])
        assert bundle.residual_norm <= 1e-12


@pytest.mark.parametrize("size", range(1, 12))
def test_general_dimension_identity(size: int) -> None:
    dims = dimension_identity(size)
    assert dims["full"] == dims["symmetric_traceless"] + dims["antisymmetric"] + dims["trace"]
    assert dims["symmetric"] == dims["symmetric_traceless"] + dims["trace"]


def test_general_square_decomposition_round_trip() -> None:
    matrix = as_matrix(((1, 2, 3), (4, 5, 6), (-2, 8, 0.5)))
    parts = decompose_square(matrix)
    reconstructed = reconstruct_square(parts)
    assert frobenius_norm(subtract(matrix, reconstructed)) <= 1e-12
    assert audit_square(matrix).passed


def test_identity_frame_round_trip() -> None:
    frame = identity_frame(2, 3)
    matrix = as_matrix(((1, 2, 3), (4, 5, 6)))
    result = frame.round_trip(matrix)
    assert frobenius_norm(result.residual) <= 1e-12
    assert isclose(result.energy_ratio, 1.0)


def test_regular_block_partition_is_exact() -> None:
    matrix = outer((1, 2, 3, 4), (-1, 0.5, 2, -3))
    partition = BlockPartition.regular(4, 4, (1, 3), (2,))
    records = partition.analyze(matrix)
    assert len(records) == 6
    reconstructed = partition.synthesize(records)
    assert frobenius_norm(subtract(matrix, reconstructed)) <= 1e-12
    assert partition.audit(matrix)["exact"] is True


def test_block_partition_rejects_overlap_or_holes() -> None:
    from omega_tensor_repair_t.blocks import BlockSpec

    with pytest.raises(ValueError):
        BlockPartition(
            (2, 2),
            (
                BlockSpec("a", 0, 2, 0, 1),
                BlockSpec("b", 0, 1, 1, 2),
            ),
        )


def test_default_tower_conserves_dimension_at_each_branch() -> None:
    assert audit_tower(default_rank2_tower_2d()).passed


def test_group_average_is_invariant_under_swap() -> None:
    matrix = as_matrix(((1, 2), (3, 4)))
    averaged = group_average(matrix, ((0, 1), (1, 0)))
    swapped = group_average(averaged, ((1, 0),))
    assert averaged == swapped


def test_trace_repair_exposes_correction() -> None:
    matrix = as_matrix(((1, 2), (3, 4)))
    result = repair_trace(matrix, 10.0)
    assert result.exact_constraint_satisfied
    assert isclose(trace(result.repaired), 10.0)
    assert result.residual_norm > 0.0


def test_symmetry_repair_exposes_correction() -> None:
    matrix = as_matrix(((1, 2), (5, 4)))
    result = repair_symmetry(matrix)
    assert result.exact_constraint_satisfied
    assert result.repaired[0][1] == result.repaired[1][0]
    assert result.residual_norm > 0.0


def test_compiler_keeps_epistemic_boundaries() -> None:
    result = compile_spec(
        {
            "left_dimension": 2,
            "right_dimension": 2,
            "channels": ["full", "symmetric", "symmetric_traceless", "trace", "antisymmetric", "residual"],
        }
    )
    payload = result.to_dict()
    assert payload["plan"]["classical_tensor_dimension"] == 4
    assert payload["plan"]["claims"]["all_views_independent"] is False
    assert payload["plan"]["exact_reconstruction_required"] is True


def test_non_square_compiler_warns_about_transpose_channels() -> None:
    result = compile_spec(
        {
            "left_dimension": 2,
            "right_dimension": 3,
            "channels": ["full", "symmetric", "trace"],
        }
    )
    assert result.warnings
    names = {channel["name"] for channel in result.plan["channels"]}
    assert "symmetric" not in names


def test_benchmark_is_deterministic_and_certified() -> None:
    first = run_benchmark()
    second = run_benchmark()
    assert first == second
    assert first["status"] == "CERTIFIED_FINITE_SOFTWARE_FIXTURES_R0_1"
    assert first["bundle_fixtures"] == 625
    assert first["claims"]["general_theorem_proved_by_benchmark"] is False
