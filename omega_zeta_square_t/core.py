"""Exact geometry and optional analytic functions for Ω-ZETA-SQUARE-T∞.

The canonical coordinate is
    w = s - 1/2,
    u = w**2.

The geometry functions are dependency-free and exact up to ordinary floating/
complex arithmetic. Analytic evaluation helpers use mpmath only when called.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Tuple


@dataclass(frozen=True)
class SquareCoordinate:
    """Centered-square image together with decoded squared coordinates."""

    u: complex
    delta_squared: float
    gamma_squared: float

    @property
    def rh_defect(self) -> float:
        return self.delta_squared


def centered_square(s: complex) -> complex:
    """Map s to u=(s-1/2)^2, quotienting w <-> -w."""

    return (complex(s) - 0.5) ** 2


def decode_square(u: complex) -> SquareCoordinate:
    """Recover delta^2 and gamma^2 from u=(delta+i gamma)^2.

    For u=x+iy,
        delta^2 = (|u|+x)/2,
        gamma^2 = (|u|-x)/2.

    Tiny negative roundoff is clamped to zero.
    """

    z = complex(u)
    r = abs(z)
    delta2 = 0.5 * (r + z.real)
    gamma2 = 0.5 * (r - z.real)
    eps = 1e-15 * max(1.0, r)
    if -eps < delta2 < 0.0:
        delta2 = 0.0
    if -eps < gamma2 < 0.0:
        gamma2 = 0.0
    return SquareCoordinate(z, float(delta2), float(gamma2))


def rh_defect(u: complex) -> float:
    """Exact centered horizontal-distance squared encoded by u."""

    return decode_square(u).delta_squared


def height_squared(u: complex) -> float:
    """Return gamma^2 encoded by u."""

    return decode_square(u).gamma_squared


def strip_boundary(y: float) -> float:
    """x-coordinate of the image of Re(s)=0 or Re(s)=1.

    Both strip boundaries map to x = 1/4 - y^2.
    """

    y = float(y)
    return 0.25 - y * y


def in_centered_critical_strip(u: complex, tol: float = 1e-12) -> bool:
    """Test the parabolic image of 0 <= Re(s) <= 1.

    The image is x <= 1/4 - y^2.
    """

    z = complex(u)
    return z.real <= strip_boundary(z.imag) + float(tol)


def trivial_zero_image(n: int) -> float:
    """Image of the trivial zeta zero s=-2n under the centered square.

    u_n = (-2n-1/2)^2 = (2n+1/2)^2 > 0.
    """

    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be a positive integer")
    return (2.0 * n + 0.5) ** 2


def nontrivial_zero_image(beta: float, gamma: float) -> complex:
    """Image a candidate nontrivial zero beta+i*gamma."""

    beta = float(beta)
    gamma = float(gamma)
    if not (isfinite(beta) and isfinite(gamma)):
        raise ValueError("beta and gamma must be finite")
    return complex(beta - 0.5, gamma) ** 2


def xi(s: complex, dps: int = 50):
    """Evaluate Riemann's completed xi(s) with mpmath.

    This helper is optional; importing the package does not require mpmath.
    """

    try:
        import mpmath as mp
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("xi evaluation requires optional dependency 'mpmath'") from exc
    with mp.workdps(int(dps)):
        z = mp.mpc(s)
        return mp.mpf("0.5") * z * (z - 1) * mp.power(mp.pi, -z / 2) * mp.gamma(z / 2) * mp.zeta(z)


def theta(u: complex, dps: int = 50):
    """Evaluate Theta(u)=xi(1/2+sqrt(u)).

    The xi functional symmetry makes the result independent of the sign chosen
    for sqrt(u), modulo numerical error.
    """

    try:
        import mpmath as mp
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("theta evaluation requires optional dependency 'mpmath'") from exc
    with mp.workdps(int(dps)):
        z = mp.mpc(u)
        root = mp.sqrt(z)
        return xi(mp.mpf("0.5") + root, dps=dps)


def zeta_square(u: complex, dps: int = 50):
    """Evaluate the branch-independent unified zeta-square object away from u=1/4.

        Z_square(u) = (u-1/4) zeta(1/2+sqrt(u)) zeta(1/2-sqrt(u)).

    The removable singularity at u=1/4 is intentionally not special-cased;
    callers doing certified work should evaluate the analytic continuation.
    """

    try:
        import mpmath as mp
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("zeta_square evaluation requires optional dependency 'mpmath'") from exc
    with mp.workdps(int(dps)):
        z = mp.mpc(u)
        if abs(z - mp.mpf("0.25")) == 0:
            raise ValueError("u=1/4 is removable; use analytic continuation for certified evaluation")
        root = mp.sqrt(z)
        return (z - mp.mpf("0.25")) * mp.zeta(mp.mpf("0.5") + root) * mp.zeta(mp.mpf("0.5") - root)


def parabolic_tomography(beta: float, gamma: float, b: float) -> complex:
    """Moving-center image around c_b=1/2+i b.

    For delta=beta-1/2,
        u_b = delta^2-(gamma-b)^2 + 2 i delta (gamma-b).
    On RH (delta=0), the full trajectory stays on the non-positive real axis.
    """

    return complex(float(beta) - 0.5, float(gamma) - float(b)) ** 2


def parabolic_vertex_from_beta(beta: float) -> float:
    """Vertex x-coordinate delta^2 of the b-tomography parabola."""

    delta = float(beta) - 0.5
    return delta * delta


def square_invariants(s: complex) -> Tuple[complex, float, float]:
    """Convenience helper returning (u, delta^2, gamma^2)."""

    u = centered_square(s)
    decoded = decode_square(u)
    return u, decoded.delta_squared, decoded.gamma_squared
