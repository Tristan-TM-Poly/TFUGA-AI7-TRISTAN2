"""Exact tensor channels induced by transpose, trace and rotational structure."""

from __future__ import annotations

from math import sqrt
from typing import Sequence

from .linalg import (
    Matrix,
    add,
    as_matrix,
    as_vector,
    flatten,
    identity,
    outer,
    scale,
    subtract,
    trace,
    transpose,
    zeros,
)
from .models import RepairBundle, TensorChannel


def symmetric_part(matrix: Matrix) -> Matrix:
    rows = len(matrix)
    if rows == 0 or any(len(row) != rows for row in matrix):
        raise ValueError("symmetric decomposition requires a square matrix")
    return scale(add(matrix, transpose(matrix)), 0.5)


def antisymmetric_part(matrix: Matrix) -> Matrix:
    rows = len(matrix)
    if rows == 0 or any(len(row) != rows for row in matrix):
        raise ValueError("antisymmetric decomposition requires a square matrix")
    return scale(subtract(matrix, transpose(matrix)), 0.5)


def isotropic_part(matrix: Matrix) -> Matrix:
    rows = len(matrix)
    if rows == 0 or any(len(row) != rows for row in matrix):
        raise ValueError("isotropic decomposition requires a square matrix")
    return scale(identity(rows), trace(matrix) / rows)


def symmetric_traceless_part(matrix: Matrix) -> Matrix:
    return subtract(symmetric_part(matrix), isotropic_part(matrix))


def decompose_square(matrix: Matrix) -> tuple[Matrix, Matrix, Matrix]:
    """Return symmetric-traceless, isotropic and antisymmetric components."""

    return (
        symmetric_traceless_part(matrix),
        isotropic_part(matrix),
        antisymmetric_part(matrix),
    )


def reconstruct_square(parts: Sequence[Matrix]) -> Matrix:
    if not parts:
        raise ValueError("at least one component is required")
    result = zeros(len(parts[0]), len(parts[0][0]))
    for part in parts:
        result = add(result, part)
    return result


def dimension_identity(size: int) -> dict[str, int]:
    if size <= 0:
        raise ValueError("size must be positive")
    return {
        "full": size * size,
        "symmetric": size * (size + 1) // 2,
        "symmetric_traceless": size * (size + 1) // 2 - 1,
        "antisymmetric": size * (size - 1) // 2,
        "trace": 1,
    }


def analyze_2d(left: Sequence[float], right: Sequence[float]) -> RepairBundle:
    """Build the exact 4→(3+1)→((2+1)+1) channel tree."""

    x = as_vector(left)
    y = as_vector(right)
    if len(x) != 2 or len(y) != 2:
        raise ValueError("analyze_2d requires two 2D vectors")
    tensor = outer(x, y)
    t11, t12 = tensor[0]
    t21, t22 = tensor[1]
    root2 = sqrt(2.0)
    q1 = (t11 - t22) / root2
    q2 = (t12 + t21) / root2
    q3 = (t11 + t22) / root2
    q4 = (t12 - t21) / root2

    channels = (
        TensorChannel(
            name="full",
            dimension=4,
            values=(q1, q2, q3, q4),
            symmetry="O(2): complete rank-2 tensor",
            interpretation="All four bilinear degrees of freedom in an adapted orthonormal basis.",
        ),
        TensorChannel(
            name="symmetric",
            dimension=3,
            values=(q1, q2, q3),
            symmetry="transpose-even",
            parent="full",
            interpretation="Symmetric tensor channel.",
        ),
        TensorChannel(
            name="symmetric_traceless",
            dimension=2,
            values=(q1, q2),
            symmetry="transpose-even, trace-free",
            parent="symmetric",
            interpretation="Anisotropic spin-2-like channel under planar rotations.",
        ),
        TensorChannel(
            name="trace",
            dimension=1,
            values=(q3,),
            symmetry="O(2)-scalar",
            parent="symmetric",
            interpretation="Isotropic scalar channel, proportional to x·y.",
        ),
        TensorChannel(
            name="antisymmetric",
            dimension=1,
            values=(q4,),
            symmetry="transpose-odd pseudoscalar",
            parent="full",
            interpretation="Oriented-area channel, proportional to det[x,y].",
        ),
        TensorChannel(
            name="carrier",
            dimension=4,
            values=x + y,
            symmetry="direct-sum input carrier",
            interpretation="Inputs retained without claiming extra bilinear independence.",
        ),
    )

    q1_, q2_, q3_, q4_ = channels[0].values
    reconstruction = as_matrix(
        (
            ((q3_ + q1_) / root2, (q2_ + q4_) / root2),
            ((q2_ - q4_) / root2, (q3_ - q1_) / root2),
        )
    )
    residual = subtract(tensor, reconstruction)
    return RepairBundle(
        input_left=x,
        input_right=y,
        full_tensor=tensor,
        channels=channels,
        reconstruction=reconstruction,
        residual=residual,
        status="EXACT_2D_TENSOR_REPAIR_BUNDLE_R0_1",
        claims={
            "classical_tensor_dimension_preserved": True,
            "derived_channels_independent_as_a_union": False,
            "exact_reconstruction_claimed": True,
            "new_physical_law_claimed": False,
        },
    )


def analyze_square_outer(left: Sequence[float], right: Sequence[float]) -> dict[str, object]:
    x = as_vector(left)
    y = as_vector(right)
    if len(x) != len(y) or not x:
        raise ValueError("vectors must have the same positive dimension")
    tensor = outer(x, y)
    symmetric_traceless, isotropic, antisymmetric = decompose_square(tensor)
    reconstructed = reconstruct_square((symmetric_traceless, isotropic, antisymmetric))
    dims = dimension_identity(len(x))
    return {
        "dimension": len(x),
        "dimension_identity": dims,
        "tensor": tensor,
        "symmetric_traceless": symmetric_traceless,
        "isotropic": isotropic,
        "antisymmetric": antisymmetric,
        "reconstruction": reconstructed,
        "channels_flat": {
            "full": flatten(tensor),
            "symmetric_traceless_ambient": flatten(symmetric_traceless),
            "isotropic_ambient": flatten(isotropic),
            "antisymmetric_ambient": flatten(antisymmetric),
        },
    }
