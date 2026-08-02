"""Deterministic OAKBench tests for Ω-LOGEXP-MORPH-T∞."""

from math import isclose

import pytest

from omega_logexp_morph_t import (
    MorphSector,
    add,
    bch,
    compress_in_basis,
    determinant,
    homogeneous_affine,
    identity,
    lift_input,
    matrix,
    matrix_exponential,
    matrix_logarithm_near_identity,
    matrix_vector_multiply,
    max_row_sum_norm,
    multiply,
    nilpotent_lift,
    project_lifted_output,
    relative_reconstruction_error,
    scale,
    semigroup_defect,
    subtract,
)


def assert_matrix_close(left, right, tolerance=1.0e-10):
    assert max_row_sum_norm(subtract(left, right)) <= tolerance


def test_exp_zero_is_identity():
    assert_matrix_close(
        matrix_exponential(matrix([[0.0, 0.0], [0.0, 0.0]])),
        identity(2),
    )


def test_near_identity_log_reconstructs_small_rotation_generator():
    generator = matrix([[0.0, 0.1], [-0.1, 0.0]])
    transformation = matrix_exponential(generator)
    recovered = matrix_logarithm_near_identity(transformation)
    assert_matrix_close(recovered, generator, tolerance=1.0e-11)
    assert relative_reconstruction_error(
        transformation,
        matrix_exponential(recovered),
    ) < 1.0e-12


def test_log_rejects_outside_mercator_ball():
    with pytest.raises(ValueError, match="Mercator logarithm"):
        matrix_logarithm_near_identity(matrix([[2.0, 0.0], [0.0, 2.0]]))


def test_nilpotent_lift_encodes_rectangular_singular_morphism_exactly():
    linear_map = matrix([[1.0, 2.0, 0.0], [0.0, 0.0, 1.0]])
    lifted_generator = nilpotent_lift(linear_map)
    assert_matrix_close(
        multiply(lifted_generator, lifted_generator),
        matrix([[0.0] * 5 for _ in range(5)]),
    )

    lifted_transformation = matrix_exponential(lifted_generator)
    vector = (2.0, -1.0, 4.0)
    encoded = matrix_vector_multiply(
        lifted_transformation,
        lift_input(vector, output_size=2),
    )
    projected = project_lifted_output(encoded, input_size=3)
    assert projected == matrix_vector_multiply(linear_map, vector)


def test_bch_outperforms_naive_sum_for_noncommuting_generators():
    left = matrix([[0.0, 0.08], [-0.08, 0.0]])
    right = matrix([[0.03, 0.0], [0.0, -0.03]])
    target = multiply(matrix_exponential(left), matrix_exponential(right))

    naive_error = relative_reconstruction_error(
        target,
        matrix_exponential(add(left, right)),
    )
    bch_error = relative_reconstruction_error(
        target,
        matrix_exponential(bch(left, right, order=4)),
    )
    assert bch_error < 1.0e-6
    assert bch_error < naive_error / 1000.0


def test_semigroup_defect_is_small_for_one_autonomous_generator():
    generator = matrix([[0.0, 0.2], [-0.2, 0.0]])
    step = matrix_exponential(scale(generator, 0.5))
    full = matrix_exponential(generator)
    assert semigroup_defect(full, multiply(step, step)) < 1.0e-12


def test_basis_compression_recovers_generator_coefficients():
    rotation = matrix([[0.0, 1.0], [-1.0, 0.0]])
    stretch = matrix([[1.0, 0.0], [0.0, -1.0]])
    target = add(scale(rotation, 0.3), scale(stretch, -0.2))

    coefficients, approximation, residual = compress_in_basis(
        target,
        [rotation, stretch],
    )
    assert isclose(coefficients[0], 0.3, abs_tol=1.0e-10)
    assert isclose(coefficients[1], -0.2, abs_tol=1.0e-10)
    assert residual < 1.0e-10
    assert_matrix_close(approximation, target, tolerance=1.0e-10)


def test_morph_sector_detects_reflection_and_singular_map():
    reflection = MorphSector.classify(matrix([[-1.0, 0.0], [0.0, 1.0]]))
    assert reflection.invertible
    assert reflection.determinant_sign == -1

    singular = MorphSector.classify(matrix([[1.0, 0.0], [0.0, 0.0]]))
    assert not singular.invertible
    assert singular.rank == 1
    assert singular.determinant_sign == 0


def test_homogeneous_affine_has_expected_action():
    affine = homogeneous_affine(
        matrix([[2.0, 0.0], [0.0, 3.0]]),
        (5.0, -1.0),
    )
    result = matrix_vector_multiply(affine, (4.0, 2.0, 1.0))
    assert result == (13.0, 5.0, 1.0)


def test_determinant_of_exponential_is_positive():
    generator = matrix([[0.2, 0.4], [-0.1, -0.3]])
    assert determinant(matrix_exponential(generator)) > 0.0
