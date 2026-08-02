"""Quaternion, affine, stress, and crystal operators for Ω-QUATERNION-CRYSTAL-T.

The module deliberately keeps distinct mathematical responsibilities:

* unit quaternions encode orientation and proper rotations in 3D;
* 3x3 matrices encode general linear maps, stretch, and shear;
* rank-2 tensors encode stress and strain;
* rank-4 tensors encode linear elasticity.

This separation is an OAK safety invariant: a quaternion is not treated as a
replacement for a constitutive law or for a physical tensor.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, cos, isclose, pi, sin, sqrt
from typing import Iterable, Sequence, TypeAlias

Vector3: TypeAlias = tuple[float, float, float]
Matrix3: TypeAlias = tuple[Vector3, Vector3, Vector3]
Tensor4: TypeAlias = tuple[tuple[tuple[tuple[float, ...], ...], ...], ...]

_EPS = 1.0e-12


def _vector3(values: Iterable[float]) -> Vector3:
    vector = tuple(float(value) for value in values)
    if len(vector) != 3:
        raise ValueError(f"Expected three vector components, got {len(vector)}")
    return vector[0], vector[1], vector[2]


def matrix3(rows: Iterable[Iterable[float]]) -> Matrix3:
    converted = tuple(_vector3(row) for row in rows)
    if len(converted) != 3:
        raise ValueError(f"Expected three matrix rows, got {len(converted)}")
    return converted[0], converted[1], converted[2]


def identity_matrix() -> Matrix3:
    return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def vector_dot(left: Sequence[float], right: Sequence[float]) -> float:
    a = _vector3(left)
    b = _vector3(right)
    return sum(a[index] * b[index] for index in range(3))


def vector_norm(vector: Sequence[float]) -> float:
    return sqrt(vector_dot(vector, vector))


def normalize_vector(vector: Sequence[float]) -> Vector3:
    converted = _vector3(vector)
    norm = vector_norm(converted)
    if norm <= _EPS:
        raise ValueError("Cannot normalize a zero vector")
    return tuple(component / norm for component in converted)  # type: ignore[return-value]


def matrix_transpose(value: Matrix3) -> Matrix3:
    return tuple(
        tuple(value[column][row] for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def matrix_multiply(left: Matrix3, right: Matrix3) -> Matrix3:
    right_t = matrix_transpose(right)
    return tuple(
        tuple(vector_dot(row, column) for column in right_t)
        for row in left
    )  # type: ignore[return-value]


def matrix_vector_multiply(value: Matrix3, vector: Sequence[float]) -> Vector3:
    converted = _vector3(vector)
    return tuple(vector_dot(row, converted) for row in value)  # type: ignore[return-value]


def matrix_add(left: Matrix3, right: Matrix3) -> Matrix3:
    return tuple(
        tuple(left[row][column] + right[row][column] for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def matrix_scale(value: Matrix3, scale: float) -> Matrix3:
    return tuple(
        tuple(float(scale) * value[row][column] for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def matrix_trace(value: Matrix3) -> float:
    return value[0][0] + value[1][1] + value[2][2]


def matrix_determinant(value: Matrix3) -> float:
    a, b, c = value[0]
    d, e, f = value[1]
    g, h, i = value[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def matrix_inverse(value: Matrix3) -> Matrix3:
    determinant = matrix_determinant(value)
    if abs(determinant) <= _EPS:
        raise ValueError("Cannot invert a singular 3x3 matrix")

    a, b, c = value[0]
    d, e, f = value[1]
    g, h, i = value[2]
    adjugate = (
        (e * i - f * h, c * h - b * i, b * f - c * e),
        (f * g - d * i, a * i - c * g, c * d - a * f),
        (d * h - e * g, b * g - a * h, a * e - b * d),
    )
    return matrix_scale(adjugate, 1.0 / determinant)


def double_contraction(left: Matrix3, right: Matrix3) -> float:
    return sum(
        left[row][column] * right[row][column]
        for row in range(3)
        for column in range(3)
    )


def symmetrize(value: Matrix3) -> Matrix3:
    return matrix_scale(matrix_add(value, matrix_transpose(value)), 0.5)


def deviatoric(value: Matrix3) -> Matrix3:
    pressure_part = matrix_trace(value) / 3.0
    return tuple(
        tuple(
            value[row][column] - (pressure_part if row == column else 0.0)
            for column in range(3)
        )
        for row in range(3)
    )  # type: ignore[return-value]


def hydrostatic_stress(stress: Matrix3) -> float:
    """Return positive mean normal stress under a tension-positive convention."""

    return matrix_trace(stress) / 3.0


def von_mises_stress(stress: Matrix3) -> float:
    dev = deviatoric(symmetrize(stress))
    return sqrt(1.5 * double_contraction(dev, dev))


@dataclass(frozen=True, slots=True)
class Quaternion:
    """Hamilton quaternion ``w + x i + y j + z k``.

    Unit quaternions represent proper rotations. The rotations represented by
    ``q`` and ``-q`` are identical.
    """

    w: float
    x: float
    y: float
    z: float

    @classmethod
    def identity(cls) -> "Quaternion":
        return cls(1.0, 0.0, 0.0, 0.0)

    @classmethod
    def from_axis_angle(
        cls,
        axis: Sequence[float],
        angle_radians: float,
    ) -> "Quaternion":
        unit_axis = normalize_vector(axis)
        half_angle = 0.5 * float(angle_radians)
        scale = sin(half_angle)
        return cls(
            cos(half_angle),
            unit_axis[0] * scale,
            unit_axis[1] * scale,
            unit_axis[2] * scale,
        ).normalized()

    def norm_squared(self) -> float:
        return self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z

    def norm(self) -> float:
        return sqrt(self.norm_squared())

    def normalized(self) -> "Quaternion":
        norm = self.norm()
        if norm <= _EPS:
            raise ValueError("Cannot normalize a zero quaternion")
        return Quaternion(self.w / norm, self.x / norm, self.y / norm, self.z / norm)

    def conjugate(self) -> "Quaternion":
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def inverse(self) -> "Quaternion":
        norm_squared = self.norm_squared()
        if norm_squared <= _EPS:
            raise ValueError("Cannot invert a zero quaternion")
        conjugate = self.conjugate()
        return Quaternion(
            conjugate.w / norm_squared,
            conjugate.x / norm_squared,
            conjugate.y / norm_squared,
            conjugate.z / norm_squared,
        )

    def __mul__(self, other: "Quaternion") -> "Quaternion":
        if not isinstance(other, Quaternion):
            return NotImplemented
        return Quaternion(
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
        )

    def rotate_vector(self, vector: Sequence[float]) -> Vector3:
        unit = self.normalized()
        pure = Quaternion(0.0, *_vector3(vector))
        rotated = unit * pure * unit.conjugate()
        return rotated.x, rotated.y, rotated.z

    def to_rotation_matrix(self) -> Matrix3:
        q = self.normalized()
        w, x, y, z = q.w, q.x, q.y, q.z
        return (
            (
                1.0 - 2.0 * (y * y + z * z),
                2.0 * (x * y - z * w),
                2.0 * (x * z + y * w),
            ),
            (
                2.0 * (x * y + z * w),
                1.0 - 2.0 * (x * x + z * z),
                2.0 * (y * z - x * w),
            ),
            (
                2.0 * (x * z - y * w),
                2.0 * (y * z + x * w),
                1.0 - 2.0 * (x * x + y * y),
            ),
        )

    def angle_to(self, other: "Quaternion") -> float:
        """Return the shortest SO(3) rotation angle between two orientations."""

        relative = other.normalized() * self.normalized().conjugate()
        scalar = min(1.0, max(-1.0, abs(relative.w)))
        return 2.0 * acos(scalar)

    def is_unit(self, *, tolerance: float = 1.0e-10) -> bool:
        return isclose(self.norm_squared(), 1.0, abs_tol=tolerance)


def rotate_rank2(tensor: Matrix3, orientation: Quaternion) -> Matrix3:
    """Rotate a rank-2 tensor from crystal coordinates into lab coordinates."""

    rotation = orientation.to_rotation_matrix()
    return matrix_multiply(matrix_multiply(rotation, tensor), matrix_transpose(rotation))


def rotate_rank4(stiffness: Tensor4, orientation: Quaternion) -> Tensor4:
    """Rotate ``C_abcd`` into ``C_ijkl`` using four copies of ``R(q)``."""

    rotation = orientation.to_rotation_matrix()
    result = [[[[0.0 for _ in range(3)] for _ in range(3)] for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    total = 0.0
                    for a in range(3):
                        for b in range(3):
                            for c in range(3):
                                for d in range(3):
                                    total += (
                                        rotation[i][a]
                                        * rotation[j][b]
                                        * rotation[k][c]
                                        * rotation[l][d]
                                        * stiffness[a][b][c][d]
                                    )
                    result[i][j][k][l] = total
    return tuple(
        tuple(
            tuple(tuple(result[i][j][k][l] for l in range(3)) for k in range(3))
            for j in range(3)
        )
        for i in range(3)
    )


def hooke_stress(stiffness: Tensor4, strain: Matrix3) -> Matrix3:
    """Compute ``sigma_ij = C_ijkl epsilon_kl``."""

    symmetric_strain = symmetrize(strain)
    return tuple(
        tuple(
            sum(
                stiffness[i][j][k][l] * symmetric_strain[k][l]
                for k in range(3)
                for l in range(3)
            )
            for j in range(3)
        )
        for i in range(3)
    )  # type: ignore[return-value]


def elastic_energy_density(stress: Matrix3, strain: Matrix3) -> float:
    return 0.5 * double_contraction(symmetrize(stress), symmetrize(strain))


def resolved_shear_stress(
    stress: Matrix3,
    slip_direction: Sequence[float],
    plane_normal: Sequence[float],
) -> float:
    """Compute the Schmid resolved shear stress ``s · sigma · n``."""

    direction = normalize_vector(slip_direction)
    normal = normalize_vector(plane_normal)
    traction = matrix_vector_multiply(stress, normal)
    return vector_dot(direction, traction)


@dataclass(frozen=True, slots=True)
class CubicElasticity:
    """Three independent elastic constants of a cubic crystal."""

    c11: float
    c12: float
    c44: float

    def stability_margins(self) -> dict[str, float]:
        return {
            "c11_minus_c12": self.c11 - self.c12,
            "c11_plus_2c12": self.c11 + 2.0 * self.c12,
            "c44": self.c44,
        }

    def is_mechanically_stable(self) -> bool:
        return all(value > 0.0 for value in self.stability_margins().values())

    def to_tensor(self) -> Tensor4:
        values = [[[[0.0 for _ in range(3)] for _ in range(3)] for _ in range(3)] for _ in range(3)]
        for i in range(3):
            values[i][i][i][i] = float(self.c11)
            for j in range(3):
                if i == j:
                    continue
                values[i][i][j][j] = float(self.c12)
                values[i][j][i][j] = float(self.c44)
                values[i][j][j][i] = float(self.c44)
        return tuple(
            tuple(
                tuple(tuple(values[i][j][k][l] for l in range(3)) for k in range(3))
                for j in range(3)
            )
            for i in range(3)
        )

    def oriented_tensor(self, orientation: Quaternion) -> Tensor4:
        return rotate_rank4(self.to_tensor(), orientation)


@dataclass(frozen=True, slots=True)
class AffineTransform3D:
    """General affine map ``x -> M x + t``.

    ``compose(other)`` returns ``self ∘ other``.
    """

    linear: Matrix3
    translation: Vector3 = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "linear", matrix3(self.linear))
        object.__setattr__(self, "translation", _vector3(self.translation))

    @classmethod
    def identity(cls) -> "AffineTransform3D":
        return cls(identity_matrix())

    @classmethod
    def similarity(
        cls,
        orientation: Quaternion,
        *,
        scale: float = 1.0,
        translation: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> "AffineTransform3D":
        if abs(scale) <= _EPS:
            raise ValueError("A similarity scale must be non-zero")
        return cls(
            matrix_scale(orientation.to_rotation_matrix(), float(scale)),
            _vector3(translation),
        )

    @classmethod
    def crystal_map(
        cls,
        orientation: Quaternion,
        stretch: Matrix3,
        *,
        translation: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> "AffineTransform3D":
        """Build ``F = R(q) U`` from orientation and a user-supplied stretch."""

        return cls(
            matrix_multiply(orientation.to_rotation_matrix(), matrix3(stretch)),
            _vector3(translation),
        )

    def apply(self, point: Sequence[float]) -> Vector3:
        mapped = matrix_vector_multiply(self.linear, point)
        return tuple(mapped[index] + self.translation[index] for index in range(3))  # type: ignore[return-value]

    def compose(self, other: "AffineTransform3D") -> "AffineTransform3D":
        linear = matrix_multiply(self.linear, other.linear)
        shifted = matrix_vector_multiply(self.linear, other.translation)
        translation = tuple(
            shifted[index] + self.translation[index]
            for index in range(3)
        )
        return AffineTransform3D(linear, translation)  # type: ignore[arg-type]

    def inverse(self) -> "AffineTransform3D":
        inverse_linear = matrix_inverse(self.linear)
        inverse_translation = matrix_vector_multiply(
            inverse_linear,
            tuple(-component for component in self.translation),
        )
        return AffineTransform3D(inverse_linear, inverse_translation)

    def jacobian_determinant(self) -> float:
        return matrix_determinant(self.linear)


@dataclass(frozen=True, slots=True)
class CrystalState:
    """Minimal coupled crystal state for deterministic OAKBench experiments."""

    orientation: Quaternion
    deformation_gradient: Matrix3
    stress_crystal: Matrix3

    def __post_init__(self) -> None:
        object.__setattr__(self, "orientation", self.orientation.normalized())
        object.__setattr__(self, "deformation_gradient", matrix3(self.deformation_gradient))
        object.__setattr__(self, "stress_crystal", symmetrize(matrix3(self.stress_crystal)))

    @property
    def stress_lab(self) -> Matrix3:
        return rotate_rank2(self.stress_crystal, self.orientation)

    def invariants(self) -> dict[str, float]:
        stress = self.stress_lab
        return {
            "orientation_norm": self.orientation.norm(),
            "deformation_jacobian": matrix_determinant(self.deformation_gradient),
            "stress_trace": matrix_trace(stress),
            "stress_determinant": matrix_determinant(stress),
            "hydrostatic_stress": hydrostatic_stress(stress),
            "von_mises_stress": von_mises_stress(stress),
        }


def degrees(value: float) -> float:
    return float(value) * 180.0 / pi


def radians(value: float) -> float:
    return float(value) * pi / 180.0
