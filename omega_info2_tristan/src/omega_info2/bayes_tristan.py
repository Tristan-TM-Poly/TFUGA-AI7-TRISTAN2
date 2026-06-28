"""Bayes-Tristan vector update layer for Ω-INFO²-T.

This module implements a conservative multi-dimensional Bayesian updater.
It does not claim that a posterior is proof. It updates structured beliefs
about truth, utility, fertility, testability, safety, profitability, and
novelty from evidence likelihood ratios.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import exp, log
from typing import Any

from .models import InfoObject, clamp01


def _clip_probability(value: float, eps: float = 1e-6) -> float:
    return min(1.0 - eps, max(eps, float(value)))


def _logit(p: float) -> float:
    p = _clip_probability(p)
    return log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))


@dataclass(slots=True)
class BayesTristanVector:
    truth: float = 0.5
    utility: float = 0.5
    fertility: float = 0.5
    testability: float = 0.5
    safety: float = 0.5
    profitability: float = 0.5
    novelty: float = 0.5

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            setattr(self, name, clamp01(getattr(self, name)))

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    @classmethod
    def from_info_object(cls, obj: InfoObject) -> "BayesTristanVector":
        return cls(
            truth=max(obj.scores.truth, 0.05),
            utility=max(obj.scores.utility, 0.05),
            fertility=max(obj.scores.fertility, 0.05),
            testability=max(obj.scores.testability, 0.05),
            safety=max(obj.scores.safety, 0.05),
            profitability=max(1.0 - obj.scores.risk, 0.05),
            novelty=max(obj.scores.novelty, 0.05),
        )


@dataclass(slots=True)
class EvidenceVector:
    """Likelihood-ratio evidence vector.

    A value > 1 supports a dimension, < 1 weakens it, and 1 is neutral.
    Keep values bounded; extreme evidence should be decomposed into traceable
    evidence items instead of using huge ratios.
    """

    label: str
    truth_lr: float = 1.0
    utility_lr: float = 1.0
    fertility_lr: float = 1.0
    testability_lr: float = 1.0
    safety_lr: float = 1.0
    profitability_lr: float = 1.0
    novelty_lr: float = 1.0
    source: str | None = None
    note: str | None = None

    def bounded_lrs(self) -> dict[str, float]:
        return {
            "truth": _bounded_lr(self.truth_lr),
            "utility": _bounded_lr(self.utility_lr),
            "fertility": _bounded_lr(self.fertility_lr),
            "testability": _bounded_lr(self.testability_lr),
            "safety": _bounded_lr(self.safety_lr),
            "profitability": _bounded_lr(self.profitability_lr),
            "novelty": _bounded_lr(self.novelty_lr),
        }


def _bounded_lr(value: float, lower: float = 0.05, upper: float = 20.0) -> float:
    try:
        return max(lower, min(upper, float(value)))
    except (TypeError, ValueError):
        return 1.0


@dataclass(slots=True)
class BayesTristanReport:
    prior: BayesTristanVector
    posterior: BayesTristanVector
    evidence: list[dict[str, Any]] = field(default_factory=list)
    residue: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prior": self.prior.to_dict(),
            "posterior": self.posterior.to_dict(),
            "evidence": self.evidence,
            "residue": self.residue,
        }


class BayesTristanUpdater:
    """Vectorial Bayes updater with OAK-safe residue tracking."""

    def update(
        self,
        prior: BayesTristanVector,
        evidence_items: list[EvidenceVector],
    ) -> BayesTristanReport:
        logits = {name: _logit(value) for name, value in prior.to_dict().items()}
        residue: list[str] = []
        serialized: list[dict[str, Any]] = []

        for item in evidence_items:
            lrs = item.bounded_lrs()
            serialized.append({"label": item.label, "source": item.source, "note": item.note, "likelihood_ratios": lrs})
            if not item.source:
                residue.append(f"Evidence '{item.label}' lacks source/provenance.")
            for dimension, lr in lrs.items():
                logits[dimension] += log(lr)

        posterior = BayesTristanVector(**{name: _sigmoid(value) for name, value in logits.items()})
        return BayesTristanReport(prior=prior, posterior=posterior, evidence=serialized, residue=residue)

    def update_info_object(self, obj: InfoObject, evidence_items: list[EvidenceVector]) -> BayesTristanReport:
        report = self.update(BayesTristanVector.from_info_object(obj), evidence_items)
        posterior = report.posterior
        obj.scores.truth = posterior.truth
        obj.scores.utility = posterior.utility
        obj.scores.fertility = posterior.fertility
        obj.scores.testability = posterior.testability
        obj.scores.safety = posterior.safety
        obj.scores.novelty = posterior.novelty
        obj.oak.residue.extend(report.residue)
        return report
