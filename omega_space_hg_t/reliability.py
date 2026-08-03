"""R0.4 reliability, radiation and FDIR research models for Ω-SPACE-HG-T∞."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from math import exp, log, sqrt
from typing import Any, Iterable, Literal, Sequence


GateKind = Literal["leaf", "and", "or", "k_of_n"]


def deterministic_uniform(seed: int, stream: str, index: int = 0) -> float:
    payload = f"{seed}:{stream}:{index}".encode("utf-8")
    value = int.from_bytes(sha256(payload).digest()[:8], "big")
    return (value + 0.5) / 2**64


def exponential_failure_probability(rate_per_hour: float, duration_hours: float) -> float:
    if rate_per_hour < 0.0 or duration_hours < 0.0:
        raise ValueError("rate and duration cannot be negative")
    return 1.0 - exp(-rate_per_hour * duration_hours)


def exponential_failure_time_hours(rate_per_hour: float, seed: int, stream: str) -> float:
    if rate_per_hour < 0.0:
        raise ValueError("failure rate cannot be negative")
    if rate_per_hour == 0.0:
        return float("inf")
    u = deterministic_uniform(seed, stream)
    return -log(1.0 - u) / rate_per_hour


@dataclass(frozen=True)
class ComponentReliability:
    component_id: str
    function_id: str
    failure_rate_per_hour: float
    critical: bool = True
    redundancy_group: str | None = None
    common_cause_group: str | None = None
    detection_coverage: float = 1.0
    recovery_probability: float = 0.0

    def validate(self) -> None:
        if not self.component_id or not self.function_id:
            raise ValueError("component and function ids cannot be empty")
        if self.failure_rate_per_hour < 0.0:
            raise ValueError("failure rate cannot be negative")
        for value in (self.detection_coverage, self.recovery_probability):
            if not 0.0 <= value <= 1.0:
                raise ValueError("coverage and recovery probabilities must lie in [0, 1]")


@dataclass(frozen=True)
class CommonCauseModel:
    group_id: str
    failure_rate_per_hour: float
    affected_components: tuple[str, ...]
    detection_coverage: float = 1.0
    recovery_probability: float = 0.0

    def validate(self) -> None:
        if not self.group_id or not self.affected_components:
            raise ValueError("common-cause group requires an id and affected components")
        if self.failure_rate_per_hour < 0.0:
            raise ValueError("common-cause rate cannot be negative")
        for value in (self.detection_coverage, self.recovery_probability):
            if not 0.0 <= value <= 1.0:
                raise ValueError("coverage and recovery probabilities must lie in [0, 1]")


@dataclass(frozen=True)
class RadiationEnvironment:
    particle_flux_cm2_s: float
    device_cross_section_cm2: float
    device_count: int
    shielding_attenuation: float = 1.0
    recovery_probability: float = 0.95

    def validate(self) -> None:
        if self.particle_flux_cm2_s < 0.0 or self.device_cross_section_cm2 < 0.0:
            raise ValueError("radiation flux and cross-section cannot be negative")
        if self.device_count < 0:
            raise ValueError("device count cannot be negative")
        if not 0.0 <= self.shielding_attenuation <= 1.0:
            raise ValueError("shielding attenuation must lie in [0, 1]")
        if not 0.0 <= self.recovery_probability <= 1.0:
            raise ValueError("recovery probability must lie in [0, 1]")

    def expected_events(self, duration_s: float) -> float:
        self.validate()
        if duration_s < 0.0:
            raise ValueError("duration cannot be negative")
        return (
            self.particle_flux_cm2_s
            * self.device_cross_section_cm2
            * self.device_count
            * self.shielding_attenuation
            * duration_s
        )


def poisson_sample(expected_events: float, seed: int, stream: str) -> int:
    if expected_events < 0.0:
        raise ValueError("expected events cannot be negative")
    if expected_events == 0.0:
        return 0
    u = deterministic_uniform(seed, stream)
    probability = exp(-expected_events)
    cumulative = probability
    count = 0
    while u > cumulative and count < 100000:
        count += 1
        probability *= expected_events / count
        cumulative += probability
        if probability == 0.0:
            break
    return count


@dataclass(frozen=True)
class FaultTreeNode:
    node_id: str
    kind: GateKind
    children: tuple["FaultTreeNode", ...] = ()
    leaf_probability: float | None = None
    threshold: int | None = None

    def validate(self) -> None:
        if not self.node_id:
            raise ValueError("fault-tree node id cannot be empty")
        if self.kind == "leaf":
            if self.children or self.leaf_probability is None:
                raise ValueError("leaf requires a probability and no children")
            if not 0.0 <= self.leaf_probability <= 1.0:
                raise ValueError("leaf probability must lie in [0, 1]")
        else:
            if not self.children:
                raise ValueError("gate requires children")
            if self.kind == "k_of_n":
                if self.threshold is None or not 1 <= self.threshold <= len(self.children):
                    raise ValueError("invalid k-of-n threshold")
            for child in self.children:
                child.validate()

    def probability(self) -> float:
        self.validate()
        if self.kind == "leaf":
            return float(self.leaf_probability)
        probabilities = [child.probability() for child in self.children]
        if self.kind == "and":
            result = 1.0
            for value in probabilities:
                result *= value
            return result
        if self.kind == "or":
            survival = 1.0
            for value in probabilities:
                survival *= 1.0 - value
            return 1.0 - survival
        threshold = int(self.threshold)
        distribution = [1.0] + [0.0] * len(probabilities)
        for value in probabilities:
            next_distribution = [0.0] * len(distribution)
            for failures, probability in enumerate(distribution):
                next_distribution[failures] += probability * (1.0 - value)
                if failures + 1 < len(distribution):
                    next_distribution[failures + 1] += probability * value
            distribution = next_distribution
        return sum(distribution[threshold:])


@dataclass(frozen=True)
class FailureEvent:
    event_id: str
    epoch_hour: float
    source: str
    affected_components: tuple[str, ...]
    detected: bool
    recovered: bool
    critical_effect: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


FDIRMode = Literal["BOOT", "NOMINAL", "DEGRADED", "SAFE", "RECOVERY", "FAILED"]


@dataclass(frozen=True)
class FDIRPolicy:
    safe_mode_soc_threshold: float = 0.20
    recovery_soc_threshold: float = 0.35
    maximum_recovery_attempts: int = 3

    def validate(self) -> None:
        if not 0.0 <= self.safe_mode_soc_threshold <= self.recovery_soc_threshold <= 1.0:
            raise ValueError("invalid FDIR SOC thresholds")
        if self.maximum_recovery_attempts < 0:
            raise ValueError("maximum recovery attempts cannot be negative")


@dataclass(frozen=True)
class FDIRState:
    mode: FDIRMode = "BOOT"
    active_failures: tuple[str, ...] = ()
    recovery_attempts: int = 0
    epoch_hour: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fdir_transition(
    state: FDIRState,
    policy: FDIRPolicy,
    *,
    battery_soc: float,
    detected_failures: Iterable[str] = (),
    recovered_failures: Iterable[str] = (),
    command_recovery: bool = False,
    unrecoverable_critical_failure: bool = False,
    dt_hours: float = 0.0,
) -> FDIRState:
    policy.validate()
    if not 0.0 <= battery_soc <= 1.0 or dt_hours < 0.0:
        raise ValueError("invalid FDIR resources or step")
    active = set(state.active_failures)
    active.update(detected_failures)
    active.difference_update(recovered_failures)
    attempts = state.recovery_attempts

    if unrecoverable_critical_failure:
        mode: FDIRMode = "FAILED"
    elif state.mode == "BOOT":
        mode = "SAFE" if active or battery_soc < policy.safe_mode_soc_threshold else "NOMINAL"
    elif battery_soc < policy.safe_mode_soc_threshold:
        mode = "SAFE"
    elif active:
        if command_recovery and attempts < policy.maximum_recovery_attempts:
            mode = "RECOVERY"
            attempts += 1
        elif state.mode == "RECOVERY" and attempts >= policy.maximum_recovery_attempts:
            mode = "FAILED"
        else:
            mode = "DEGRADED"
    elif state.mode in ("SAFE", "DEGRADED", "RECOVERY") and battery_soc >= policy.recovery_soc_threshold:
        mode = "NOMINAL"
        attempts = 0
    else:
        mode = "NOMINAL"

    return FDIRState(mode, tuple(sorted(active)), attempts, state.epoch_hour + dt_hours)


@dataclass(frozen=True)
class TrialResult:
    trial_index: int
    seed: int
    mission_success: bool
    events: tuple[FailureEvent, ...]
    failed_functions: tuple[str, ...]
    detected_events: int
    recovered_events: int
    entered_safe_mode: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "trial_index": self.trial_index,
            "seed": self.seed,
            "mission_success": self.mission_success,
            "events": [event.to_dict() for event in self.events],
            "failed_functions": list(self.failed_functions),
            "detected_events": self.detected_events,
            "recovered_events": self.recovered_events,
            "entered_safe_mode": self.entered_safe_mode,
        }


def _bernoulli(probability: float, seed: int, stream: str) -> bool:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must lie in [0, 1]")
    return deterministic_uniform(seed, stream) < probability


def simulate_reliability_trial(
    components: Sequence[ComponentReliability],
    duration_hours: float,
    seed: int,
    *,
    common_causes: Sequence[CommonCauseModel] = (),
    radiation: RadiationEnvironment | None = None,
    trial_index: int = 0,
) -> TrialResult:
    if duration_hours <= 0.0:
        raise ValueError("duration must be positive")
    by_id = {component.component_id: component for component in components}
    if len(by_id) != len(components):
        raise ValueError("component ids must be unique")
    for component in components:
        component.validate()
    for common_cause in common_causes:
        common_cause.validate()
        if any(component_id not in by_id for component_id in common_cause.affected_components):
            raise ValueError("common-cause model references an unknown component")

    events: list[FailureEvent] = []
    failed_components: set[str] = set()
    recovered_components: set[str] = set()

    for component in components:
        failure_time = exponential_failure_time_hours(
            component.failure_rate_per_hour,
            seed,
            f"component:{component.component_id}",
        )
        if failure_time <= duration_hours:
            detected = _bernoulli(component.detection_coverage, seed, f"detect:{component.component_id}")
            recovered = detected and _bernoulli(
                component.recovery_probability,
                seed,
                f"recover:{component.component_id}",
            )
            failed_components.add(component.component_id)
            if recovered:
                recovered_components.add(component.component_id)
            events.append(
                FailureEvent(
                    f"component:{component.component_id}",
                    failure_time,
                    "component",
                    (component.component_id,),
                    detected,
                    recovered,
                    component.critical,
                )
            )

    for model in common_causes:
        failure_time = exponential_failure_time_hours(
            model.failure_rate_per_hour,
            seed,
            f"ccf:{model.group_id}",
        )
        if failure_time <= duration_hours:
            detected = _bernoulli(model.detection_coverage, seed, f"ccf-detect:{model.group_id}")
            recovered = detected and _bernoulli(
                model.recovery_probability,
                seed,
                f"ccf-recover:{model.group_id}",
            )
            failed_components.update(model.affected_components)
            if recovered:
                recovered_components.update(model.affected_components)
            critical = any(by_id[item].critical for item in model.affected_components)
            events.append(
                FailureEvent(
                    f"ccf:{model.group_id}",
                    failure_time,
                    "common_cause",
                    tuple(sorted(model.affected_components)),
                    detected,
                    recovered,
                    critical,
                )
            )

    if radiation is not None:
        expected = radiation.expected_events(duration_hours * 3600.0)
        count = poisson_sample(expected, seed, "radiation-count")
        for index in range(count):
            if not components:
                break
            component_index = min(
                len(components) - 1,
                int(deterministic_uniform(seed, "radiation-target", index) * len(components)),
            )
            component = components[component_index]
            epoch = deterministic_uniform(seed, "radiation-epoch", index) * duration_hours
            recovered = _bernoulli(
                radiation.recovery_probability,
                seed,
                f"radiation-recover:{index}",
            )
            failed_components.add(component.component_id)
            if recovered:
                recovered_components.add(component.component_id)
            events.append(
                FailureEvent(
                    f"radiation:{index}",
                    epoch,
                    "radiation",
                    (component.component_id,),
                    True,
                    recovered,
                    component.critical,
                )
            )

    active_failed = failed_components - recovered_components
    functions: dict[str, list[ComponentReliability]] = {}
    for component in components:
        functions.setdefault(component.function_id, []).append(component)
    failed_functions: list[str] = []
    for function_id, members in functions.items():
        if any(member.critical for member in members) and all(
            member.component_id in active_failed for member in members
        ):
            failed_functions.append(function_id)

    events.sort(key=lambda event: (event.epoch_hour, event.event_id))
    return TrialResult(
        trial_index=trial_index,
        seed=seed,
        mission_success=not failed_functions,
        events=tuple(events),
        failed_functions=tuple(sorted(failed_functions)),
        detected_events=sum(event.detected for event in events),
        recovered_events=sum(event.recovered for event in events),
        entered_safe_mode=any(event.detected and event.critical_effect for event in events),
    )


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("invalid binomial counts")
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2.0 * trials)) / denominator
    radius = (
        z
        * sqrt(proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials))
        / denominator
    )
    return max(0.0, center - radius), min(1.0, center + radius)


def run_reliability_campaign(
    components: Sequence[ComponentReliability],
    duration_hours: float,
    *,
    start_offset: int = 0,
    count: int = 1024,
    base_seed: int = 2026,
    common_causes: Sequence[CommonCauseModel] = (),
    radiation: RadiationEnvironment | None = None,
    retain_failure_witnesses: int = 16,
) -> dict[str, Any]:
    if start_offset < 0 or count <= 0 or retain_failure_witnesses < 0:
        raise ValueError("invalid campaign offsets or counts")
    trials = tuple(
        simulate_reliability_trial(
            components,
            duration_hours,
            base_seed + start_offset + index,
            common_causes=common_causes,
            radiation=radiation,
            trial_index=start_offset + index,
        )
        for index in range(count)
    )
    successes = sum(trial.mission_success for trial in trials)
    total_events = sum(len(trial.events) for trial in trials)
    detected = sum(trial.detected_events for trial in trials)
    recovered = sum(trial.recovered_events for trial in trials)
    lower, upper = wilson_interval(successes, count)
    witnesses = [trial.to_dict() for trial in trials if not trial.mission_success][
        :retain_failure_witnesses
    ]
    witness_digest = sha256(
        repr([(item["trial_index"], item["failed_functions"]) for item in witnesses]).encode("utf-8")
    ).hexdigest()
    return {
        "start_offset": start_offset,
        "count": count,
        "next_offset": start_offset + count,
        "permanent_total_cap": None,
        "duration_hours": duration_hours,
        "mission_successes": successes,
        "mission_failures": count - successes,
        "estimated_success_probability": successes / count,
        "wilson_95_interval": [lower, upper],
        "mean_events_per_trial": total_events / count,
        "detection_fraction": detected / max(total_events, 1),
        "recovery_fraction": recovered / max(total_events, 1),
        "safe_mode_entry_fraction": sum(trial.entered_safe_mode for trial in trials) / count,
        "failure_witnesses": witnesses,
        "failure_witness_digest": witness_digest,
        "theorem_claimed": False,
        "scientific_validation_claimed": False,
        "flight_qualified_claimed": False,
    }
