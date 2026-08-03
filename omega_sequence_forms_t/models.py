"""Typed public models for Ω-SUITE-FORM-T∞.

The package distinguishes finite-prefix agreement, predictive validation and
mathematical proof.  No candidate inferred only from terms is labelled as a
proved global identity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum, IntEnum
from fractions import Fraction
from typing import Any, Callable


class CandidateKind(str, Enum):
    """Analytic representation families implemented by the R0.1 engine."""

    NEWTON_POLYNOMIAL = "newton_polynomial"
    LINEAR_RECURRENCE = "linear_recurrence"
    RATIONAL_GENERATING_FUNCTION = "rational_generating_function"


class OAKLevel(IntEnum):
    """Evidence ladder for formulas inferred from a finite prefix."""

    VISUAL_PATTERN = 0
    OBSERVED_FIT = 1
    HELD_OUT_PREDICTION = 2
    INDEPENDENT_GENERATOR_CHECK = 3
    SYMBOLIC_IDENTITY = 4
    MATHEMATICAL_PROOF = 5
    FORMAL_PROOF = 6


@dataclass(frozen=True)
class ValidationSummary:
    """Exact fit and held-out prediction counts."""

    fitted_terms: int
    fitted_matches: int
    held_out_terms: int
    held_out_matches: int

    @property
    def fits_observed(self) -> bool:
        return self.fitted_terms == self.fitted_matches

    @property
    def predicts_held_out(self) -> bool:
        return self.held_out_terms > 0 and self.held_out_terms == self.held_out_matches


@dataclass
class FormCandidate:
    """One representation candidate and its evidence receipt."""

    kind: CandidateKind
    expression: str
    parameters: dict[str, Any]
    validation: ValidationSummary
    oak_level: OAKLevel
    complexity: int
    exact_arithmetic: bool = True
    warnings: list[str] = field(default_factory=list)
    _evaluator: Callable[[int], Fraction] | None = field(default=None, repr=False, compare=False)

    def evaluate(self, n: int) -> Fraction:
        if n < 0:
            raise ValueError("sequence indices must be non-negative")
        if self._evaluator is None:
            raise RuntimeError("candidate does not expose an evaluator")
        return self._evaluator(n)

    @property
    def score(self) -> tuple[int, int, int, int]:
        """Deterministic ranking: evidence, holdout, fit, then simplicity."""

        return (
            int(self.oak_level),
            self.validation.held_out_matches,
            self.validation.fitted_matches,
            -self.complexity,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("_evaluator", None)
        payload["kind"] = self.kind.value
        payload["oak_level"] = int(self.oak_level)
        payload["oak_label"] = self.oak_level.name
        payload["parameters"] = _json_safe(payload["parameters"])
        return payload


@dataclass
class DiscoveryReport:
    """Deterministic discovery output for one finite sequence prefix."""

    terms: tuple[Fraction, ...]
    training_terms: int
    held_out_terms: int
    candidates: list[FormCandidate]
    diagnostics: dict[str, Any]
    warnings: list[str]
    schema: str = "omega-sequence-forms-report/1"

    @property
    def best(self) -> FormCandidate | None:
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda candidate: candidate.score)

    def to_dict(self) -> dict[str, Any]:
        best = self.best
        return {
            "schema": self.schema,
            "terms": [_fraction_text(value) for value in self.terms],
            "training_terms": self.training_terms,
            "held_out_terms": self.held_out_terms,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "best_candidate": None if best is None else best.to_dict(),
            "diagnostics": _json_safe(self.diagnostics),
            "warnings": list(self.warnings),
            "global_identity_proved": False,
        }


def _fraction_text(value: Fraction) -> int | str:
    return value.numerator if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _json_safe(value: Any) -> Any:
    if isinstance(value, Fraction):
        return _fraction_text(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
