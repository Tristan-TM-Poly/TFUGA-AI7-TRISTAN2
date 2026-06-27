"""Small Reed-Solomon erasure code over GF(256) for Ω-ECC-T.

This module is OAK-safe by design: it implements an auditable erasure-recovery
baseline, not a full industrial Reed-Solomon stack with unknown-error decoding.
Unknown symbol errors must be handled by integrity checks or a future syndrome
solver, not silently treated as erasures.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

PRIMITIVE_POLY = 0x11D
FIELD_SIZE = 256
FIELD_ORDER = 255


def _build_tables() -> tuple[list[int], list[int]]:
    exp = [0] * (FIELD_ORDER * 2)
    log = [0] * FIELD_SIZE
    x = 1
    for i in range(FIELD_ORDER):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & FIELD_SIZE:
            x ^= PRIMITIVE_POLY
    for i in range(FIELD_ORDER, FIELD_ORDER * 2):
        exp[i] = exp[i - FIELD_ORDER]
    return exp, log


GF_EXP, GF_LOG = _build_tables()


def gf_add(a: int, b: int) -> int:
    return int(a) ^ int(b)


def gf_mul(a: int, b: int) -> int:
    a = int(a)
    b = int(b)
    if not 0 <= a < FIELD_SIZE or not 0 <= b < FIELD_SIZE:
        raise ValueError("GF(256) values must be in [0, 255]")
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]


def gf_pow(a: int, power: int) -> int:
    a = int(a)
    if not 0 <= a < FIELD_SIZE:
        raise ValueError("GF(256) values must be in [0, 255]")
    if power < 0:
        return gf_pow(gf_inv(a), -power)
    if a == 0:
        return 0 if power > 0 else 1
    return GF_EXP[(GF_LOG[a] * power) % FIELD_ORDER]


def gf_inv(a: int) -> int:
    a = int(a)
    if not 0 < a < FIELD_SIZE:
        raise ZeroDivisionError("0 has no multiplicative inverse in GF(256)")
    return GF_EXP[FIELD_ORDER - GF_LOG[a]]


def gf_div(a: int, b: int) -> int:
    a = int(a)
    b = int(b)
    if b == 0:
        raise ZeroDivisionError("division by zero in GF(256)")
    if a == 0:
        return 0
    return GF_EXP[(GF_LOG[a] - GF_LOG[b]) % FIELD_ORDER]


def _byte(value: int, name: str = "value") -> int:
    value = int(value)
    if not 0 <= value < FIELD_SIZE:
        raise ValueError(f"{name} must be a byte in [0, 255]")
    return value


def _bytes(values: Sequence[int], name: str = "values") -> List[int]:
    return [_byte(value, name) for value in values]


def poly_trim(poly: Sequence[int]) -> List[int]:
    out = _bytes(poly, "poly")
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def poly_add(a: Sequence[int], b: Sequence[int]) -> List[int]:
    left = _bytes(a, "left")
    right = _bytes(b, "right")
    width = max(len(left), len(right))
    out = [0] * width
    for idx in range(width):
        x = left[idx] if idx < len(left) else 0
        y = right[idx] if idx < len(right) else 0
        out[idx] = gf_add(x, y)
    return poly_trim(out)


def poly_scale(poly: Sequence[int], scalar: int) -> List[int]:
    scalar = _byte(scalar, "scalar")
    return poly_trim([gf_mul(coef, scalar) for coef in _bytes(poly, "poly")])


def poly_mul(a: Sequence[int], b: Sequence[int]) -> List[int]:
    left = _bytes(a, "left")
    right = _bytes(b, "right")
    out = [0] * (len(left) + len(right) - 1)
    for i, x in enumerate(left):
        for j, y in enumerate(right):
            out[i + j] ^= gf_mul(x, y)
    return poly_trim(out)


def poly_eval(poly: Sequence[int], x: int) -> int:
    x = _byte(x, "x")
    acc = 0
    for coef in reversed(_bytes(poly, "poly")):
        acc = gf_mul(acc, x) ^ coef
    return acc


def lagrange_interpolate(points: Sequence[Tuple[int, int]], degree_limit: int) -> List[int]:
    """Interpolate a polynomial from points over GF(256).

    Coefficients are returned low-to-high. ``degree_limit`` is the number of
    coefficients to return; for a k-symbol RS message, this is k.
    """
    if degree_limit <= 0:
        raise ValueError("degree_limit must be positive")
    if len(points) < degree_limit:
        raise ValueError("not enough points to interpolate the requested degree")
    selected = [(_byte(x, "x"), _byte(y, "y")) for x, y in points[:degree_limit]]
    xs = [x for x, _ in selected]
    if len(set(xs)) != len(xs):
        raise ValueError("interpolation points must have distinct x values")

    result = [0]
    for i, (xi, yi) in enumerate(selected):
        basis = [1]
        denom = 1
        for j, (xj, _) in enumerate(selected):
            if i == j:
                continue
            basis = poly_mul(basis, [xj, 1])  # x - xj == x + xj in characteristic 2.
            denom = gf_mul(denom, xi ^ xj)
        scaled = poly_scale(basis, gf_div(yi, denom))
        result = poly_add(result, scaled)

    result = result[:degree_limit]
    if len(result) < degree_limit:
        result.extend([0] * (degree_limit - len(result)))
    return result


@dataclass(frozen=True)
class RSErasureDecodeResult:
    message: Optional[List[int]]
    codeword: Optional[List[int]]
    known_symbols: int
    erased_positions: List[int]
    status: str
    oak_trust: float

    @property
    def recovered(self) -> bool:
        return self.status == "recovered"


class ReedSolomonErasureCode:
    """Evaluation-form Reed-Solomon erasure code over GF(256).

    A k-byte message is interpreted as polynomial coefficients. The n-symbol
    codeword is the polynomial evaluated at x=1..n. Any k known symbols can
    recover the message when erasure positions are known.
    """

    def __init__(self, n: int, k: int, name: str = "RS_GF256_erasure") -> None:
        n = int(n)
        k = int(k)
        if not 1 <= k <= n <= FIELD_ORDER:
            raise ValueError("Reed-Solomon parameters must satisfy 1 <= k <= n <= 255")
        self.n = n
        self.k = k
        self.name = name
        self.evaluation_points = list(range(1, n + 1))

    def rate(self) -> float:
        return self.k / self.n

    def max_erasures(self) -> int:
        return self.n - self.k

    def encode(self, message: Sequence[int]) -> List[int]:
        coefficients = _bytes(message, "message")
        if len(coefficients) != self.k:
            raise ValueError(f"message must contain exactly {self.k} symbols")
        return [poly_eval(coefficients, x) for x in self.evaluation_points]

    def decode_erasures(self, received: Sequence[Optional[int]]) -> RSErasureDecodeResult:
        if len(received) != self.n:
            raise ValueError(f"received word must contain exactly {self.n} symbols")
        erased = [idx for idx, value in enumerate(received) if value is None]
        known: List[Tuple[int, int]] = []
        for idx, value in enumerate(received):
            if value is not None:
                known.append((self.evaluation_points[idx], _byte(value, "received symbol")))
        if len(known) < self.k:
            return RSErasureDecodeResult(
                message=None,
                codeword=None,
                known_symbols=len(known),
                erased_positions=erased,
                status="insufficient_known_symbols",
                oak_trust=0.0,
            )
        message = lagrange_interpolate(known, self.k)
        codeword = self.encode(message)
        for idx, value in enumerate(received):
            if value is not None and codeword[idx] != value:
                return RSErasureDecodeResult(
                    message=message,
                    codeword=codeword,
                    known_symbols=len(known),
                    erased_positions=erased,
                    status="inconsistent_known_symbols_oak_reject",
                    oak_trust=0.0,
                )
        return RSErasureDecodeResult(
            message=message,
            codeword=codeword,
            known_symbols=len(known),
            erased_positions=erased,
            status="recovered",
            oak_trust=1.0,
        )


def erase_positions(codeword: Sequence[int], positions: Iterable[int]) -> List[Optional[int]]:
    out: List[Optional[int]] = [_byte(value, "codeword") for value in codeword]
    for pos in positions:
        idx = int(pos)
        if not 0 <= idx < len(out):
            raise IndexError("erasure position out of range")
        out[idx] = None
    return out
