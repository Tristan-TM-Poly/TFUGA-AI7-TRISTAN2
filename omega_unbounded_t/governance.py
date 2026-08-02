from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import uuid


@dataclass(frozen=True)
class StopPolicy:
    """Evidence-based stopping policy with no arbitrary iteration ceiling."""

    minimum_marginal_information: float = 0.02
    maximum_repetition_score: float = 0.90
    maximum_equivalent_validations: int = 2
    maximum_stagnant_observations: int = 2

    def __post_init__(self) -> None:
        if not 0.0 <= self.minimum_marginal_information <= 1.0:
            raise ValueError("minimum_marginal_information must be between 0 and 1")
        if not 0.0 <= self.maximum_repetition_score <= 1.0:
            raise ValueError("maximum_repetition_score must be between 0 and 1")
        if self.maximum_equivalent_validations < 1:
            raise ValueError("maximum_equivalent_validations must be positive")
        if self.maximum_stagnant_observations < 1:
            raise ValueError("maximum_stagnant_observations must be positive")


@dataclass(frozen=True)
class IterationObservation:
    objective_reached: bool
    authoritative_validation: bool
    marginal_information_gain: float
    repetition_score: float
    validation_fingerprint: str | None = None
    critical_new_risk: bool = False
    user_interrupt: bool = False
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.marginal_information_gain <= 1.0:
            raise ValueError("marginal_information_gain must be between 0 and 1")
        if not 0.0 <= self.repetition_score <= 1.0:
            raise ValueError("repetition_score must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StopDecision:
    action: str
    reasons: tuple[str, ...]
    priority: int
    observation_count: int
    equivalent_validations: int
    stagnant_observations: int

    @property
    def should_stop(self) -> bool:
        return self.action == "STOP"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["should_stop"] = self.should_stop
        return payload


class StopGate:
    """Stops when proof is sufficient and additional work becomes repetitive.

    A user interruption always wins. A newly discovered critical risk keeps the
    investigation open unless the user explicitly interrupts it.
    """

    def __init__(self, policy: StopPolicy | None = None):
        self.policy = policy or StopPolicy()
        self.history: list[IterationObservation] = []

    def observe(self, observation: IterationObservation) -> StopDecision:
        self.history.append(observation)
        return self._decide(observation)

    def _decide(self, observation: IterationObservation) -> StopDecision:
        equivalent = self._equivalent_validations(observation.validation_fingerprint)
        stagnant = self._stagnant_observations()

        if observation.user_interrupt:
            return StopDecision(
                action="STOP",
                reasons=("explicit user interruption has absolute priority",),
                priority=100,
                observation_count=len(self.history),
                equivalent_validations=equivalent,
                stagnant_observations=stagnant,
            )

        if observation.critical_new_risk:
            return StopDecision(
                action="CONTINUE",
                reasons=("a critical new risk requires investigation before closure",),
                priority=90,
                observation_count=len(self.history),
                equivalent_validations=equivalent,
                stagnant_observations=stagnant,
            )

        if observation.objective_reached and observation.authoritative_validation:
            if equivalent >= self.policy.maximum_equivalent_validations:
                return StopDecision(
                    action="STOP",
                    reasons=("equivalent authoritative validation limit reached",),
                    priority=80,
                    observation_count=len(self.history),
                    equivalent_validations=equivalent,
                    stagnant_observations=stagnant,
                )
            if (
                observation.marginal_information_gain
                <= self.policy.minimum_marginal_information
                and observation.repetition_score >= self.policy.maximum_repetition_score
            ):
                return StopDecision(
                    action="STOP",
                    reasons=(
                        "objective reached with authoritative validation",
                        "marginal information is low and repetition is high",
                    ),
                    priority=75,
                    observation_count=len(self.history),
                    equivalent_validations=equivalent,
                    stagnant_observations=stagnant,
                )
            if stagnant >= self.policy.maximum_stagnant_observations:
                return StopDecision(
                    action="STOP",
                    reasons=(
                        "objective reached with authoritative validation",
                        "marginal information remained stagnant",
                    ),
                    priority=70,
                    observation_count=len(self.history),
                    equivalent_validations=equivalent,
                    stagnant_observations=stagnant,
                )

        return StopDecision(
            action="CONTINUE",
            reasons=("stopping evidence is not yet sufficient",),
            priority=0,
            observation_count=len(self.history),
            equivalent_validations=equivalent,
            stagnant_observations=stagnant,
        )

    def _equivalent_validations(self, fingerprint: str | None) -> int:
        if not fingerprint:
            return 0
        return sum(
            1
            for item in self.history
            if item.authoritative_validation and item.validation_fingerprint == fingerprint
        )

    def _stagnant_observations(self) -> int:
        count = 0
        for item in reversed(self.history):
            if item.marginal_information_gain <= self.policy.minimum_marginal_information:
                count += 1
                continue
            break
        return count


@dataclass(frozen=True)
class ReflexRule:
    event_id: str
    timestamp: str
    trigger: str
    blocked_action: str
    symptom: tuple[str, ...]
    cause: tuple[str, ...]
    correction: tuple[str, ...]
    regression_test: tuple[str, ...]
    scope: tuple[str, ...]
    active: bool = True
    status: str = "negative_memory_rule"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReflexMemoryLedger:
    """Append-only M-minus rules that can block known failure patterns."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self.rules: list[ReflexRule] = []
        if self.path is not None and self.path.exists():
            self._load_existing()

    def record(
        self,
        *,
        trigger: str,
        blocked_action: str,
        symptom: Sequence[str],
        cause: Sequence[str],
        correction: Sequence[str],
        regression_test: Sequence[str],
        scope: Sequence[str],
    ) -> ReflexRule:
        if not trigger.strip() or not blocked_action.strip():
            raise ValueError("trigger and blocked_action cannot be empty")
        rule = ReflexRule(
            event_id=f"M-REFLEX-{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            trigger=trigger,
            blocked_action=blocked_action,
            symptom=tuple(str(item) for item in symptom),
            cause=tuple(str(item) for item in cause),
            correction=tuple(str(item) for item in correction),
            regression_test=tuple(str(item) for item in regression_test),
            scope=tuple(str(item) for item in scope),
        )
        self.rules.append(rule)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(rule.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return rule

    def record_overiteration(self) -> ReflexRule:
        return self.record(
            trigger="objective_reached_and_authoritative_validation_obtained",
            blocked_action="repeat_equivalent_validation",
            symptom=("continued iteration after sufficient proof", "repeated equivalent checks"),
            cause=("missing stop priority", "new work was not required to resolve a material risk"),
            correction=("invoke StopGate", "stop before a third equivalent validation"),
            regression_test=("no_third_equivalent_validation", "user_interrupt_stops_immediately"),
            scope=("assistant", "ci", "agents", "self_improvement_lab"),
        )

    def block_reasons(self, action: str, *, trigger: str | None = None) -> tuple[str, ...]:
        return tuple(
            rule.event_id
            for rule in self.rules
            if rule.active
            and rule.blocked_action == action
            and (trigger is None or rule.trigger == trigger)
        )

    def is_blocked(self, action: str, *, trigger: str | None = None) -> bool:
        return bool(self.block_reasons(action, trigger=trigger))

    def _load_existing(self) -> None:
        assert self.path is not None
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            payload = json.loads(raw)
            self.rules.append(
                ReflexRule(
                    event_id=str(payload["event_id"]),
                    timestamp=str(payload["timestamp"]),
                    trigger=str(payload["trigger"]),
                    blocked_action=str(payload["blocked_action"]),
                    symptom=tuple(payload.get("symptom", ())),
                    cause=tuple(payload.get("cause", ())),
                    correction=tuple(payload.get("correction", ())),
                    regression_test=tuple(payload.get("regression_test", ())),
                    scope=tuple(payload.get("scope", ())),
                    active=bool(payload.get("active", True)),
                    status=str(payload.get("status", "negative_memory_rule")),
                )
            )


@dataclass(frozen=True)
class ObjectiveVector:
    """Named multi-objective point for Pareto selection."""

    name: str
    maximize: Mapping[str, float] = field(default_factory=dict)
    minimize: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("objective-vector name cannot be empty")
        if not self.maximize and not self.minimize:
            raise ValueError("at least one objective is required")
        overlap = set(self.maximize).intersection(self.minimize)
        if overlap:
            raise ValueError(f"objectives cannot be both maximized and minimized: {sorted(overlap)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "maximize": dict(self.maximize),
            "minimize": dict(self.minimize),
            "metadata": dict(self.metadata),
        }


def dominates(left: ObjectiveVector, right: ObjectiveVector, *, tolerance: float = 1e-12) -> bool:
    if set(left.maximize) != set(right.maximize) or set(left.minimize) != set(right.minimize):
        raise ValueError("Pareto points must use the same objective keys")

    no_worse = all(
        float(left.maximize[key]) + tolerance >= float(right.maximize[key])
        for key in left.maximize
    ) and all(
        float(left.minimize[key]) <= float(right.minimize[key]) + tolerance
        for key in left.minimize
    )
    strictly_better = any(
        float(left.maximize[key]) > float(right.maximize[key]) + tolerance
        for key in left.maximize
    ) or any(
        float(left.minimize[key]) + tolerance < float(right.minimize[key])
        for key in left.minimize
    )
    return no_worse and strictly_better


def pareto_front(points: Iterable[ObjectiveVector]) -> tuple[ObjectiveVector, ...]:
    materialized = tuple(points)
    return tuple(
        point
        for index, point in enumerate(materialized)
        if not any(
            dominates(other, point)
            for other_index, other in enumerate(materialized)
            if other_index != index
        )
    )
