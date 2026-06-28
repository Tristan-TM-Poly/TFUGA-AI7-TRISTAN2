"""SourceTrustKernel for Ω-INFO²-T."""

from __future__ import annotations

from dataclasses import dataclass

from .models import clamp01


@dataclass(slots=True)
class SourceTrustInput:
    reputation: float = 0.5
    traceability: float = 0.5
    reproducibility: float = 0.5
    freshness: float = 0.5
    independence: float = 0.5
    conflict_of_interest: float = 0.0
    opacity: float = 0.0
    primary_source: bool = False
    peer_reviewed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "reputation",
            "traceability",
            "reproducibility",
            "freshness",
            "independence",
            "conflict_of_interest",
            "opacity",
        ):
            setattr(self, name, clamp01(getattr(self, name)))


def score_source(source: SourceTrustInput) -> float:
    """Score a source without confusing trust with truth.

    High source trust increases confidence, but OAK validation still requires
    evidence, counter-evidence, tests, and residue tracking.
    """
    positive = (
        0.20 * source.reputation
        + 0.20 * source.traceability
        + 0.20 * source.reproducibility
        + 0.15 * source.freshness
        + 0.15 * source.independence
    )
    bonuses = 0.05 * float(source.primary_source) + 0.05 * float(source.peer_reviewed)
    penalties = 0.20 * source.conflict_of_interest + 0.20 * source.opacity
    return clamp01(positive + bonuses - penalties)


class SourceTrustKernel:
    """Callable kernel API for future hypergraph integration."""

    def __call__(self, source: SourceTrustInput) -> float:
        return score_source(source)
