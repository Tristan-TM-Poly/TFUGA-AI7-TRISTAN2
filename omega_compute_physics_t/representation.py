"""R0.4 representation evolution for Ω-META-COMPUTE-PHYSICS-T∞.

The module searches a bounded, interpretable family of derived coordinates and
scores whether they compress finite-domain resource prediction. A discovered
coordinate is an empirical representation candidate, never evidence of a
causal variable or a mathematical asymptotic law by itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
import math
from typing import Any, Mapping, Sequence

from .atlas import ResourceSample
from .validation import ModelCandidate, cross_validated_rmse

_EPS = 1e-15


@dataclass(frozen=True)
class DerivedCoordinate:
    """Serializable candidate coordinate generated from measured variables."""

    kind: str
    variables: tuple[str, ...]
    label: str
    complexity_cost: float

    def evaluate(self, point: Mapping[str, float]) -> float:
        xs = [float(point[name]) for name in self.variables]
        if self.kind == "identity":
            return xs[0]
        if self.kind == "log":
            if xs[0] <= 0:
                raise ValueError(f"{self.label} requires a positive input")
            return math.log(xs[0])
        if self.kind == "sqrt":
            if xs[0] < 0:
                raise ValueError(f"{self.label} requires a non-negative input")
            return math.sqrt(xs[0])
        if self.kind == "product":
            return xs[0] * xs[1]
        if self.kind == "ratio":
            if abs(xs[1]) <= _EPS:
                raise ValueError(f"{self.label} divides by zero")
            return xs[0] / xs[1]
        if self.kind == "geometric_mean":
            product = xs[0] * xs[1]
            if product < 0:
                raise ValueError(f"{self.label} requires non-negative product")
            return math.sqrt(product)
        if self.kind == "log_ratio":
            if xs[0] <= 0 or xs[1] <= 0:
                raise ValueError(f"{self.label} requires positive inputs")
            return math.log(xs[0] / xs[1])
        raise ValueError(f"unsupported coordinate kind: {self.kind}")


@dataclass(frozen=True)
class RepresentationScore:
    coordinate: DerivedCoordinate
    baseline_cv_rmse: float
    transformed_cv_rmse: float
    relative_improvement: float
    score: float
    valid: bool = True
    note: str = ""
    epistemic_level: str = "empirical-representation-candidate"
    oak_warning: str = (
        "Predictive compression does not establish that a derived coordinate is "
        "causal, unique, physically fundamental, or asymptotically exact."
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["coordinate"] = asdict(self.coordinate)
        return payload


def generate_coordinate_candidates(
    variable_names: Sequence[str],
    *,
    include_identity: bool = False,
    include_unary: bool = True,
    include_pairs: bool = True,
    max_candidates: int = 128,
) -> tuple[DerivedCoordinate, ...]:
    """Generate a bounded interpretable coordinate language.

    The language is deliberately small: logs/square roots and pairwise
    products/ratios/geometric means/log-ratios. R0.4 evolves *within* this safe
    grammar before considering a richer symbolic language in later releases.
    """

    names = tuple(sorted(set(variable_names)))
    if not names:
        raise ValueError("variable_names cannot be empty")
    rows: list[DerivedCoordinate] = []
    if include_identity:
        rows.extend(
            DerivedCoordinate("identity", (name,), name, 1.0)
            for name in names
        )
    if include_unary:
        for name in names:
            rows.append(DerivedCoordinate("log", (name,), f"log({name})", 1.5))
            rows.append(DerivedCoordinate("sqrt", (name,), f"sqrt({name})", 1.5))
    if include_pairs:
        for left, right in combinations(names, 2):
            rows.append(DerivedCoordinate("product", (left, right), f"{left}*{right}", 2.0))
            rows.append(DerivedCoordinate("ratio", (left, right), f"{left}/{right}", 2.0))
            rows.append(DerivedCoordinate("ratio", (right, left), f"{right}/{left}", 2.0))
            rows.append(
                DerivedCoordinate(
                    "geometric_mean", (left, right), f"sqrt({left}*{right})", 2.5
                )
            )
            rows.append(DerivedCoordinate("log_ratio", (left, right), f"log({left}/{right})", 2.5))
            rows.append(DerivedCoordinate("log_ratio", (right, left), f"log({right}/{left})", 2.5))
    rows = sorted(rows, key=lambda item: (item.complexity_cost, item.label))
    if len(rows) > max_candidates:
        rows = rows[:max_candidates]
    return tuple(rows)


def transform_samples(
    samples: Sequence[ResourceSample],
    coordinate: DerivedCoordinate,
    *,
    keep_original: bool = False,
) -> list[ResourceSample]:
    """Project samples through one derived coordinate."""

    transformed: list[ResourceSample] = []
    for sample in samples:
        value = coordinate.evaluate(sample.variables)
        variables = dict(sample.variables) if keep_original else {}
        variables[coordinate.label] = value
        transformed.append(
            ResourceSample(
                variables=variables,
                resources=dict(sample.resources),
                metadata={**dict(sample.metadata), "representation": coordinate.label},
            )
        )
    return transformed


def search_representations(
    samples: Sequence[ResourceSample],
    target: str,
    *,
    complexity_penalty: float = 0.02,
    max_candidates: int = 128,
    seed: int = 0,
) -> tuple[RepresentationScore, ...]:
    """Rank generated coordinates by predictive compression.

    A linear empirical law is fitted in each one-dimensional coordinate and
    compared to a linear model in the original variables. ``score`` rewards CV
    error reduction while penalising representational description cost.
    """

    if len(samples) < 8:
        raise ValueError("representation search requires at least 8 samples")
    variables = tuple(sorted(samples[0].variables))
    if any(tuple(sorted(sample.variables)) != variables for sample in samples):
        raise ValueError("all samples must expose the same variable names")

    linear = ModelCandidate("linear", max_total_degree=1)
    baseline = cross_validated_rmse(samples, target, linear, seed=seed)
    denominator = max(abs(baseline), _EPS)
    rows: list[RepresentationScore] = []
    for candidate in generate_coordinate_candidates(variables, max_candidates=max_candidates):
        try:
            projected = transform_samples(samples, candidate)
            transformed = cross_validated_rmse(projected, target, linear, seed=seed)
            improvement = (baseline - transformed) / denominator
            score = improvement - complexity_penalty * candidate.complexity_cost
            rows.append(
                RepresentationScore(
                    coordinate=candidate,
                    baseline_cv_rmse=baseline,
                    transformed_cv_rmse=transformed,
                    relative_improvement=improvement,
                    score=score,
                )
            )
        except (ValueError, KeyError, OverflowError, ZeroDivisionError) as exc:
            rows.append(
                RepresentationScore(
                    coordinate=candidate,
                    baseline_cv_rmse=baseline,
                    transformed_cv_rmse=math.inf,
                    relative_improvement=-math.inf,
                    score=-math.inf,
                    valid=False,
                    note=f"{type(exc).__name__}: {exc}",
                )
            )
    return tuple(sorted(rows, key=lambda row: (-row.score, row.coordinate.label)))


def best_representation(
    samples: Sequence[ResourceSample],
    target: str,
    **kwargs: Any,
) -> RepresentationScore:
    rows = search_representations(samples, target, **kwargs)
    valid = [row for row in rows if row.valid]
    if not valid:
        raise ValueError("no valid representation candidate")
    return valid[0]
