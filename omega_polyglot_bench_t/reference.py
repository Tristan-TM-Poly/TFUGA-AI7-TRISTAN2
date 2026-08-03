"""Readable Python oracle for cross-language conformance."""

from __future__ import annotations

from collections.abc import Sequence


def vector_affine_python(
    x: Sequence[float],
    y: Sequence[float],
    scalar: float,
) -> list[float]:
    """Return ``scalar * x + y`` with strict shape validation.

    This intentionally uses a plain Python loop. It is the behavioral oracle,
    not a claim that Python cannot be accelerated through NumPy, Numba, JAX,
    PyTorch, or another specialized implementation.
    """

    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    return [scalar * float(xi) + float(yi) for xi, yi in zip(x, y, strict=True)]
