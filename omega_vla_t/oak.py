"""OAK verification reports for Ω-VLA-T∞ operators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from .core import LinearOperator


@dataclass(frozen=True)
class OAKCheck:
    name: str
    passed: bool
    value: float | int | str | None
    threshold: float | None
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "value": self.value,
            "threshold": self.threshold,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class OAKReport:
    operator: str
    status: str
    checks: tuple[OAKCheck, ...]
    scientific_validation_claimed: bool = False
    theorem_claimed: bool = False

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator": self.operator,
            "status": self.status,
            "passed": self.passed,
            "checks": [check.to_dict() for check in self.checks],
            "scientific_validation_claimed": self.scientific_validation_claimed,
            "theorem_claimed": self.theorem_claimed,
        }

    def to_markdown(self) -> str:
        lines = [
            f"# OAK report — {self.operator}",
            "",
            f"**Status:** `{self.status}`",
            f"**Passed:** `{self.passed}`",
            "",
            "| Check | Passed | Value | Threshold | Detail |",
            "|---|---:|---:|---:|---|",
        ]
        for check in self.checks:
            lines.append(
                f"| {check.name} | {check.passed} | {check.value} | {check.threshold} | {check.detail} |"
            )
        lines.extend(
            [
                "",
                "This report certifies only deterministic software fixtures and declared numerical checks.",
                "It does not certify a theorem, a physical law, or experimental validity.",
            ]
        )
        return "\n".join(lines) + "\n"


def basis_covariance_error(
    operator: LinearOperator,
    basis: npt.ArrayLike,
    vector: npt.ArrayLike,
) -> float:
    """Check A'x' = P^{-1}Ax for a square endomorphism and basis P."""
    if operator.domain.dimension != operator.codomain.dimension:
        raise ValueError("basis covariance fixture requires an endomorphism")
    p = np.asarray(basis, dtype=float)
    x = operator.domain.vector(vector)
    transformed = operator.change_basis(p, p)
    x_prime = np.linalg.solve(p, x)
    left = transformed.apply(x_prime)
    right = np.linalg.solve(p, operator.apply(x))
    return float(np.linalg.norm(left - right))


def audit_operator(
    operator: LinearOperator,
    *,
    seed: int = 0,
    linearity_tolerance: float = 1e-10,
    covariance_tolerance: float = 1e-10,
    condition_warning: float = 1e10,
    rank_threshold: float = 1e-10,
) -> OAKReport:
    """Run deterministic algebraic and numerical checks on one operator."""
    if min(linearity_tolerance, covariance_tolerance, condition_warning, rank_threshold) <= 0:
        raise ValueError("audit thresholds must be positive")

    rng = np.random.default_rng(seed)
    x = rng.normal(size=operator.domain.dimension)
    y = rng.normal(size=operator.domain.dimension)
    alpha, beta = rng.normal(size=2)
    linearity_error = float(
        np.linalg.norm(
            operator.apply(alpha * x + beta * y)
            - alpha * operator.apply(x)
            - beta * operator.apply(y)
        )
    )
    svd = operator.svd_report(threshold=rank_threshold)

    checks: list[OAKCheck] = [
        OAKCheck(
            "linearity",
            linearity_error <= linearity_tolerance,
            linearity_error,
            linearity_tolerance,
            "Numerical verification of A(αx+βy)=αAx+βAy.",
        ),
        OAKCheck(
            "finite_condition_number",
            bool(np.isfinite(svd.condition_number)),
            svd.condition_number,
            None,
            "Infinite conditioning indicates an exactly singular fixture.",
        ),
        OAKCheck(
            "conditioning_warning_gate",
            svd.condition_number <= condition_warning,
            svd.condition_number,
            condition_warning,
            "A failed gate means numerically fragile, not mathematically false.",
        ),
        OAKCheck(
            "rank_consistency",
            svd.threshold_rank <= svd.exact_rank,
            svd.threshold_rank,
            float(svd.exact_rank),
            "Threshold rank cannot exceed the library exact-rank estimate.",
        ),
    ]

    if operator.domain.dimension == operator.codomain.dimension:
        q, _ = np.linalg.qr(rng.normal(size=(operator.domain.dimension, operator.domain.dimension)))
        covariance_error = basis_covariance_error(operator, q, x)
        checks.append(
            OAKCheck(
                "basis_covariance",
                covariance_error <= covariance_tolerance,
                covariance_error,
                covariance_tolerance,
                "Coordinate change must preserve the represented map.",
            )
        )

    passed = all(check.passed for check in checks)
    return OAKReport(
        operator=operator.name,
        status="OAK_PASS_SOFTWARE_FIXTURE" if passed else "OAK_REVIEW_REQUIRED",
        checks=tuple(checks),
    )
