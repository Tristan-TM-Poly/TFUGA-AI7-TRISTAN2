from __future__ import annotations

from math import pi

import pytest

from omega_quaternion_crystal_t import (
    AffineTransform3D,
    CrystalState,
    CubicElasticity,
    Quaternion,
    hooke_stress,
    identity_matrix,
    matrix_determinant,
    matrix_trace,
    resolved_shear_stress,
    rotate_rank2,
    vector_norm,
)


def assert_vector_close(actual, expected, tolerance: float = 1.0e-10) -> None:
    assert actual == pytest.approx(expected, abs=tolerance)


def assert_matrix_close(actual, expected, tolerance: float = 1.0e-10) -> None:
    for row_actual, row_expected in zip(actual, expected, strict=True):
        assert row_actual == pytest.approx(row_expected, abs=tolerance)


def test_quaternion_rotates_x_to_y_about_z() -> None:
    orientation = Quaternion.from_axis_angle((0.0, 0.0, 1.0), pi / 2.0)
    assert orientation.is_unit()
    assert_vector_close(orientation.rotate_vector((1.0, 0.0, 0.0)), (0.0, 1.0, 0.0))


def test_rotation_preserves_vector_norm_and_double_cover() -> None:
    orientation = Quaternion.from_axis_angle((1.0, 2.0, 3.0), 0.713)
    opposite = Quaternion(-orientation.w, -orientation.x, -orientation.y, -orientation.z)
    vector = (2.0, -3.0, 4.0)

    rotated = orientation.rotate_vector(vector)
    rotated_by_opposite = opposite.rotate_vector(vector)

    assert vector_norm(rotated) == pytest.approx(vector_norm(vector))
    assert_vector_close(rotated, rotated_by_opposite)
    assert orientation.angle_to(opposite) == pytest.approx(0.0)


def test_rotations_about_different_axes_do_not_commute() -> None:
    qx = Quaternion.from_axis_angle((1.0, 0.0, 0.0), pi / 2.0)
    qy = Quaternion.from_axis_angle((0.0, 1.0, 0.0), pi / 2.0)
    vector = (0.0, 0.0, 1.0)

    x_then_y = (qy * qx).rotate_vector(vector)
    y_then_x = (qx * qy).rotate_vector(vector)

    assert x_then_y != pytest.approx(y_then_x)
    assert_vector_close(x_then_y, (0.0, -1.0, 0.0))
    assert_vector_close(y_then_x, (1.0, 0.0, 0.0))


def test_rank2_rotation_preserves_trace_and_determinant() -> None:
    stress = (
        (12.0, 2.0, -1.0),
        (2.0, 8.0, 3.0),
        (-1.0, 3.0, 5.0),
    )
    orientation = Quaternion.from_axis_angle((1.0, 1.0, 0.0), 0.9)
    rotated = rotate_rank2(stress, orientation)

    assert matrix_trace(rotated) == pytest.approx(matrix_trace(stress))
    assert matrix_determinant(rotated) == pytest.approx(matrix_determinant(stress))


def test_affine_composition_and_inverse_follow_semidirect_product_law() -> None:
    q = Quaternion.from_axis_angle((0.0, 0.0, 1.0), pi / 2.0)
    rotate_and_shift = AffineTransform3D.similarity(
        q,
        scale=2.0,
        translation=(1.0, 2.0, 3.0),
    )
    translate = AffineTransform3D(identity_matrix(), (4.0, 0.0, 0.0))
    composed = rotate_and_shift.compose(translate)
    point = (1.0, 1.0, 1.0)

    sequential = rotate_and_shift.apply(translate.apply(point))
    assert_vector_close(composed.apply(point), sequential)
    assert_vector_close(composed.inverse().apply(composed.apply(point)), point)
    assert composed.jacobian_determinant() == pytest.approx(8.0)


def test_cubic_hooke_law_and_stability_gate() -> None:
    elasticity = CubicElasticity(c11=200.0, c12=120.0, c44=80.0)
    strain = (
        (0.01, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    )
    stress = hooke_stress(elasticity.to_tensor(), strain)

    assert elasticity.is_mechanically_stable()
    assert elasticity.stability_margins() == {
        "c11_minus_c12": 80.0,
        "c11_plus_2c12": 440.0,
        "c44": 80.0,
    }
    assert_matrix_close(
        stress,
        (
            (2.0, 0.0, 0.0),
            (0.0, 1.2, 0.0),
            (0.0, 0.0, 1.2),
        ),
    )


def test_resolved_shear_stress_matches_schmid_projection() -> None:
    tau = 42.0
    stress = (
        (0.0, tau, 0.0),
        (tau, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    )
    assert resolved_shear_stress(stress, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == pytest.approx(tau)


def test_crystal_state_exposes_oak_invariants() -> None:
    state = CrystalState(
        orientation=Quaternion.from_axis_angle((0.0, 0.0, 1.0), pi / 3.0),
        deformation_gradient=(
            (1.1, 0.1, 0.0),
            (0.0, 0.9, 0.0),
            (0.0, 0.0, 1.0),
        ),
        stress_crystal=(
            (10.0, 2.0, 0.0),
            (2.0, 5.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
    )
    invariants = state.invariants()

    assert invariants["orientation_norm"] == pytest.approx(1.0)
    assert invariants["deformation_jacobian"] == pytest.approx(0.99)
    assert invariants["stress_trace"] == pytest.approx(16.0)
    assert invariants["hydrostatic_stress"] == pytest.approx(16.0 / 3.0)
    assert invariants["von_mises_stress"] > 0.0
