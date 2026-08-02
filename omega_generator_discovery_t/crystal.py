"""Quaternion holonomy and crystal-loop diagnostics."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import acos, sqrt
from typing import Iterable, Sequence

QuaternionTuple = tuple[float, float, float, float]
_EPS = 1.0e-12


def normalize_quaternion(value: Sequence[float]) -> QuaternionTuple:
    if len(value) != 4:
        raise ValueError("Quaternion requires four components")
    q = tuple(float(x) for x in value)
    norm = sqrt(sum(x*x for x in q))
    if norm <= _EPS:
        raise ValueError("Cannot normalize a zero quaternion")
    return tuple(x/norm for x in q)  # type: ignore[return-value]


def conjugate(value: Sequence[float]) -> QuaternionTuple:
    w, x, y, z = normalize_quaternion(value)
    return (w, -x, -y, -z)


def quaternion_multiply(left: Sequence[float], right: Sequence[float]) -> QuaternionTuple:
    aw, ax, ay, az = normalize_quaternion(left)
    bw, bx, by, bz = normalize_quaternion(right)
    return normalize_quaternion((
        aw*bw-ax*bx-ay*by-az*bz,
        aw*bx+ax*bw+ay*bz-az*by,
        aw*by-ax*bz+ay*bw+az*bx,
        aw*bz+ax*by-ay*bx+az*bw,
    ))


def relative_orientation(source: Sequence[float], target: Sequence[float]) -> QuaternionTuple:
    return quaternion_multiply(target, conjugate(source))


@dataclass(frozen=True, slots=True)
class HolonomyReport:
    loop_quaternion: QuaternionTuple
    residual_angle_radians: float
    frustration_score: float
    status: str = "orientation_loop_residual_not_dislocation_density"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def crystal_holonomy(orientations: Iterable[Sequence[float]]) -> HolonomyReport:
    values = tuple(normalize_quaternion(q) for q in orientations)
    if len(values) < 3:
        raise ValueError("A loop requires at least three orientations")
    product: QuaternionTuple = (1.0, 0.0, 0.0, 0.0)
    for index in range(len(values)):
        delta = relative_orientation(values[index], values[(index+1) % len(values)])
        product = quaternion_multiply(delta, product)
    angle = 2.0*acos(min(1.0, abs(product[0])))
    return HolonomyReport(product, angle, min(1.0, angle/3.141592653589793))
