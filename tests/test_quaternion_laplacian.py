from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hgfm.quaternion_laplacian import (
    Quaternion,
    example_incidence,
    is_hermitian,
    quadratic_form,
    quaternion_laplacian,
)


def test_quaternion_laplacian_is_hermitian():
    incidence = example_incidence()
    laplacian = quaternion_laplacian(incidence, weights=[1.0, 0.5, 2.0])

    assert is_hermitian(laplacian)


def test_quaternion_laplacian_quadratic_form_is_real_nonnegative():
    incidence = example_incidence()
    laplacian = quaternion_laplacian(incidence, weights=[1.0, 0.5, 2.0])
    vector = [
        Quaternion(1.0, 0.2, -0.1, 0.3),
        Quaternion(-0.5, 1.0, 0.4, -0.2),
        Quaternion(0.7, -0.3, 0.8, 0.1),
    ]

    energy = quadratic_form(vector, laplacian)

    assert energy.is_real(tol=1e-8)
    assert energy.r >= -1e-8


def test_negative_weights_are_rejected():
    incidence = example_incidence()

    try:
        quaternion_laplacian(incidence, weights=[1.0, -0.1, 2.0])
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("negative quaternion Laplacian weights must be rejected")
