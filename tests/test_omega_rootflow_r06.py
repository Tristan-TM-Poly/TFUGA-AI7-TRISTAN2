import json
from fractions import Fraction

import numpy as np
import pytest

from omega_rootflow_t import (
    audit_exact_algebra,
    audit_tangent_prediction,
    collision_tangent_space,
    exact_discriminant,
    exact_newton_power_sums,
    exact_resultant,
)
from omega_rootflow_t.cli import main


def test_exact_square_free_cubic_has_integer_discriminant_and_moments() -> None:
    # (z+2)(z-1)(z-3) = z^3 - 2 z^2 - 5 z + 6.
    report = audit_exact_algebra([6, -5, -2, 1], power_sum_order=4)
    assert report.discriminant == Fraction(900)
    assert report.derivative_gcd == (Fraction(1),)
    assert report.repeated_factor_degree == 0
    assert report.square_free
    assert report.power_sums == (
        Fraction(3),
        Fraction(2),
        Fraction(14),
        Fraction(20),
        Fraction(98),
    )
    assert report.status == "OAK_PASS_EXACT_SQUARE_FREE"
    assert report.theorem_claimed is False


def test_exact_repeated_cubic_recovers_gcd_and_zero_discriminant() -> None:
    # (z-1)^2(z+2) = z^3 - 3z + 2.
    report = audit_exact_algebra([2, -3, 0, 1])
    assert report.discriminant == 0
    assert report.derivative_gcd == (Fraction(-1), Fraction(1))
    assert report.repeated_factor_degree == 1
    assert not report.square_free
    assert report.status == "OAK_PASS_EXACT_REPEATED_FACTOR"


def test_exact_rational_coefficients_remain_exact() -> None:
    coeffs = ["1/2", "-3/2", "1"]
    # z^2 - 3/2 z + 1/2 has discriminant 1/4.
    assert exact_discriminant(coeffs) == Fraction(1, 4)
    assert exact_newton_power_sums(coeffs, 2) == (
        Fraction(2),
        Fraction(3, 2),
        Fraction(5, 4),
    )


def test_exact_resultant_supports_constant_operand() -> None:
    # Res(z^2-1, 2) = 2^2.
    assert exact_resultant([-1, 0, 1], [2]) == 4


def test_exact_api_rejects_binary_float_as_ambiguous_input() -> None:
    with pytest.raises(TypeError):
        exact_discriminant([1.0, -2.0, 1.0])


def test_collision_tangent_space_for_generic_double_root_has_codimension_one() -> None:
    coeffs = np.array([2.0, -3.0, 0.0, 1.0])
    tangent = collision_tangent_space(coeffs, 1.0, [0, 1, 2])
    assert tangent.status == "OAK_PASS_COLLISION_TANGENT_SPACE"
    assert tangent.tangent_dimension == 2
    assert tangent.tangent_basis.shape == (2, 3)
    assert np.max(np.abs(tangent.tangent_constraint_residuals)) < 1e-12
    assert np.isclose(tangent.second_derivative_magnitude, 6.0)
    assert tangent.theorem_claimed is False


def test_collision_tangent_prediction_has_quadratic_residual_scaling() -> None:
    coeffs = np.array([2.0, -3.0, 0.0, 1.0])
    tangent = collision_tangent_space(coeffs, 1.0, [0, 1, 2])
    coarse = audit_tangent_prediction(coeffs, tangent, epsilon=1e-3)
    fine = audit_tangent_prediction(coeffs, tangent, epsilon=5e-4)
    assert coarse.status == "OAK_PASS_COLLISION_TANGENT_PREDICTION"
    assert fine.status == "OAK_PASS_COLLISION_TANGENT_PREDICTION"
    assert fine.maximum_polynomial_residual < 0.35 * coarse.maximum_polynomial_residual
    assert fine.maximum_derivative_residual < 0.35 * coarse.maximum_derivative_residual


def test_collision_tangent_refuses_point_off_discriminant() -> None:
    tangent = collision_tangent_space([-1.0, 0.0, 1.0], 1.0, [0, 1])
    assert tangent.status == "OAK_REFUSE_NOT_ON_COLLISION"
    assert tangent.tangent_dimension == 0


def test_collision_tangent_refuses_higher_multiplicity_as_double_model() -> None:
    # (z-1)^3 = z^3 - 3z^2 + 3z - 1: P''(1)=0.
    tangent = collision_tangent_space([-1.0, 3.0, -3.0, 1.0], 1.0, [0, 1, 2])
    assert tangent.status == "OAK_REFUSE_HIGHER_MULTIPLICITY"


def test_r06_cli_exact_and_collision_tangent_surfaces(tmp_path) -> None:
    exact_output = tmp_path / "exact.json"
    tangent_output = tmp_path / "tangent.json"

    assert main(
        [
            "exact-audit",
            "--coeffs",
            "2,-3,0,1",
            "--output",
            str(exact_output),
        ]
    ) == 0
    assert main(
        [
            "collision-tangent",
            "--coeffs",
            "2,-3,0,1",
            "--critical-root",
            "1",
            "--degrees",
            "0,1,2",
            "--epsilon",
            "0.001",
            "--output",
            str(tangent_output),
        ]
    ) == 0

    exact = json.loads(exact_output.read_text(encoding="utf-8"))
    tangent = json.loads(tangent_output.read_text(encoding="utf-8"))
    assert exact["version"] == "R0.6"
    assert exact["audit"]["discriminant"] == "0"
    assert exact["audit"]["derivative_gcd"] == ["-1", "1"]
    assert tangent["tangent"]["tangent_dimension"] == 2
    assert tangent["prediction_audit"]["status"] == "OAK_PASS_COLLISION_TANGENT_PREDICTION"
