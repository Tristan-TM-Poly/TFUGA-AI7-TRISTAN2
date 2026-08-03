"""Residual Form Evolution Engine for layered analytic decompositions."""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
import json
from typing import Callable, Iterable, Iterator, Mapping, Sequence

from ..exact import NumberLike, normalize_terms, vector_complexity


Evaluator = Callable[[int], Fraction]
CandidateFactory = Callable[[tuple[Fraction, ...]], Iterable["ResidualCandidate"]]


@dataclass(frozen=True)
class ResidualCandidate:
    candidate_id: str
    family_id: str
    expression: str
    evaluator: Evaluator
    complexity: int
    assumptions: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()

    def evaluate_prefix(self, count: int) -> tuple[Fraction, ...]:
        return tuple(self.evaluator(index) for index in range(count))


@dataclass(frozen=True)
class ResidualLayer:
    layer_index: int
    candidate_id: str
    family_id: str
    expression: str
    complexity: int
    input_l1: Fraction
    output_l1: Fraction
    compression_gain: float
    residual_digest: str
    assumptions: tuple[str, ...]
    risk_tags: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "layer_index": self.layer_index,
            "candidate_id": self.candidate_id,
            "family_id": self.family_id,
            "expression": self.expression,
            "complexity": self.complexity,
            "input_l1": str(self.input_l1),
            "output_l1": str(self.output_l1),
            "compression_gain": self.compression_gain,
            "residual_digest": self.residual_digest,
            "assumptions": list(self.assumptions),
            "risk_tags": list(self.risk_tags),
        }


@dataclass
class ResidualDecomposition:
    original: tuple[Fraction, ...]
    residual: tuple[Fraction, ...]
    layers: list[ResidualLayer] = field(default_factory=list)
    evaluators: list[Evaluator] = field(default_factory=list, repr=False)
    stop_reason: str = "not_started"

    def reconstruct(self, n: int) -> Fraction:
        if not 0 <= n < len(self.original):
            raise IndexError("reconstruction is limited to the observed prefix")
        return sum((evaluator(n) for evaluator in self.evaluators), self.residual[n])

    def exact_roundtrip(self) -> bool:
        return all(self.reconstruct(index) == value for index, value in enumerate(self.original))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "omega-sequence-forms-residual-decomposition/1",
            "term_count": len(self.original),
            "layers": [layer.to_dict() for layer in self.layers],
            "residual": [str(value) for value in self.residual],
            "stop_reason": self.stop_reason,
            "exact_roundtrip": self.exact_roundtrip(),
            "global_identity_proved": False,
        }

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


def l1(values: Sequence[Fraction]) -> Fraction:
    return sum((abs(value) for value in values), Fraction(0))


def residual_after(values: Sequence[Fraction], candidate: ResidualCandidate) -> tuple[Fraction, ...]:
    return tuple(value - candidate.evaluator(index) for index, value in enumerate(values))


def _gain(
    before: Sequence[Fraction],
    after: Sequence[Fraction],
    complexity: int,
    *,
    complexity_weight: float,
) -> float:
    before_norm = float(l1(before))
    after_norm = float(l1(after))
    signal_gain = before_norm - after_norm
    return signal_gain - complexity_weight * complexity


def greedy_residual_decompose(
    terms: Iterable[NumberLike],
    factories: Sequence[CandidateFactory],
    *,
    maximum_layers: int | None = None,
    minimum_gain: float = 0.0,
    complexity_weight: float = 0.01,
) -> ResidualDecomposition:
    values = normalize_terms(terms)
    if maximum_layers is not None and maximum_layers <= 0:
        raise ValueError("maximum_layers must be positive when supplied")
    if minimum_gain < 0 or complexity_weight < 0:
        raise ValueError("gain parameters must be non-negative")
    decomposition = ResidualDecomposition(original=values, residual=values)
    layer_index = 0
    while True:
        if maximum_layers is not None and layer_index >= maximum_layers:
            decomposition.stop_reason = "campaign_layer_cap"
            break
        candidates = []
        for factory in factories:
            candidates.extend(factory(decomposition.residual))
        if not candidates:
            decomposition.stop_reason = "no_candidates"
            break
        scored = []
        for candidate in candidates:
            try:
                residual = residual_after(decomposition.residual, candidate)
            except Exception:
                continue
            gain = _gain(
                decomposition.residual,
                residual,
                candidate.complexity,
                complexity_weight=complexity_weight,
            )
            scored.append((gain, -candidate.complexity, candidate.candidate_id, candidate, residual))
        if not scored:
            decomposition.stop_reason = "all_candidates_failed_domain"
            break
        gain, _, _, candidate, residual = max(scored)
        if gain <= minimum_gain:
            decomposition.stop_reason = "marginal_gain_threshold"
            break
        before_norm = l1(decomposition.residual)
        after_norm = l1(residual)
        digest = sha256(
            json.dumps([str(value) for value in residual], separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        decomposition.layers.append(
            ResidualLayer(
                layer_index=layer_index,
                candidate_id=candidate.candidate_id,
                family_id=candidate.family_id,
                expression=candidate.expression,
                complexity=candidate.complexity,
                input_l1=before_norm,
                output_l1=after_norm,
                compression_gain=gain,
                residual_digest=digest,
                assumptions=candidate.assumptions,
                risk_tags=candidate.risk_tags,
            )
        )
        decomposition.evaluators.append(candidate.evaluator)
        decomposition.residual = residual
        layer_index += 1
        if all(value == 0 for value in residual):
            decomposition.stop_reason = "zero_residual"
            break
    return decomposition


def constant_factory(values: tuple[Fraction, ...]) -> tuple[ResidualCandidate, ...]:
    if not values:
        return ()
    candidates = []
    for statistic, value in (
        ("first", values[0]),
        ("last", values[-1]),
        ("mean", sum(values, Fraction(0)) / len(values)),
    ):
        candidates.append(
            ResidualCandidate(
                candidate_id=f"constant.{statistic}.{value}",
                family_id="constant",
                expression=str(value),
                evaluator=lambda _n, value=value: value,
                complexity=2,
            )
        )
    return tuple(candidates)


def affine_factory(values: tuple[Fraction, ...]) -> tuple[ResidualCandidate, ...]:
    if len(values) < 2:
        return ()
    slope = values[1] - values[0]
    intercept = values[0]
    return (
        ResidualCandidate(
            candidate_id=f"affine.{intercept}.{slope}",
            family_id="affine",
            expression=f"({intercept})+({slope})*n",
            evaluator=lambda n: intercept + slope * n,
            complexity=4,
        ),
    )


def periodic_factory(max_period: int = 16) -> CandidateFactory:
    if max_period <= 0:
        raise ValueError("max_period must be positive")

    def factory(values: tuple[Fraction, ...]) -> tuple[ResidualCandidate, ...]:
        candidates = []
        for period in range(2, min(max_period, len(values) // 2) + 1):
            pattern = values[:period]
            if all(values[index] == pattern[index % period] for index in range(len(values))):
                candidates.append(
                    ResidualCandidate(
                        candidate_id=f"periodic.{period}",
                        family_id="periodic",
                        expression=f"pattern[{period}][n mod {period}]",
                        evaluator=lambda n, pattern=pattern, period=period: pattern[n % period],
                        complexity=period + 2,
                    )
                )
        return tuple(candidates)

    return factory
