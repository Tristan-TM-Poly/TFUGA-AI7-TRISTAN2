from __future__ import annotations

from typing import Any

from .core import Matrix, matmul, pseudoinverse, shape, transpose


def _matrix_sub(a: Matrix, b: Matrix) -> Matrix:
    if shape(a) != shape(b):
        raise ValueError("matrix dimension mismatch")
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _frobenius(a: Matrix) -> float:
    return sum(value * value for row in a for value in row) ** 0.5


def resolution_matrices(a: Matrix, *, rtol: float = 1e-10) -> dict[str, Matrix]:
    """Return state- and observation-space resolution projectors.

    `state_resolution = A+ A` projects onto the reconstructible row-space part of
    the state. `observation_resolution = A A+` projects onto the column space of
    observations reproducible by the forward model.
    """
    ap = pseudoinverse(a, rtol=rtol)
    return {
        "state_resolution": matmul(ap, a),
        "observation_resolution": matmul(a, ap),
    }


def penrose_residuals(a: Matrix, *, rtol: float = 1e-10) -> dict[str, float]:
    """Return numerical residuals for the four Moore-Penrose conditions."""
    ap = pseudoinverse(a, rtol=rtol)
    aap = matmul(a, ap)
    apa = matmul(ap, a)
    return {
        "A_Aplus_A_minus_A": _frobenius(_matrix_sub(matmul(aap, a), a)),
        "Aplus_A_Aplus_minus_Aplus": _frobenius(_matrix_sub(matmul(apa, ap), ap)),
        "symmetry_A_Aplus": _frobenius(_matrix_sub(transpose(aap), aap)),
        "symmetry_Aplus_A": _frobenius(_matrix_sub(transpose(apa), apa)),
    }


def identifiability_geometry(a: Matrix, *, rtol: float = 1e-10) -> dict[str, Any]:
    """Bundle projectors and Penrose residuals for OAK evidence."""
    return {
        **resolution_matrices(a, rtol=rtol),
        "penrose_residuals": penrose_residuals(a, rtol=rtol),
        "interpretation": {
            "state_resolution": "identity only on fully reconstructible state directions",
            "observation_resolution": "identity only on observations lying in the forward-model column space",
        },
        "oak_boundary": [
            "a projector exposes recoverable subspaces but does not identify a physical cause uniquely",
            "small Penrose residuals validate the numerical pseudoinverse algebra, not the forward model itself",
        ],
    }
