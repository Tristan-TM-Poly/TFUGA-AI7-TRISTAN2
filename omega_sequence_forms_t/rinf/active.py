"""Active selection of discriminating indices between candidate continuations."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import log2
from statistics import median
from typing import Callable, Iterable, Mapping, Sequence


Prediction = Fraction | int | float | complex | str
Evaluator = Callable[[int], Prediction]


@dataclass(frozen=True)
class CandidatePredictor:
    candidate_id: str
    evaluator: Evaluator
    weight: float = 1.0
    valid_from: int = 0
    valid_to: int | None = None

    def supports(self, n: int) -> bool:
        return n >= self.valid_from and (self.valid_to is None or n <= self.valid_to)


@dataclass(frozen=True)
class IndexDiscrimination:
    index: int
    prediction_count: int
    distinct_predictions: int
    entropy_bits: float
    pairwise_disagreements: int
    numerical_spread: float | None
    predictions: tuple[tuple[str, str], ...]
    failures: tuple[tuple[str, str], ...]

    @property
    def score(self) -> tuple[float, int, float, int]:
        return (
            self.entropy_bits,
            self.distinct_predictions,
            self.numerical_spread or 0.0,
            self.pairwise_disagreements,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "prediction_count": self.prediction_count,
            "distinct_predictions": self.distinct_predictions,
            "entropy_bits": self.entropy_bits,
            "pairwise_disagreements": self.pairwise_disagreements,
            "numerical_spread": self.numerical_spread,
            "predictions": dict(self.predictions),
            "failures": dict(self.failures),
        }


def _canonical_prediction(value: Prediction) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, complex):
        return f"{value.real:.17g}{value.imag:+.17g}j"
    if isinstance(value, float):
        return f"{value:.17g}"
    return str(value)


def _numeric_value(value: Prediction) -> float | None:
    if isinstance(value, Fraction):
        return float(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, complex) and value.imag == 0:
        return float(value.real)
    return None


def discriminate_index(index: int, predictors: Sequence[CandidatePredictor]) -> IndexDiscrimination:
    if index < 0:
        raise ValueError("index must be non-negative")
    predictions: list[tuple[str, str]] = []
    failures: list[tuple[str, str]] = []
    weights: dict[str, float] = {}
    numeric: list[float] = []
    total_weight = 0.0

    for predictor in predictors:
        if not predictor.supports(index):
            continue
        if predictor.weight <= 0:
            continue
        try:
            value = predictor.evaluator(index)
        except Exception as exc:  # candidate-domain failures are evidence
            failures.append((predictor.candidate_id, f"{type(exc).__name__}: {exc}"))
            continue
        canonical = _canonical_prediction(value)
        predictions.append((predictor.candidate_id, canonical))
        weights[canonical] = weights.get(canonical, 0.0) + predictor.weight
        total_weight += predictor.weight
        numeric_value = _numeric_value(value)
        if numeric_value is not None:
            numeric.append(numeric_value)

    entropy = 0.0
    if total_weight:
        for weight in weights.values():
            probability = weight / total_weight
            entropy -= probability * log2(probability)
    count = len(predictions)
    agreements = sum(group * (group - 1) // 2 for group in (
        sum(1 for _, value in predictions if value == prediction)
        for prediction in weights
    ))
    total_pairs = count * (count - 1) // 2
    disagreements = total_pairs - agreements
    spread = None
    if len(numeric) >= 2:
        center = median(numeric)
        spread = max(abs(value - center) for value in numeric)

    return IndexDiscrimination(
        index=index,
        prediction_count=count,
        distinct_predictions=len(weights),
        entropy_bits=entropy,
        pairwise_disagreements=disagreements,
        numerical_spread=spread,
        predictions=tuple(sorted(predictions)),
        failures=tuple(sorted(failures)),
    )


def rank_discriminating_indices(
    predictors: Sequence[CandidatePredictor],
    indices: Iterable[int],
    *,
    limit: int | None = None,
) -> tuple[IndexDiscrimination, ...]:
    results = [discriminate_index(index, predictors) for index in indices]
    results.sort(key=lambda item: (item.score, -item.index), reverse=True)
    if limit is not None:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        results = results[:limit]
    return tuple(results)


def geometric_index_frontier(
    observed_terms: int,
    *,
    layers: int = 12,
    dense_radius: int = 16,
) -> tuple[int, ...]:
    if observed_terms < 0 or layers < 0 or dense_radius < 0:
        raise ValueError("frontier parameters must be non-negative")
    indices = set(range(observed_terms, observed_terms + dense_radius))
    anchor = max(1, observed_terms)
    for layer in range(layers):
        scale = 1 << layer
        indices.update({anchor * scale, anchor * scale + 1, anchor * scale - 1})
    return tuple(sorted(index for index in indices if index >= observed_terms))
