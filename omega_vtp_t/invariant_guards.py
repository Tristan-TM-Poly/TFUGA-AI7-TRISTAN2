"""Invariant guards for Ω-DE-TensorProd.

Invariant guards are reusable OAK checks for conservation, positivity, boundary
conditions, and energy-like quantities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class InvariantCheck:
    name: str
    expected: str
    measured_error: float
    tolerance: float
    passed: bool


@dataclass(frozen=True)
class InvariantReport:
    checks: Tuple[InvariantCheck, ...]
    oak_status: str


def l2_energy(u: Sequence[float] | np.ndarray, dx: float = 1.0) -> float:
    """Discrete L2 energy integral: int u^2 dx."""

    if dx <= 0:
        raise ValueError("dx must be > 0")
    arr = np.asarray(u, dtype=float)
    return float(np.sum(arr * arr) * dx)


def positivity_error(u: Sequence[float] | np.ndarray) -> float:
    """Magnitude of negative violation for a nonnegative field/state."""

    arr = np.asarray(u, dtype=float)
    return float(max(0.0, -np.min(arr))) if arr.size else 0.0


def conservation_check(
    name: str,
    before: float,
    after: float,
    *,
    tolerance: float,
) -> InvariantCheck:
    """Check conservation of a scalar quantity."""

    err = abs(float(after) - float(before))
    return InvariantCheck(name, "conserved", err, tolerance, err <= tolerance)


def monotone_decrease_check(
    name: str,
    before: float,
    after: float,
    *,
    tolerance: float = 0.0,
) -> InvariantCheck:
    """Check that a scalar quantity did not increase beyond tolerance."""

    err = max(0.0, float(after) - float(before) - tolerance)
    return InvariantCheck(name, "nonincreasing", err, tolerance, err <= tolerance)


def positivity_check(
    u: Sequence[float] | np.ndarray,
    *,
    tolerance: float = 0.0,
) -> InvariantCheck:
    """Check nonnegativity of a state or field."""

    err = positivity_error(u)
    return InvariantCheck("positivity", "nonnegative", err, tolerance, err <= tolerance)


def custom_invariant_check(
    name: str,
    invariant: Callable[[np.ndarray], float],
    before_state: Sequence[float] | np.ndarray,
    after_state: Sequence[float] | np.ndarray,
    *,
    expected: str = "conserved",
    tolerance: float = 1e-8,
) -> InvariantCheck:
    """Check a user-provided invariant function."""

    before = float(invariant(np.asarray(before_state, dtype=float)))
    after = float(invariant(np.asarray(after_state, dtype=float)))
    if expected == "conserved":
        err = abs(after - before)
        passed = err <= tolerance
    elif expected == "nonincreasing":
        err = max(0.0, after - before - tolerance)
        passed = err <= tolerance
    else:
        raise ValueError("expected must be 'conserved' or 'nonincreasing'")
    return InvariantCheck(name, expected, float(err), tolerance, bool(passed))


def invariant_report(checks: Sequence[InvariantCheck]) -> InvariantReport:
    """Aggregate invariant checks."""

    items = tuple(checks)
    if not items:
        return InvariantReport(tuple(), "empty")
    if all(c.passed for c in items):
        status = "certified"
    elif any(c.measured_error > 10 * max(c.tolerance, np.finfo(float).eps) for c in items):
        status = "invariant_violation_high"
    else:
        status = "invariant_watch"
    return InvariantReport(items, status)
