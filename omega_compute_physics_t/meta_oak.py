"""Meta-OAK checks for the empirical compute-discovery stack.

Meta-OAK validates the *validation machinery*: predictive calibration,
overfitting risk, representation promotion and residual interpretation. These
checks are conservative software gates, not mathematical guarantees.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Sequence

from .representation import RepresentationScore
from .residuals import ResidualReport
from .theory_foundry import TheoryCandidate
from .validation import ValidatedResourceModel

_EPS = 1e-15


@dataclass(frozen=True)
class MetaOAKCheck:
    name: str
    passed: bool
    severity: str
    observed: float | str | bool
    threshold: float | str | bool
    detail: str


@dataclass(frozen=True)
class MetaOAKReport:
    checks: tuple[MetaOAKCheck, ...]
    passes: bool
    status: str = "meta-oak-audit"
    epistemic_level: str = "software-validation-of-empirical-validation"
    oak_warning: str = (
        "Passing Meta-OAK reduces known validation failure modes; it does not "
        "prove that unknown failure modes are absent or that empirical claims "
        "are mathematical theorems."
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = [asdict(check) for check in self.checks]
        return payload


def audit_validated_model(
    validated: ValidatedResourceModel,
    *,
    max_cv_to_train_ratio: float = 4.0,
    min_calibration_points: int = 2,
    calibration_slack: float = 0.05,
) -> MetaOAKReport:
    report = validated.report
    selected_rows = [
        row for row in report.scores
        if row.name == report.selected_candidate and row.valid
    ]
    if not selected_rows:
        raise ValueError("selected validation row is missing")
    score = selected_rows[0]
    ratio = score.cv_rmse / max(score.train_rmse, _EPS)
    nominal_coverage = 1.0 - report.interval.alpha
    observed_coverage = report.interval.empirical_calibration_coverage
    checks = (
        MetaOAKCheck(
            "finite_metrics",
            all(math.isfinite(value) for value in (score.cv_rmse, score.train_rmse, report.calibration_rmse)),
            "error",
            "finite" if all(math.isfinite(value) for value in (score.cv_rmse, score.train_rmse, report.calibration_rmse)) else "non-finite",
            "finite",
            "Predictive metrics must be finite before promotion.",
        ),
        MetaOAKCheck(
            "calibration_sample_floor",
            report.n_calibration >= min_calibration_points,
            "error",
            report.n_calibration,
            min_calibration_points,
            "Uncertainty cannot be promoted without an explicit calibration partition.",
        ),
        MetaOAKCheck(
            "calibration_coverage",
            observed_coverage + calibration_slack >= nominal_coverage,
            "warning",
            observed_coverage,
            nominal_coverage,
            "Observed calibration coverage should not materially undercut nominal coverage.",
        ),
        MetaOAKCheck(
            "overfit_ratio",
            ratio <= max_cv_to_train_ratio or score.cv_rmse <= _EPS,
            "warning",
            ratio,
            max_cv_to_train_ratio,
            "Large CV/train error ratios indicate a fragile empirical law.",
        ),
    )
    return MetaOAKReport(checks=checks, passes=all(check.passed for check in checks if check.severity == "error"))


def audit_representation_candidate(
    candidate: RepresentationScore,
    *,
    min_relative_improvement: float = 0.05,
    require_positive_score: bool = True,
) -> MetaOAKReport:
    checks = (
        MetaOAKCheck(
            "representation_valid",
            candidate.valid,
            "error",
            candidate.valid,
            True,
            "Invalid transformations cannot be promoted.",
        ),
        MetaOAKCheck(
            "predictive_improvement",
            candidate.relative_improvement >= min_relative_improvement,
            "warning",
            candidate.relative_improvement,
            min_relative_improvement,
            "A derived coordinate should improve held-out prediction before promotion.",
        ),
        MetaOAKCheck(
            "description_penalty_survived",
            (candidate.score > 0.0) if require_positive_score else True,
            "warning",
            candidate.score,
            "> 0" if require_positive_score else "not required",
            "Compression gain should survive the explicit representation-complexity penalty.",
        ),
    )
    return MetaOAKReport(checks=checks, passes=all(check.passed for check in checks if check.severity == "error"))


def audit_residual_interpretation(
    residual_report: ResidualReport,
    *,
    causal_claim_requested: bool = False,
) -> MetaOAKReport:
    checks = (
        MetaOAKCheck(
            "residual_sample_floor",
            residual_report.n >= 6,
            "error",
            residual_report.n,
            6,
            "Residual-structure claims require multiple observations.",
        ),
        MetaOAKCheck(
            "causal_promotion_block",
            not causal_claim_requested,
            "error",
            causal_claim_requested,
            False,
            "Correlation with residuals is association evidence only; causal promotion requires intervention or independent evidence.",
        ),
    )
    return MetaOAKReport(checks=checks, passes=all(check.passed for check in checks if check.severity == "error"))


def audit_theory_ecology(
    theories: Sequence[TheoryCandidate],
    *,
    min_competitors: int = 2,
) -> MetaOAKReport:
    finite = sum(math.isfinite(theory.cv_rmse) for theory in theories)
    checks = (
        MetaOAKCheck(
            "theory_competition",
            len(theories) >= min_competitors,
            "warning",
            len(theories),
            min_competitors,
            "A single surviving empirical theory gives no direct model-disagreement signal.",
        ),
        MetaOAKCheck(
            "finite_theory_scores",
            finite == len(theories),
            "error",
            finite,
            len(theories),
            "Every promoted theory must expose a finite predictive score.",
        ),
    )
    return MetaOAKReport(checks=checks, passes=all(check.passed for check in checks if check.severity == "error"))
