"""Omega Math Tristan executable core.

This module is intentionally small and dependency-free. It gives the canon a
minimal operational layer: OAK status normalization, Bayes-Tristan action scores,
canonicalization scores, and next-action hints.

The goal is not to prove the theory. The goal is to prevent category mistakes:
intuition != conjecture != prototype != theorem != canon.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal

OAK_LEVELS: dict[str, int] = {
    "OAK-0": 0,
    "OAK-1": 1,
    "OAK-2": 2,
    "OAK-3": 3,
    "OAK-4": 4,
    "OAK-5": 5,
    "OAK-6": 6,
    "OAK-7": 7,
    "OAK-8": 8,
    "OAK-9": 9,
    "OAK-10": 10,
}

ClaimType = Literal[
    "intuition",
    "definition",
    "conjecture",
    "theorem",
    "prototype",
    "test",
    "counterexample",
    "negative_memory",
    "canon",
]

NextAction = Literal[
    "formalize_definition",
    "write_theorem",
    "search_counterexample",
    "build_prototype",
    "run_baseline",
    "extract_invariant",
    "audit_residue",
    "write_negative_memory",
    "promote_to_canon",
    "demote_or_refute",
]


def clamp01(value: float) -> float:
    """Clamp a numeric value to [0, 1]."""
    return max(0.0, min(1.0, float(value)))


def oak_maturity(status: str) -> float:
    """Return a normalized OAK maturity score in [0, 1]."""
    if status not in OAK_LEVELS:
        raise ValueError(f"Unknown OAK status: {status!r}")
    return OAK_LEVELS[status] / 10.0


@dataclass(frozen=True)
class BayesTristanVector:
    """Multi-axis score for deciding what to develop next.

    probability is a confidence proxy, not a proof.
    fertility is generative potential, not truth.
    risk includes illusion, overclaiming, residue and unsafe leaps.
    """

    probability: float
    utility: float
    fertility: float
    testability: float
    compressibility: float
    risk: float
    oak_maturity: float

    def normalized(self) -> "BayesTristanVector":
        return BayesTristanVector(
            probability=clamp01(self.probability),
            utility=clamp01(self.utility),
            fertility=clamp01(self.fertility),
            testability=clamp01(self.testability),
            compressibility=clamp01(self.compressibility),
            risk=clamp01(self.risk),
            oak_maturity=clamp01(self.oak_maturity),
        )


@dataclass(frozen=True)
class ClaimCard:
    """Minimal claim card for the Omega Math Tristan canon."""

    id: str
    title: str
    statement: str
    branch: str
    oak_status: str
    claim_type: ClaimType
    bayes_tristan: BayesTristanVector
    hypotheses: tuple[str, ...] = ()
    definitions: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    positive_memory: tuple[str, ...] = ()
    negative_memory: tuple[str, ...] = ()
    residue: tuple[str, ...] = ()
    next_action: NextAction = "formalize_definition"
    links: tuple[str, ...] = ()

    def maturity(self) -> float:
        return oak_maturity(self.oak_status)

    def with_oak_maturity(self) -> "ClaimCard":
        """Return a copy whose Bayes-Tristan maturity matches oak_status."""
        vector = self.bayes_tristan.normalized()
        updated = BayesTristanVector(
            probability=vector.probability,
            utility=vector.utility,
            fertility=vector.fertility,
            testability=vector.testability,
            compressibility=vector.compressibility,
            risk=vector.risk,
            oak_maturity=self.maturity(),
        )
        return ClaimCard(
            id=self.id,
            title=self.title,
            statement=self.statement,
            branch=self.branch,
            oak_status=self.oak_status,
            claim_type=self.claim_type,
            bayes_tristan=updated,
            hypotheses=self.hypotheses,
            definitions=self.definitions,
            invariants=self.invariants,
            positive_memory=self.positive_memory,
            negative_memory=self.negative_memory,
            residue=self.residue,
            next_action=self.next_action,
            links=self.links,
        )


def action_score(vector: BayesTristanVector, *, cost: float = 0.0) -> float:
    """Bayes-Tristan action score.

    This score ranks development priority. It must not be interpreted as a truth
    probability or proof strength.
    """
    v = vector.normalized()
    return (
        0.22 * v.probability
        + 0.18 * v.utility
        + 0.18 * v.fertility
        + 0.16 * v.testability
        + 0.12 * v.compressibility
        + 0.14 * v.oak_maturity
        - 0.25 * v.risk
        - 0.10 * clamp01(cost)
    )


def canonicalization_score(vector: BayesTristanVector, *, cost: float = 0.0, illusion: float = 0.0) -> float:
    """Score for possible canon promotion.

    Higher is better. Promotion still requires OAK gates. A high score is not a
    proof and cannot override missing hypotheses, tests or counterexamples.
    """
    v = vector.normalized()
    return (
        v.probability
        + v.utility
        + v.fertility
        + v.testability
        + v.compressibility
        + v.oak_maturity
        - v.risk
        - clamp01(cost)
        - clamp01(illusion)
    ) / 6.0


def classify_oak_status(*, has_definition: bool, has_conjecture: bool, has_prototype: bool, has_baseline: bool, has_robust_validation: bool, has_partial_proof: bool, has_full_proof: bool, reused_across_branches: bool = False) -> str:
    """Classify a claim into an approximate OAK level using explicit gates."""
    if has_full_proof and reused_across_branches:
        return "OAK-9"
    if has_full_proof:
        return "OAK-7"
    if has_partial_proof:
        return "OAK-6"
    if has_robust_validation:
        return "OAK-5"
    if has_baseline:
        return "OAK-4"
    if has_prototype:
        return "OAK-3"
    if has_conjecture:
        return "OAK-2"
    if has_definition:
        return "OAK-1"
    return "OAK-0"


def next_action_hint(card: ClaimCard) -> NextAction:
    """Suggest a conservative next action based on missing evidence."""
    level = OAK_LEVELS.get(card.oak_status)
    if level is None:
        raise ValueError(f"Unknown OAK status: {card.oak_status!r}")

    if level <= 0:
        return "formalize_definition"
    if level == 1:
        return "write_theorem" if card.claim_type == "theorem" else "search_counterexample"
    if level == 2:
        return "build_prototype"
    if level == 3:
        return "run_baseline"
    if level == 4:
        return "audit_residue"
    if level == 5:
        return "write_theorem"
    if level == 6:
        return "search_counterexample"
    if level >= 7 and card.negative_memory:
        return "audit_residue"
    if level >= 7:
        return "promote_to_canon"
    return "formalize_definition"


def rank_claims(cards: Iterable[ClaimCard], *, cost: float = 0.0) -> list[tuple[float, ClaimCard]]:
    """Rank claim cards by action score, descending."""
    ranked = [(action_score(card.with_oak_maturity().bayes_tristan, cost=cost), card) for card in cards]
    return sorted(ranked, key=lambda item: item[0], reverse=True)
