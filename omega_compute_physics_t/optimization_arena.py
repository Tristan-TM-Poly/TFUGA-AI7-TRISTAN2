"""Evidence arena for comparing baseline and optimization variants in R0.7."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class VariantEvidence:
    variant_id: str
    resources: Mapping[str, float]
    correctness_passed: bool = True
    confidence: float = 1.0
    change_risk: float = 0.0


@dataclass(frozen=True)
class VariantScore:
    variant_id: str
    utility: float
    pareto: bool
    eligible: bool
    status: str
    oak_warning: str = (
        "Arena scores summarize supplied finite-domain measurements. A winner "
        "is not automatically globally optimal, causally explained, or "
        "asymptotically superior."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OptimizationArenaReport:
    baseline_id: str
    scores: tuple[VariantScore, ...]
    pareto_front: tuple[str, ...]
    best_variant: str | None
    status: str = "measured-optimization-arena"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_variant(row: VariantEvidence, directions: Mapping[str, str]) -> None:
    if not 0.0 <= row.confidence <= 1.0:
        raise ValueError("confidence must be in [0, 1]")
    if not 0.0 <= row.change_risk <= 1.0:
        raise ValueError("change_risk must be in [0, 1]")
    for metric, direction in directions.items():
        if direction not in {"minimize", "maximize"}:
            raise ValueError(f"invalid direction for {metric}: {direction}")
        if metric not in row.resources:
            raise ValueError(f"missing resource metric: {metric}")
        value = float(row.resources[metric])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"metric {metric} must be finite and non-negative")


def _dominates(a: VariantEvidence, b: VariantEvidence, directions: Mapping[str, str]) -> bool:
    at_least = True
    strict = False
    for metric, direction in directions.items():
        av = float(a.resources[metric])
        bv = float(b.resources[metric])
        if direction == "minimize":
            at_least &= av <= bv
            strict |= av < bv
        else:
            at_least &= av >= bv
            strict |= av > bv
    return bool(at_least and strict)


def run_optimization_arena(
    baseline: VariantEvidence,
    variants: Sequence[VariantEvidence],
    *,
    directions: Mapping[str, str],
) -> OptimizationArenaReport:
    rows = (baseline, *tuple(variants))
    for row in rows:
        _validate_variant(row, directions)
    eligible = tuple(row for row in rows if row.correctness_passed)
    pareto_ids = tuple(
        row.variant_id
        for row in eligible
        if not any(_dominates(other, row, directions) for other in eligible if other is not row)
    )

    scores: list[VariantScore] = []
    for row in rows:
        if not row.correctness_passed:
            scores.append(VariantScore(row.variant_id, float("-inf"), False, False, "correctness-failed"))
            continue
        ratios: list[float] = []
        for metric, direction in directions.items():
            base = float(baseline.resources[metric])
            value = float(row.resources[metric])
            if direction == "minimize":
                ratio = (base + 1e-12) / (value + 1e-12)
            else:
                ratio = (value + 1e-12) / (base + 1e-12)
            ratios.append(max(ratio, 1e-12))
        geometric_utility = math.exp(sum(math.log(r) for r in ratios) / max(1, len(ratios)))
        utility = geometric_utility * row.confidence * (1.0 - 0.5 * row.change_risk)
        scores.append(
            VariantScore(
                variant_id=row.variant_id,
                utility=utility,
                pareto=row.variant_id in pareto_ids,
                eligible=True,
                status="eligible-measured-variant",
            )
        )

    candidates = [row for row in scores if row.eligible and row.variant_id != baseline.variant_id]
    best = max(candidates, key=lambda row: row.utility).variant_id if candidates else None
    return OptimizationArenaReport(
        baseline_id=baseline.variant_id,
        scores=tuple(scores),
        pareto_front=pareto_ids,
        best_variant=best,
    )
