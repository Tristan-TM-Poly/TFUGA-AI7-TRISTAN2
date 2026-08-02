"""Bayesian model-class expansion with explicit residual and complexity gates."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ModelClass:
    class_id: str
    parent_id: str | None
    complexity: float
    log_evidence: float
    residual: float
    provenance: str

    def __post_init__(self) -> None:
        if not self.class_id.strip():
            raise ValueError("class_id cannot be blank")
        if not math.isfinite(self.complexity) or self.complexity < 0.0:
            raise ValueError("complexity must be finite and non-negative")
        if not math.isfinite(self.log_evidence):
            raise ValueError("log_evidence must be finite")
        if not math.isfinite(self.residual) or self.residual < 0.0:
            raise ValueError("residual must be finite and non-negative")
        if not self.provenance.strip():
            raise ValueError("provenance cannot be blank")


@dataclass(frozen=True)
class ExpansionDecision:
    selected: tuple[ModelClass, ...]
    rejected: tuple[tuple[str, str], ...]
    posterior: Mapping[str, float]
    expansion_required: bool
    trigger: str
    claim: str = "bounded_model_class_search_only"


def posterior_over_classes(classes: Sequence[ModelClass], *, complexity_weight: float = 0.1) -> dict[str, float]:
    if not classes:
        raise ValueError("classes cannot be empty")
    scores = {
        item.class_id: item.log_evidence - complexity_weight * item.complexity
        for item in classes
    }
    peak = max(scores.values())
    weights = {key: math.exp(value - peak) for key, value in scores.items()}
    total = sum(weights.values())
    return {key: value / total for key, value in sorted(weights.items())}


def effective_class_count(posterior: Mapping[str, float]) -> float:
    total = sum(float(value) for value in posterior.values())
    if total <= 0.0:
        raise ValueError("posterior must have positive mass")
    probabilities = [float(value) / total for value in posterior.values()]
    entropy = -sum(p * math.log(p) for p in probabilities if p > 0.0)
    return math.exp(entropy)


def expand_model_classes(
    current: Sequence[ModelClass],
    generator: Callable[[ModelClass], Iterable[ModelClass]],
    *,
    residual_threshold: float,
    posterior_mass_threshold: float = 0.95,
    beam_width: int = 8,
    complexity_weight: float = 0.1,
    max_complexity: float = math.inf,
) -> ExpansionDecision:
    if beam_width <= 0:
        raise ValueError("beam_width must be positive")
    if residual_threshold < 0.0:
        raise ValueError("residual_threshold cannot be negative")
    posterior = posterior_over_classes(current, complexity_weight=complexity_weight)
    ordered = sorted(current, key=lambda item: posterior[item.class_id], reverse=True)
    cumulative = 0.0
    focus: list[ModelClass] = []
    for item in ordered:
        focus.append(item)
        cumulative += posterior[item.class_id]
        if cumulative >= posterior_mass_threshold:
            break
    worst_residual = max(item.residual for item in focus)
    if worst_residual <= residual_threshold:
        return ExpansionDecision(
            selected=tuple(focus[:beam_width]),
            rejected=(),
            posterior=posterior,
            expansion_required=False,
            trigger="residual_within_threshold",
        )
    candidates: dict[str, ModelClass] = {item.class_id: item for item in current}
    rejected: list[tuple[str, str]] = []
    for parent in focus:
        for child in generator(parent):
            if child.parent_id != parent.class_id:
                rejected.append((child.class_id, "parent_mismatch"))
                continue
            if child.complexity <= parent.complexity:
                rejected.append((child.class_id, "complexity_not_expanded"))
                continue
            if child.complexity > max_complexity:
                rejected.append((child.class_id, "complexity_budget"))
                continue
            if child.class_id in candidates:
                rejected.append((child.class_id, "duplicate_class_id"))
                continue
            candidates[child.class_id] = child
    all_classes = tuple(candidates.values())
    expanded_posterior = posterior_over_classes(all_classes, complexity_weight=complexity_weight)
    selected = tuple(
        sorted(all_classes, key=lambda item: expanded_posterior[item.class_id], reverse=True)[:beam_width]
    )
    return ExpansionDecision(
        selected=selected,
        rejected=tuple(sorted(rejected)),
        posterior=expanded_posterior,
        expansion_required=True,
        trigger="residual_exceeded_threshold",
    )
