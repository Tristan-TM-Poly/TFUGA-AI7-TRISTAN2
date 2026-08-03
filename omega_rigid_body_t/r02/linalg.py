"""Small dependency-free linear algebra for Ω-RIGID-BODY-T R0.2."""
from __future__ import annotations

from math import acos, atan2, isfinite, sqrt
from typing import Iterable, Sequence

Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]
Matrix3 = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


def vector3(values: Sequence[float]) -> Vector3:
    if len(values) != 3:
        raise ValueError("expected exactly three components")
    result = tuple(float(v) for v in values)
    if not all(isfinite(v) for v in result):
        raise ValueError("vector components must be finite")
    return result  # type: ignore[return-value]


def add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(s: float, a: Vector3) -> Vector3:
    return (s * a[0], s * a[1], s * a[2])


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("dot product dimensions differ")
    return sum(float(x) * float(y) for x, y in zip(a, b))


def cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a: Sequence[float]) -> float:
    return sqrt(dot(a, a))


def normalize(a: Sequence[float]) -> tuple[float, ...]:
    magnitude = norm(a)
    if magnitude == 0.0 or not isfinite(magnitude):
        raise ValueError("cannot normalize a zero or non-finite vector")
    return tuple(float(v) / magnitude for v in a)


def qnormalize(q: Sequence[float]) -> Quaternion:
    if len(q) != 4:
        raise ValueError("quaternion must have four components")
    result = normalize(q)
    return result  # type: ignore[return-value]


def qconjugate(q: Quaternion) -> Quaternion:
    return (q[0], -q[1], -q[2], -q[3])


def qmultiply(left: Quaternion, right: Quaternion) -> Quaternion:
    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return (
        lw * rw - lx * rx - ly * ry - lz * rz,
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
    )


def qderivative_body_to_inertial(q: Quaternion, omega_body: Vector3) -> Quaternion:
    product = qmultiply(q, (0.0, *omega_body))
    return tuple(0.5 * value for value in product)  # type: ignore[return-value]


def qrotate(q: Quaternion, vector: Vector3) -> Vector3:
    unit = qnormalize(q)
    rotated = qmultiply(qmultiply(unit, (0.0, *vector)), qconjugate(unit))
    return (rotated[1], rotated[2], rotated[3])


def qrelative(final: Quaternion, initial: Quaternion) -> Quaternion:
    return qnormalize(qmultiply(qnormalize(final), qconjugate(qnormalize(initial))))


def qto_matrix(q: Quaternion) -> Matrix3:
    w, x, y, z = qnormalize(q)
    return (
        (1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)),
        (2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)),
        (2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)),
    )


def signed_quaternion_angle_about_axis(q: Quaternion, axis: Vector3) -> float:
    """Return the signed rotation angle modulo 2π about a prescribed axis."""
    w, x, y, z = qnormalize(q)
    axis_hat = normalize(axis)
    projected = x * axis_hat[0] + y * axis_hat[1] + z * axis_hat[2]
    angle = 2.0 * atan2(projected, w)
    return angle % (2.0 * 3.141592653589793)


def quaternion_axis_error(q: Quaternion, axis: Vector3) -> float:
    unit = qnormalize(q)
    vector = (unit[1], unit[2], unit[3])
    vector_norm = norm(vector)
    if vector_norm < 1e-15:
        return 0.0
    axis_hat = normalize(axis)
    alignment = abs(dot(vector, axis_hat)) / vector_norm
    return acos(max(-1.0, min(1.0, alignment)))


def matvec(matrix: Matrix3, vector: Vector3) -> Vector3:
    return tuple(dot(row, vector) for row in matrix)  # type: ignore[return-value]


def determinant3(matrix: Matrix3) -> float:
    a, b, c = matrix
    return dot(a, cross(b, c))


def solve3(matrix: Matrix3, rhs: Vector3) -> Vector3:
    """Solve a non-singular 3×3 system with partial pivoting."""
    augmented = [list(matrix[i]) + [rhs[i]] for i in range(3)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-18:
            raise ArithmeticError("singular 3x3 system")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        for j in range(column, 4):
            augmented[column][j] /= divisor
        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            for j in range(column, 4):
                augmented[row][j] -= factor * augmented[column][j]
    return (augmented[0][3], augmented[1][3], augmented[2][3])


def max_abs(values: Iterable[float]) -> float:
    return max((abs(float(value)) for value in values), default=0.0)
