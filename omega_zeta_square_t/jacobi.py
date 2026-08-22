"""Jacobi/orthogonal-polynomial reconstruction from inverse moments.

The input convention is p_k = sum lambda_j^k. We use m_k=p_{k+1}, which is
the moment sequence of the positive measure sum lambda_j delta_{lambda_j}
when RH/spectral positivity assumptions hold. The algebra below is formal and
works exactly for rational inputs; its spectral interpretation is conditional.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class JacobiRecurrence(Generic[T]):
    alpha: tuple[T, ...]
    beta: tuple[T, ...]
    monic_polynomials: tuple[tuple[T, ...], ...]
    epistemic_status: str = "FORMAL_MOMENT_RECONSTRUCTION"
    proves_rh: bool = False


def _poly_add(a: Sequence[T], b: Sequence[T], scale_b=1) -> list[T]:
    n = max(len(a), len(b))
    out = [0 for _ in range(n)]
    for i, x in enumerate(a):
        out[i] += x
    for i, x in enumerate(b):
        out[i] += scale_b * x
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def _poly_scale(a: Sequence[T], c: T) -> list[T]:
    return [c * x for x in a]


def _x_times(a: Sequence[T]) -> list[T]:
    return [0] + list(a)


def _inner(a: Sequence[T], b: Sequence[T], moments: Sequence[T]) -> T:
    value = 0
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            idx = i + j
            if idx >= len(moments):
                raise ValueError("insufficient moments for requested Jacobi reconstruction")
            value += ai * bj * moments[idx]
    return value


def jacobi_recurrence_from_inverse_moments(
    inverse_moments: Sequence[T], size: int
) -> JacobiRecurrence[T]:
    """Return monic Jacobi recurrence coefficients alpha_n, beta_n.

    `size` yields alpha_0..alpha_(size-1) and beta_1..beta_(size-1).
    At least 2*size inverse moments p_1..p_(2*size) are required.
    Positive norms are required; rank-deficient finite measures should request a
    smaller size.
    """

    if not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    if len(inverse_moments) < 2 * size:
        raise ValueError(f"need at least {2 * size} inverse moments")
    moments = list(inverse_moments[: 2 * size])  # m_k = p_(k+1)

    p_prev: list[T] = [0]
    p: list[T] = [1]
    h = _inner(p, p, moments)
    if h <= 0:
        raise ValueError("non-positive initial moment norm")

    beta_current = 0
    alphas: list[T] = []
    betas: list[T] = []
    polys: list[tuple[T, ...]] = [tuple(p)]

    for n in range(size):
        alpha = _inner(_x_times(p), p, moments) / h
        alphas.append(alpha)
        if n == size - 1:
            break

        p_next = _poly_add(_x_times(p), _poly_scale(p, alpha), scale_b=-1)
        if n > 0:
            p_next = _poly_add(p_next, _poly_scale(p_prev, beta_current), scale_b=-1)
        h_next = _inner(p_next, p_next, moments)
        if h_next <= 0:
            raise ValueError("moment functional is not positive definite at requested size")
        beta_next = h_next / h
        betas.append(beta_next)
        p_prev, p = p, p_next
        h = h_next
        beta_current = beta_next
        polys.append(tuple(p))

    return JacobiRecurrence(
        alpha=tuple(alphas), beta=tuple(betas), monic_polynomials=tuple(polys)
    )


def jacobi_characteristic_polynomial(recurrence: JacobiRecurrence[T]) -> tuple[T, ...]:
    """Return det(xI-J) coefficients in ascending powers of x.

    For monic Jacobi data, D_0=1, D_1=x-alpha_0 and
    D_{n+1}=(x-alpha_n)D_n-beta_n D_{n-1}.
    """

    if not recurrence.alpha:
        raise ValueError("recurrence must contain at least one alpha")
    d_prev: list[T] = [1]
    d: list[T] = [-recurrence.alpha[0], 1]
    for n in range(1, len(recurrence.alpha)):
        term = _poly_add(_x_times(d), _poly_scale(d, recurrence.alpha[n]), scale_b=-1)
        term = _poly_add(term, _poly_scale(d_prev, recurrence.beta[n - 1]), scale_b=-1)
        d_prev, d = d, term
    return tuple(d)
