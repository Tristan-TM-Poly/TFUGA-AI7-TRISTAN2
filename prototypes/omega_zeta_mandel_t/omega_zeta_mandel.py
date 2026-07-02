"""Omega Zeta-Mandel-Tristan prototype.

This module is intentionally small and dependency-free.  It provides:
- a classical Mandelbrot escape kernel with CVCD-style invariants;
- an eta-series approximation of the Riemann zeta function for exploratory orbits;
- a generic Cayley-Dickson product up to sedenions;
- a sedenion Mandelbrot slice kernel with explicit OAK metadata.

OAK guardrail: this is a numerical exploration scaffold, not a proof of the
Riemann hypothesis or any new theorem.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable, List, Sequence, Tuple


NumberVector = Tuple[float, ...]


@dataclass(frozen=True)
class OAKStatus:
    """Minimal epistemic status record for a numerical experiment."""

    claim_status: str
    algebra: str
    projection: str
    norm: str
    precision_note: str
    parenthesization: str
    oak_warning: str = (
        "visualization/numerical pattern only; not a proof; compare against "
        "baseline, resolution, precision, projection, norm, and parenthesization"
    )


@dataclass(frozen=True)
class OrbitCVCD:
    """Compact CVCD signature for escape-time dynamics."""

    escape_iter: int
    max_radius: float
    final_radius: float
    mean_radius: float
    radius_variance: float
    lyapunov_proxy: float
    compressed_signature: str
    uncertainty_u2: float
    oak: OAKStatus

    def to_dict(self) -> dict:
        payload = asdict(self)
        return payload


def _variance(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


def symbolic_radius_signature(radii: Sequence[float], bins: Sequence[float] = (0.5, 1.0, 2.0, 4.0)) -> str:
    """Compress an orbit's radii into a symbolic multi-scale signature."""

    symbols = "ABCDE"
    out: List[str] = []
    for radius in radii:
        idx = 0
        while idx < len(bins) and radius > bins[idx]:
            idx += 1
        out.append(symbols[idx])
    if not out:
        return ""
    rle: List[str] = []
    current = out[0]
    count = 1
    for symbol in out[1:]:
        if symbol == current:
            count += 1
        else:
            rle.append(f"{current}{count}")
            current = symbol
            count = 1
    rle.append(f"{current}{count}")
    return "".join(rle)


def mandelbrot_cvcd(c: complex, max_iter: int = 256, escape_radius: float = 2.0) -> OrbitCVCD:
    """Return a CVCD-style signature for the classical Mandelbrot map."""

    z = 0j
    radii: List[float] = []
    log_derivative_terms: List[float] = []

    escape_iter = max_iter
    for n in range(1, max_iter + 1):
        z = z * z + c
        radius = abs(z)
        radii.append(radius)
        if radius > 1e-12:
            log_derivative_terms.append(math.log(max(2.0 * radius, 1e-12)))
        if radius > escape_radius:
            escape_iter = n
            break

    mean_radius = sum(radii) / len(radii) if radii else 0.0
    lyapunov_proxy = (
        sum(log_derivative_terms) / len(log_derivative_terms)
        if log_derivative_terms
        else float("-inf")
    )
    uncertainty_u2 = min(1.0, 1.0 / max(1, len(radii)) + abs(escape_radius - 2.0) * 0.05)

    return OrbitCVCD(
        escape_iter=escape_iter,
        max_radius=max(radii) if radii else 0.0,
        final_radius=radii[-1] if radii else 0.0,
        mean_radius=mean_radius,
        radius_variance=_variance(radii),
        lyapunov_proxy=lyapunov_proxy,
        compressed_signature=symbolic_radius_signature(radii),
        uncertainty_u2=uncertainty_u2,
        oak=OAKStatus(
            claim_status="numerical visualization / baseline kernel",
            algebra="C",
            projection="identity complex plane",
            norm="complex modulus",
            precision_note="Python double precision complex arithmetic",
            parenthesization="z_next = (z * z) + c",
        ),
    )


def riemann_zeta_eta(s: complex, terms: int = 400) -> complex:
    """Approximate zeta(s) via the Dirichlet eta relation.

    eta(s) = sum_{n>=1} (-1)^(n-1) / n^s
    zeta(s) = eta(s) / (1 - 2^(1-s))

    This is for exploratory dynamics. It is not a high-precision zeta engine.
    Avoid s near the pole at 1 and compare with mpmath or Arb for serious work.
    """

    denominator = 1.0 - 2.0 ** (1.0 - s)
    if abs(denominator) < 1e-10:
        raise ValueError("eta-to-zeta denominator is too small near this point")

    eta = 0j
    for n in range(1, terms + 1):
        sign = 1.0 if n % 2 else -1.0
        eta += sign / (n ** s)
    return eta / denominator


def zeta_orbit_cvcd(s0: complex, c: complex = 0j, max_iter: int = 64, terms: int = 200, escape_radius: float = 32.0) -> OrbitCVCD:
    """Iterate s_{n+1} = zeta(s_n) + c and return a CVCD signature."""

    s = s0
    radii: List[float] = []
    escape_iter = max_iter

    for n in range(1, max_iter + 1):
        try:
            s = riemann_zeta_eta(s, terms=terms) + c
        except (OverflowError, ZeroDivisionError, ValueError):
            escape_iter = n
            radii.append(float("inf"))
            break
        radius = abs(s)
        radii.append(radius)
        if not math.isfinite(radius) or radius > escape_radius:
            escape_iter = n
            break

    finite_radii = [r for r in radii if math.isfinite(r)]
    mean_radius = sum(finite_radii) / len(finite_radii) if finite_radii else float("inf")
    uncertainty_u2 = min(1.0, 0.25 + 1.0 / max(1, terms) + 1.0 / max(1, len(finite_radii)))

    return OrbitCVCD(
        escape_iter=escape_iter,
        max_radius=max(finite_radii) if finite_radii else float("inf"),
        final_radius=radii[-1] if radii else 0.0,
        mean_radius=mean_radius,
        radius_variance=_variance(finite_radii),
        lyapunov_proxy=float("nan"),
        compressed_signature=symbolic_radius_signature(finite_radii),
        uncertainty_u2=uncertainty_u2,
        oak=OAKStatus(
            claim_status="exploratory zeta orbit; not a theorem",
            algebra="C",
            projection="identity complex plane",
            norm="complex modulus",
            precision_note=f"eta-series truncation terms={terms}; compare to validated zeta libraries",
            parenthesization="s_next = zeta_eta(s) + c",
        ),
    )


def _split_cd(x: Sequence[float]) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
    half = len(x) // 2
    return tuple(x[:half]), tuple(x[half:])


def cd_conjugate(x: Sequence[float]) -> NumberVector:
    """Cayley-Dickson conjugate."""

    if len(x) == 1:
        return (x[0],)
    a, b = _split_cd(x)
    return cd_conjugate(a) + tuple(-v for v in b)


def cd_add(x: Sequence[float], y: Sequence[float]) -> NumberVector:
    if len(x) != len(y):
        raise ValueError("Cayley-Dickson vectors must have the same dimension")
    return tuple(a + b for a, b in zip(x, y))


def cd_mul(x: Sequence[float], y: Sequence[float]) -> NumberVector:
    """Generic Cayley-Dickson product.

    For pairs (a,b)(c,d) = (ac - conjugate(d)b, da + b conjugate(c)).
    Dimensions must be powers of two.
    """

    if len(x) != len(y):
        raise ValueError("Cayley-Dickson vectors must have the same dimension")
    if len(x) == 1:
        return (x[0] * y[0],)
    if len(x) & (len(x) - 1):
        raise ValueError("dimension must be a power of two")

    a, b = _split_cd(x)
    c, d = _split_cd(y)

    ac = cd_mul(a, c)
    d_conj_b = cd_mul(cd_conjugate(d), b)
    left = tuple(u - v for u, v in zip(ac, d_conj_b))

    da = cd_mul(d, a)
    b_c_conj = cd_mul(b, cd_conjugate(c))
    right = tuple(u + v for u, v in zip(da, b_c_conj))

    return left + right


def cd_norm(x: Sequence[float]) -> float:
    return math.sqrt(sum(v * v for v in x))


def basis_vector(dim: int, index: int, value: float = 1.0) -> NumberVector:
    if not 0 <= index < dim:
        raise ValueError("basis index out of range")
    return tuple(value if i == index else 0.0 for i in range(dim))


def sedenion_mandelbrot_cvcd(c: Sequence[float], max_iter: int = 64, escape_radius: float = 4.0) -> OrbitCVCD:
    """Escape kernel for Z_{n+1} = Z_n^2 + C in 16-D sedenions."""

    if len(c) != 16:
        raise ValueError("sedenion C must have 16 components")

    z: NumberVector = (0.0,) * 16
    c_tuple: NumberVector = tuple(float(v) for v in c)
    radii: List[float] = []
    escape_iter = max_iter

    for n in range(1, max_iter + 1):
        z = cd_add(cd_mul(z, z), c_tuple)
        radius = cd_norm(z)
        radii.append(radius)
        if radius > escape_radius:
            escape_iter = n
            break

    mean_radius = sum(radii) / len(radii) if radii else 0.0
    uncertainty_u2 = min(1.0, 0.20 + 1.0 / max(1, len(radii)))

    return OrbitCVCD(
        escape_iter=escape_iter,
        max_radius=max(radii) if radii else 0.0,
        final_radius=radii[-1] if radii else 0.0,
        mean_radius=mean_radius,
        radius_variance=_variance(radii),
        lyapunov_proxy=float("nan"),
        compressed_signature=symbolic_radius_signature(radii),
        uncertainty_u2=uncertainty_u2,
        oak=OAKStatus(
            claim_status="sedenion numerical slice; projection artifact risk high",
            algebra="Sedenions / Cayley-Dickson dim=16",
            projection="caller-defined slice in R^16",
            norm="Euclidean component norm",
            precision_note="Python float; zero-divisor risk must be audited",
            parenthesization="Z_next = (Z * Z) + C using fixed Cayley-Dickson recursion",
        ),
    )


def zero_divisor_risk_probe(x: Sequence[float], probes: Iterable[Sequence[float]] | None = None) -> float:
    """Crude zero-divisor proximity probe.

    Returns min ||x*y||/(||x|| ||y||) over deterministic basis-pair probes.
    Smaller values indicate higher annihilation/pseudo-stability risk.

    This is a probe, not a complete zero-divisor detector.
    """

    x_norm = cd_norm(x)
    if x_norm == 0:
        return 0.0

    dim = len(x)
    if probes is None:
        generated: List[NumberVector] = []
        for i in range(dim):
            generated.append(basis_vector(dim, i))
        for i in range(0, dim - 1, 2):
            generated.append(tuple(
                (1.0 if j == i else -1.0 if j == i + 1 else 0.0)
                for j in range(dim)
            ))
        probes = generated

    best = float("inf")
    for y in probes:
        y_tuple = tuple(float(v) for v in y)
        y_norm = cd_norm(y_tuple)
        if y_norm == 0:
            continue
        score = cd_norm(cd_mul(x, y_tuple)) / (x_norm * y_norm)
        best = min(best, score)
    return best


def demo_manifest() -> dict:
    """Small deterministic demo payload for README and tests."""

    classic = mandelbrot_cvcd(-0.75 + 0.1j, max_iter=128)
    zeta = zeta_orbit_cvcd(0.5 + 14.134725j, max_iter=8, terms=80)
    c = cd_add(basis_vector(16, 1, -0.4), basis_vector(16, 8, 0.2))
    sedenion = sedenion_mandelbrot_cvcd(c, max_iter=32)
    return {
        "classic_mandelbrot": classic.to_dict(),
        "zeta_orbit": zeta.to_dict(),
        "sedenion_slice": sedenion.to_dict(),
        "zero_divisor_risk_probe": zero_divisor_risk_probe(c),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo_manifest(), indent=2, sort_keys=True))
