"""Counterfactual behavioral twin over a posterior ensemble."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Sequence

from .fsm import MealyMachine


@dataclass(frozen=True, slots=True)
class TwinPrediction:
    distribution: Mapping[tuple[str, ...], float]
    most_likely_outputs: tuple[str, ...]
    confidence: float
    supporting_candidates: Mapping[tuple[str, ...], tuple[str, ...]]


@dataclass(slots=True)
class CounterfactualTwin:
    candidates: tuple[MealyMachine, ...]
    posterior: Mapping[str, float]

    def predict(self, inputs: Sequence[str]) -> TwinPrediction:
        if not self.candidates:
            raise ValueError("Twin requires at least one candidate")
        total = sum(max(0.0, self.posterior.get(candidate.candidate_id, 0.0)) for candidate in self.candidates)
        if total <= 0.0:
            weights = {candidate.candidate_id: 1.0 / len(self.candidates) for candidate in self.candidates}
        else:
            weights = {
                candidate.candidate_id: max(0.0, self.posterior.get(candidate.candidate_id, 0.0)) / total
                for candidate in self.candidates
            }
        distribution: dict[tuple[str, ...], float] = defaultdict(float)
        supporters: dict[tuple[str, ...], list[str]] = defaultdict(list)
        for candidate in self.candidates:
            outputs, _ = candidate.run(inputs)
            distribution[outputs] += weights[candidate.candidate_id]
            supporters[outputs].append(candidate.candidate_id)
        most_likely, confidence = max(distribution.items(), key=lambda item: item[1])
        return TwinPrediction(
            distribution=dict(sorted(distribution.items(), key=lambda item: item[1], reverse=True)),
            most_likely_outputs=most_likely,
            confidence=confidence,
            supporting_candidates={key: tuple(value) for key, value in supporters.items()},
        )
