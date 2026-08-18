from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import json
from typing import Iterable

_EPS = 1e-12


def _unit_interval(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")


def _non_negative(value: float, name: str) -> None:
    if value < 0.0:
        raise ValueError(f"{name} cannot be negative")


@dataclass(frozen=True)
class CapacityEnvelope:
    """Comparable verified-work capacities, expressed in the same units/time."""

    compute: float
    agents: float
    humans: float
    proof: float
    memory: float
    governance: float

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if value <= 0.0:
                raise ValueError(f"{name} capacity must be positive")

    @property
    def effective(self) -> float:
        return min(asdict(self).values())

    @property
    def bottleneck(self) -> str:
        values = asdict(self)
        return min(values, key=values.__getitem__)


@dataclass(frozen=True)
class PhaseState:
    """Dimensionless architecture state plus a comparable capacity envelope."""

    capacities: CapacityEnvelope
    residual_pressure: float
    debt_pressure: float
    latency_pressure: float
    compute_cost_pressure: float
    human_friction: float
    verified_capability_index: float
    regeneration_index: float
    independence_index: float
    observability_index: float
    human_dependency_index: float
    persistent_complexity: float

    def __post_init__(self) -> None:
        for name in (
            "residual_pressure",
            "debt_pressure",
            "latency_pressure",
            "compute_cost_pressure",
            "human_friction",
            "verified_capability_index",
            "regeneration_index",
            "independence_index",
            "observability_index",
            "human_dependency_index",
        ):
            _unit_interval(float(getattr(self, name)), name)
        if self.persistent_complexity <= 0.0:
            raise ValueError("persistent_complexity must be positive")


@dataclass(frozen=True)
class TransitionWeights:
    residual: float = 1.0
    debt: float = 1.0
    latency: float = 1.0
    compute_cost: float = 1.0
    human_friction: float = 1.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            _non_negative(float(value), name)
        if sum(asdict(self).values()) <= 0.0:
            raise ValueError("at least one transition weight must be positive")


@dataclass(frozen=True)
class PhasePolicy:
    critical_pressure: float = 0.65
    mutation_threshold: float = 0.75
    target_criticality: float = 0.90
    overload_criticality: float = 1.10
    reversibility_uncertainty_threshold: float = 0.30
    maximum_mutation_uncertainty: float = 0.65
    minimum_capacity_conservation: float = 0.98
    minimum_regeneration_conservation: float = 0.95

    def __post_init__(self) -> None:
        for name in (
            "critical_pressure",
            "target_criticality",
            "reversibility_uncertainty_threshold",
            "maximum_mutation_uncertainty",
            "minimum_capacity_conservation",
            "minimum_regeneration_conservation",
        ):
            _unit_interval(float(getattr(self, name)), name)
        if self.mutation_threshold < 0.0:
            raise ValueError("mutation_threshold cannot be negative")
        if self.overload_criticality <= self.target_criticality:
            raise ValueError("overload_criticality must exceed target_criticality")
        if self.maximum_mutation_uncertainty < self.reversibility_uncertainty_threshold:
            raise ValueError(
                "maximum_mutation_uncertainty must be at least the reversibility threshold"
            )


class PhaseAction(str, Enum):
    STAY = "STAY"
    COMPRESS_AND_VERIFY = "COMPRESS_AND_VERIFY"
    COMPRESS_AND_OBSERVE = "COMPRESS_AND_OBSERVE"
    MUTATE = "MUTATE"
    THROTTLE_GENERATION = "THROTTLE_GENERATION"


class PhaseLabel(str, Enum):
    HUMAN_CENTRIC = "HUMAN_CENTRIC"
    TOOL_AUGMENTED = "TOOL_AUGMENTED"
    AGENTIC = "AGENTIC"
    DISTRIBUTED = "DISTRIBUTED"
    SELF_RENORMALIZING = "SELF_RENORMALIZING"
    REGENERATIVE = "REGENERATIVE"


@dataclass(frozen=True)
class PhaseDecision:
    phase: PhaseLabel
    action: PhaseAction
    transition_pressure: float
    distance_to_transition: float
    mutation_score: float
    criticality_ratio: float
    order_parameter: float
    absorption_capacity: float
    bottleneck: str
    evidence_temperature: float
    reversible_required: bool
    automatic_execution: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["phase"] = self.phase.value
        payload["action"] = self.action.value
        payload["reasons"] = list(self.reasons)
        return payload


@dataclass(frozen=True)
class MutationCandidate:
    name: str
    expected_residual_reduction: float
    verified_capability_after: float
    migration_cost: float
    migration_risk: float
    induced_debt: float
    reversibility: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("candidate name cannot be empty")
        _unit_interval(self.expected_residual_reduction, "expected_residual_reduction")
        _unit_interval(self.verified_capability_after, "verified_capability_after")
        _unit_interval(self.reversibility, "reversibility")
        for name in ("migration_cost", "migration_risk", "induced_debt"):
            _non_negative(float(getattr(self, name)), name)
        if self.migration_cost + self.migration_risk + self.induced_debt <= 0.0:
            raise ValueError("mutation cost+risk+debt denominator must be positive")

    def score(self, current: PhaseState) -> float:
        denominator = self.migration_cost + self.migration_risk + self.induced_debt
        capability_gain = max(
            0.0,
            self.verified_capability_after - current.verified_capability_index,
        )
        return (
            self.expected_residual_reduction
            * (1.0 + capability_gain)
            * (0.5 + 0.5 * self.reversibility)
            / denominator
        )


@dataclass(frozen=True)
class RegenerationAudit:
    capacity_conservation: float
    regeneration_conservation: float
    complexity_ratio: float
    passed: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        return payload


class PhaseEvolutionEngine:
    """Pure decision engine: it proposes phase actions and performs no mutation."""

    def __init__(
        self,
        policy: PhasePolicy | None = None,
        weights: TransitionWeights | None = None,
    ) -> None:
        self.policy = policy or PhasePolicy()
        self.weights = weights or TransitionWeights()

    def transition_pressure(self, state: PhaseState) -> float:
        weighted = (
            self.weights.residual * state.residual_pressure
            + self.weights.debt * state.debt_pressure
            + self.weights.latency * state.latency_pressure
            + self.weights.compute_cost * state.compute_cost_pressure
            + self.weights.human_friction * state.human_friction
        )
        normalizer = sum(asdict(self.weights).values())
        return weighted / normalizer

    @staticmethod
    def order_parameter(state: PhaseState) -> float:
        numerator = (
            state.verified_capability_index
            * state.regeneration_index
            * state.independence_index
            * state.observability_index
        )
        denominator = (
            1.0
            + state.debt_pressure
            + state.human_friction
            + state.human_dependency_index
        )
        return numerator / denominator

    @staticmethod
    def phase_label(order_parameter: float) -> PhaseLabel:
        if order_parameter < 0.05:
            return PhaseLabel.HUMAN_CENTRIC
        if order_parameter < 0.15:
            return PhaseLabel.TOOL_AUGMENTED
        if order_parameter < 0.30:
            return PhaseLabel.AGENTIC
        if order_parameter < 0.50:
            return PhaseLabel.DISTRIBUTED
        if order_parameter < 0.70:
            return PhaseLabel.SELF_RENORMALIZING
        return PhaseLabel.REGENERATIVE

    @staticmethod
    def mutation_score(
        expected_residual_reduction: float,
        migration_cost: float,
        migration_risk: float,
        induced_debt: float,
    ) -> float:
        _unit_interval(expected_residual_reduction, "expected_residual_reduction")
        for name, value in (
            ("migration_cost", migration_cost),
            ("migration_risk", migration_risk),
            ("induced_debt", induced_debt),
        ):
            _non_negative(value, name)
        denominator = migration_cost + migration_risk + induced_debt
        if denominator <= 0.0:
            raise ValueError("mutation cost+risk+debt denominator must be positive")
        return expected_residual_reduction / denominator

    def evaluate(
        self,
        state: PhaseState,
        *,
        generation_rate: float,
        expected_residual_reduction: float,
        migration_cost: float,
        migration_risk: float,
        induced_debt: float,
        uncertainty: float,
    ) -> PhaseDecision:
        _non_negative(generation_rate, "generation_rate")
        _unit_interval(uncertainty, "uncertainty")

        pressure = self.transition_pressure(state)
        absorption = state.capacities.effective
        criticality = generation_rate / absorption
        mutation = self.mutation_score(
            expected_residual_reduction,
            migration_cost,
            migration_risk,
            induced_debt,
        )
        order = self.order_parameter(state)
        phase = self.phase_label(order)
        distance = max(0.0, self.policy.critical_pressure - pressure)
        reasons: list[str] = []

        if criticality >= self.policy.overload_criticality:
            action = PhaseAction.THROTTLE_GENERATION
            reasons.append("generation exceeds verified absorption capacity")
        elif pressure >= self.policy.critical_pressure:
            if (
                mutation >= self.policy.mutation_threshold
                and uncertainty <= self.policy.maximum_mutation_uncertainty
            ):
                action = PhaseAction.MUTATE
                reasons.append("transition pressure is critical")
                reasons.append("candidate mutation clears residual-reduction threshold")
            else:
                action = PhaseAction.COMPRESS_AND_OBSERVE
                reasons.append("transition pressure is critical")
                if mutation < self.policy.mutation_threshold:
                    reasons.append("mutation evidence is insufficient")
                if uncertainty > self.policy.maximum_mutation_uncertainty:
                    reasons.append("mutation uncertainty exceeds promotion ceiling")
        elif criticality >= self.policy.target_criticality:
            action = PhaseAction.COMPRESS_AND_VERIFY
            reasons.append("system is operating near verified absorption limit")
        else:
            action = PhaseAction.STAY
            reasons.append("current regime remains below transition thresholds")

        reversible_required = (
            uncertainty >= self.policy.reversibility_uncertainty_threshold
            or action in {PhaseAction.MUTATE, PhaseAction.THROTTLE_GENERATION}
        )
        if reversible_required:
            reasons.append("reversibility gate is required")

        return PhaseDecision(
            phase=phase,
            action=action,
            transition_pressure=pressure,
            distance_to_transition=distance,
            mutation_score=mutation,
            criticality_ratio=criticality,
            order_parameter=order,
            absorption_capacity=absorption,
            bottleneck=state.capacities.bottleneck,
            evidence_temperature=uncertainty,
            reversible_required=reversible_required,
            automatic_execution=False,
            reasons=tuple(reasons),
        )

    def audit_regeneration(
        self,
        before: PhaseState,
        after: PhaseState,
    ) -> RegenerationAudit:
        if before.verified_capability_index <= _EPS:
            capacity_conservation = 1.0 if after.verified_capability_index <= _EPS else float("inf")
        else:
            capacity_conservation = (
                after.verified_capability_index / before.verified_capability_index
            )

        if before.regeneration_index <= _EPS:
            regeneration_conservation = 1.0 if after.regeneration_index <= _EPS else float("inf")
        else:
            regeneration_conservation = after.regeneration_index / before.regeneration_index

        complexity_ratio = after.persistent_complexity / before.persistent_complexity
        reasons: list[str] = []
        if capacity_conservation < self.policy.minimum_capacity_conservation:
            reasons.append("verified capability loss exceeds conservation gate")
        if regeneration_conservation < self.policy.minimum_regeneration_conservation:
            reasons.append("regeneration loss exceeds conservation gate")
        if not reasons and complexity_ratio < 1.0:
            reasons.append("structure reduced while guarded capability was conserved")
        if not reasons:
            reasons.append("transition conserves guarded capability and regeneration")

        return RegenerationAudit(
            capacity_conservation=capacity_conservation,
            regeneration_conservation=regeneration_conservation,
            complexity_ratio=complexity_ratio,
            passed=not any("loss exceeds" in reason for reason in reasons),
            reasons=tuple(reasons),
        )

    @staticmethod
    def rank_mutations(
        current: PhaseState,
        candidates: Iterable[MutationCandidate],
    ) -> tuple[MutationCandidate, ...]:
        return tuple(
            sorted(candidates, key=lambda item: (-item.score(current), item.name))
        )


def _demo_state(*, critical: bool) -> PhaseState:
    return PhaseState(
        capacities=CapacityEnvelope(
            compute=140.0,
            agents=120.0,
            humans=80.0,
            proof=60.0,
            memory=100.0,
            governance=75.0,
        ),
        residual_pressure=0.92 if critical else 0.25,
        debt_pressure=0.82 if critical else 0.20,
        latency_pressure=0.75 if critical else 0.20,
        compute_cost_pressure=0.60 if critical else 0.25,
        human_friction=0.70 if critical else 0.20,
        verified_capability_index=0.78,
        regeneration_index=0.72,
        independence_index=0.66,
        observability_index=0.82,
        human_dependency_index=0.28,
        persistent_complexity=1.0,
    )


def demo() -> dict[str, object]:
    engine = PhaseEvolutionEngine()
    stable = _demo_state(critical=False)
    critical = _demo_state(critical=True)
    decision = engine.evaluate(
        critical,
        generation_rate=55.0,
        expected_residual_reduction=0.80,
        migration_cost=0.20,
        migration_risk=0.15,
        induced_debt=0.10,
        uncertainty=0.45,
    )
    distilled = PhaseState(
        **{
            **asdict(stable),
            "capacities": stable.capacities,
            "verified_capability_index": 0.79,
            "regeneration_index": 0.75,
            "persistent_complexity": 0.72,
        }
    )
    audit = engine.audit_regeneration(stable, distilled)
    return {
        "status": "proposal_only",
        "phase_decision": decision.to_dict(),
        "regeneration_audit": audit.to_dict(),
        "authority": {
            "automatic_execution": False,
            "automatic_merge": False,
            "human_approval_required_for_irreversible_change": True,
        },
    }


def main() -> int:
    print(json.dumps(demo(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
