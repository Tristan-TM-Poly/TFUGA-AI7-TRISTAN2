"""Formal core for Ω-PURE-MATH-T∞.

This module intentionally separates definitions, conjectures and proved statements.
It provides machine-readable research objects without claiming novelty or proof.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, Callable, Iterable


class ClaimStatus(str, Enum):
    DEFINITION = "definition"
    PROPOSITION = "proposition"
    THEOREM = "theorem"
    CONJECTURE = "conjecture"
    HEURISTIC = "heuristic"
    COUNTEREXAMPLE = "counterexample"


@dataclass(frozen=True)
class Claim:
    """A claim with an explicit epistemic status."""

    identifier: str
    title: str
    statement: str
    status: ClaimStatus
    hypotheses: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    oak_notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class TheorySpec:
    """Executable manifest for the ten-slot Ω-PURE-MATH theory object."""

    name: str
    objects: tuple[str, ...] = ()
    morphisms: tuple[str, ...] = ()
    representations: tuple[str, ...] = ()
    transformations: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    defects: tuple[str, ...] = ()
    factorizations: tuple[str, ...] = ()
    proofs: tuple[str, ...] = ()
    complexities: tuple[str, ...] = ()
    extensions: tuple[str, ...] = ()
    claims: tuple[Claim, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["claims"] = [claim.to_dict() for claim in self.claims]
        return data


@dataclass(frozen=True)
class OAKFinding:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class OAKReport:
    accepted: bool
    findings: tuple[OAKFinding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "findings": [asdict(item) for item in self.findings],
        }


def fertile_compression_score(
    closure_complexity: float,
    theory_complexity: float,
) -> float:
    """Working Tristan definition Φ(T)=K(closure)/(1+K(T)).

    This is a research heuristic, not a canonical information-theoretic quantity.
    """

    if not (isfinite(closure_complexity) and isfinite(theory_complexity)):
        raise ValueError("complexities must be finite")
    if closure_complexity < 0 or theory_complexity < 0:
        raise ValueError("complexities must be non-negative")
    return closure_complexity / (1.0 + theory_complexity)


def law_defect(
    left: Any,
    right: Any,
    *,
    subtract: Callable[[Any, Any], Any] | None = None,
) -> Any:
    """Return the defect between two sides of a proposed law."""

    if subtract is not None:
        return subtract(left, right)
    try:
        return left - right
    except TypeError as exc:  # pragma: no cover - defensive message path
        raise TypeError("provide subtract= for objects without subtraction") from exc


def invariant_defect(
    transform: Callable[[Any], Any],
    invariant: Callable[[Any], Any],
    obj: Any,
    *,
    metric: Callable[[Any, Any], float],
) -> float:
    """Measure D_I(g,x)=d(I(gx), I(x))."""

    value = float(metric(invariant(transform(obj)), invariant(obj)))
    if value < 0 or not isfinite(value):
        raise ValueError("metric must return a finite non-negative value")
    return value


def oak_audit_claims(claims: Iterable[Claim]) -> OAKReport:
    """Guard against promoting conjectures/heuristics as theorems.

    The gate is deliberately conservative: a theorem must declare at least one
    dependency or an OAK note explaining its proof/certification basis.
    """

    findings: list[OAKFinding] = []
    for claim in claims:
        if claim.status is ClaimStatus.THEOREM and not (
            claim.dependencies or claim.oak_notes
        ):
            findings.append(
                OAKFinding(
                    code="THEOREM_WITHOUT_BASIS",
                    severity="error",
                    message=f"{claim.identifier}: theorem has no proof/certification basis",
                )
            )
        if claim.status in {ClaimStatus.CONJECTURE, ClaimStatus.HEURISTIC}:
            findings.append(
                OAKFinding(
                    code="NON_CANONICAL_CLAIM",
                    severity="info",
                    message=f"{claim.identifier}: retained as {claim.status.value}",
                )
            )
    return OAKReport(
        accepted=not any(item.severity == "error" for item in findings),
        findings=tuple(findings),
    )
