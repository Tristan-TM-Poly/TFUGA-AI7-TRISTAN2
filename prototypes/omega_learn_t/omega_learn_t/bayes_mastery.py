from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Tuple

from .core import AXES, Evidence, MasteryAxis, clamp01


@dataclass(frozen=True)
class BetaPosterior:
    alpha: float
    beta: float

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def uncertainty(self) -> float:
        total = self.alpha + self.beta
        return (self.alpha * self.beta / ((total ** 2) * (total + 1))) ** 0.5


def update_mastery(
    evidence: Iterable[Evidence],
    prior: Mapping[MasteryAxis, Tuple[float, float]] | None = None,
) -> Dict[MasteryAxis, BetaPosterior]:
    """Update mastery by axis with simple Beta-Binomial evidence.

    Default prior Beta(2,2) is intentionally conservative: neither mastery nor failure
    is assumed without evidence.
    """

    params: Dict[MasteryAxis, Tuple[float, float]] = {
        axis: tuple(prior.get(axis, (2.0, 2.0))) if prior else (2.0, 2.0)
        for axis in AXES
    }
    for item in evidence:
        alpha, beta = params[item.axis]
        alpha += item.successes * item.weight
        beta += item.failures * item.weight
        params[item.axis] = (alpha, beta)
    return {axis: BetaPosterior(alpha=a, beta=b) for axis, (a, b) in params.items()}


def mastery_vector(evidence: Iterable[Evidence]) -> Dict[MasteryAxis, float]:
    return {axis: clamp01(post.mean) for axis, post in update_mastery(evidence).items()}


def weakest_axes(scores: Mapping[MasteryAxis, float], limit: int = 3) -> list[MasteryAxis]:
    return [axis for axis, _ in sorted(scores.items(), key=lambda kv: kv[1])[:limit]]


def confidence_penalty(evidence: Iterable[Evidence]) -> float:
    posts = update_mastery(evidence)
    avg_uncertainty = sum(p.uncertainty for p in posts.values()) / len(posts)
    return clamp01(avg_uncertainty * 4.0)
