"""Meta-generation, automation and crystallization controls for R6."""
from __future__ import annotations

from dataclasses import dataclass

from .models import Crystal, GeneratorSpec, NarrativeResidual, PromotionDecision


@dataclass(frozen=True)
class ImprovementCandidate:
    improvement_id: str
    target: str
    hypothesis: str
    predicted_gain: float
    cost: float
    risk: float
    complexity: float
    benchmark: str

    @property
    def utility(self) -> float:
        denominator = self.cost + self.risk + self.complexity
        return self.predicted_gain / denominator if denominator > 0 else 0.0


class GeneratorRegistry:
    def __init__(self, specs: tuple[GeneratorSpec, ...] = ()) -> None:
        self._specs: dict[str, GeneratorSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: GeneratorSpec) -> None:
        errors = spec.validate()
        if errors:
            raise ValueError("; ".join(errors))
        self._specs[spec.generator_id] = spec

    def get(self, generator_id: str) -> GeneratorSpec:
        return self._specs[generator_id]

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs))

    def coalition_for(self, required_outputs: tuple[str, ...]) -> tuple[str, ...]:
        remaining = set(required_outputs)
        selected: list[str] = []
        for spec in sorted(self._specs.values(), key=lambda item: (item.cost_units, item.generator_id)):
            contribution = remaining.intersection(spec.outputs)
            if contribution:
                selected.append(spec.generator_id)
                remaining.difference_update(contribution)
            if not remaining:
                break
        if remaining:
            raise ValueError(f"no generator coverage for outputs: {sorted(remaining)}")
        return tuple(selected)


def propose_generator_from_residual(residual: NarrativeResidual) -> GeneratorSpec:
    generator_id = residual.proposed_generator or f"GeneratorFor-{residual.domain}-{residual.scale}"
    return GeneratorSpec(
        generator_id=generator_id,
        purpose=f"Reduce residual {residual.residual_id}: {residual.description}",
        inputs=(residual.domain, residual.scale, "StoryIR"),
        outputs=(f"resolved:{residual.domain}",),
        verifier_ids=(f"Judge:{residual.domain}",),
        cost_units=max(1, residual.severity),
        experimental=True,
    )


def rank_improvements(candidates: tuple[ImprovementCandidate, ...]) -> tuple[ImprovementCandidate, ...]:
    return tuple(sorted(candidates, key=lambda item: (-item.utility, item.improvement_id)))


def meta_depth_allowed(verified_gain: float, added_complexity: float, added_risk: float) -> bool:
    return verified_gain > (added_complexity + added_risk) and verified_gain > 0


def automation_value(future_work_eliminated: float, reliability: float, implementation_cost: float, risk: float) -> float:
    denominator = implementation_cost + risk
    return (future_work_eliminated * reliability) / denominator if denominator > 0 else 0.0


def crystallization_decision(
    *, verified_gain: float, benchmark_passed: bool, rollback_defined: bool,
    complexity_delta: float, known_regression: bool = False
) -> PromotionDecision:
    if known_regression:
        return PromotionDecision.DESTROY
    if not benchmark_passed or not rollback_defined:
        return PromotionDecision.KEEP_EXPERIMENTAL
    if verified_gain <= 0:
        return PromotionDecision.DEPRECATE
    if complexity_delta > verified_gain:
        return PromotionDecision.KEEP_EXPERIMENTAL
    return PromotionDecision.PROMOTE


def make_crystal(
    crystal_id: str, capability: str, implementation: str,
    evidence: tuple[str, ...], benchmarks: tuple[str, ...], rollback: str,
    dependencies: tuple[str, ...] = (), limits: tuple[str, ...] = ()
) -> Crystal:
    crystal = Crystal(
        crystal_id=crystal_id,
        capability=capability,
        implementation=implementation,
        evidence=evidence,
        benchmarks=benchmarks,
        dependencies=dependencies,
        limits=limits,
        rollback=rollback,
    )
    errors = crystal.validate()
    if errors:
        raise ValueError("; ".join(errors))
    return crystal
