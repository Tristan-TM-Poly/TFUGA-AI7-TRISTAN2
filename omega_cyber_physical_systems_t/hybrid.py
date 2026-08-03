from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Mapping, Sequence


COMPARATORS = ("<", "<=", ">", ">=", "==", "!=")


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class Predicate:
    variable: str
    comparator: str
    threshold: float
    tolerance: float = 1e-12
    label: str = ""

    def validate(self, variables: Sequence[str] | None = None) -> None:
        if not self.variable.strip():
            raise ValueError("predicate variable cannot be empty")
        if self.comparator not in COMPARATORS:
            raise ValueError(f"unsupported comparator: {self.comparator}")
        if not isfinite(self.threshold) or self.tolerance < 0 or not isfinite(self.tolerance):
            raise ValueError("predicate threshold and tolerance must be finite")
        if variables is not None and self.variable not in variables:
            raise ValueError(f"predicate references unknown variable: {self.variable}")

    def evaluate(self, state: Mapping[str, float]) -> bool:
        self.validate(tuple(state))
        value = float(state[self.variable])
        t = self.threshold
        eps = self.tolerance
        if self.comparator == "<":
            return value < t - eps
        if self.comparator == "<=":
            return value <= t + eps
        if self.comparator == ">":
            return value > t + eps
        if self.comparator == ">=":
            return value >= t - eps
        if self.comparator == "==":
            return abs(value - t) <= eps
        return abs(value - t) > eps

    def signed_margin(self, state: Mapping[str, float]) -> float:
        value = float(state[self.variable])
        if self.comparator in ("<", "<="):
            return self.threshold - value
        if self.comparator in (">", ">="):
            return value - self.threshold
        if self.comparator == "==":
            return self.tolerance - abs(value - self.threshold)
        return abs(value - self.threshold) - self.tolerance

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class AffineFlow:
    intercept: float = 0.0
    coefficients: Mapping[str, float] = field(default_factory=dict)

    def validate(self, variables: Sequence[str]) -> None:
        if not isfinite(self.intercept):
            raise ValueError("flow intercept must be finite")
        for variable, coefficient in self.coefficients.items():
            if variable not in variables:
                raise ValueError(f"flow references unknown variable: {variable}")
            if not isfinite(float(coefficient)):
                raise ValueError("flow coefficients must be finite")

    def evaluate(self, state: Mapping[str, float]) -> float:
        return self.intercept + sum(float(value) * float(state[name]) for name, value in self.coefficients.items())

    def to_dict(self) -> dict[str, Any]:
        return {"intercept": self.intercept, "coefficients": dict(self.coefficients)}


@dataclass(frozen=True)
class ResetRule:
    target_variable: str
    source_variable: str | None = None
    scale: float = 1.0
    offset: float = 0.0

    def validate(self, variables: Sequence[str]) -> None:
        if self.target_variable not in variables:
            raise ValueError(f"reset target is unknown: {self.target_variable}")
        if self.source_variable is not None and self.source_variable not in variables:
            raise ValueError(f"reset source is unknown: {self.source_variable}")
        if not isfinite(self.scale) or not isfinite(self.offset):
            raise ValueError("reset scale and offset must be finite")

    def apply(self, state: Mapping[str, float]) -> float:
        source = 0.0 if self.source_variable is None else float(state[self.source_variable])
        return self.scale * source + self.offset

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HybridMode:
    mode_id: str
    flows: Mapping[str, AffineFlow]
    invariants: tuple[Predicate, ...] = ()
    safe: bool = True
    terminal: bool = False
    description: str = ""

    def validate(self, variables: Sequence[str]) -> None:
        if not self.mode_id.strip():
            raise ValueError("mode_id cannot be empty")
        if set(self.flows) != set(variables):
            missing = sorted(set(variables) - set(self.flows))
            extra = sorted(set(self.flows) - set(variables))
            raise ValueError(f"mode flows must cover variables exactly; missing={missing}, extra={extra}")
        for flow in self.flows.values():
            flow.validate(variables)
        for invariant in self.invariants:
            invariant.validate(variables)

    def derivative(self, state: Mapping[str, float]) -> dict[str, float]:
        return {name: flow.evaluate(state) for name, flow in self.flows.items()}

    def invariants_hold(self, state: Mapping[str, float]) -> bool:
        return all(item.evaluate(state) for item in self.invariants)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "flows": {name: flow.to_dict() for name, flow in self.flows.items()},
            "invariants": [item.to_dict() for item in self.invariants],
            "safe": self.safe,
            "terminal": self.terminal,
            "description": self.description,
        }


@dataclass(frozen=True)
class HybridTransition:
    transition_id: str
    source_mode: str
    target_mode: str
    guards: tuple[Predicate, ...]
    resets: tuple[ResetRule, ...] = ()
    priority: int = 100
    minimum_dwell_s: float = 0.0
    controllable: bool = False
    description: str = ""

    def validate(self, variables: Sequence[str], modes: Sequence[str]) -> None:
        if not self.transition_id.strip():
            raise ValueError("transition_id cannot be empty")
        if self.source_mode not in modes or self.target_mode not in modes:
            raise ValueError("transition references an unknown mode")
        if not self.guards:
            raise ValueError("transition requires at least one guard")
        if self.minimum_dwell_s < 0 or not isfinite(self.minimum_dwell_s):
            raise ValueError("minimum_dwell_s must be finite and non-negative")
        for guard in self.guards:
            guard.validate(variables)
        targets: set[str] = set()
        for reset in self.resets:
            reset.validate(variables)
            if reset.target_variable in targets:
                raise ValueError("a transition cannot reset the same variable twice")
            targets.add(reset.target_variable)

    def enabled(self, state: Mapping[str, float], dwell_s: float) -> bool:
        return dwell_s + 1e-15 >= self.minimum_dwell_s and all(item.evaluate(state) for item in self.guards)

    def apply(self, state: Mapping[str, float]) -> dict[str, float]:
        updated = {name: float(value) for name, value in state.items()}
        before = dict(updated)
        for reset in self.resets:
            updated[reset.target_variable] = reset.apply(before)
        return updated

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "source_mode": self.source_mode,
            "target_mode": self.target_mode,
            "guards": [item.to_dict() for item in self.guards],
            "resets": [item.to_dict() for item in self.resets],
            "priority": self.priority,
            "minimum_dwell_s": self.minimum_dwell_s,
            "controllable": self.controllable,
            "description": self.description,
        }


@dataclass(frozen=True)
class HybridAutomaton:
    automaton_id: str
    variables: tuple[str, ...]
    modes: tuple[HybridMode, ...]
    transitions: tuple[HybridTransition, ...]
    initial_mode: str
    initial_state: Mapping[str, float]
    safe_modes: tuple[str, ...]
    emergency_mode: str | None = None
    permanent_total_cap: None = None
    physics_certified: bool = False
    safety_certified: bool = False

    def mode_map(self) -> dict[str, HybridMode]:
        return {item.mode_id: item for item in self.modes}

    def validate(self) -> None:
        if not self.automaton_id.strip():
            raise ValueError("automaton_id cannot be empty")
        if not self.variables or len(set(self.variables)) != len(self.variables):
            raise ValueError("variables must be non-empty and unique")
        if any(not item.strip() for item in self.variables):
            raise ValueError("variable names cannot be empty")
        if set(self.initial_state) != set(self.variables):
            raise ValueError("initial_state must cover variables exactly")
        if not all(isfinite(float(value)) for value in self.initial_state.values()):
            raise ValueError("initial_state values must be finite")
        mode_ids = [item.mode_id for item in self.modes]
        if not mode_ids or len(set(mode_ids)) != len(mode_ids):
            raise ValueError("modes must be non-empty and unique")
        for mode in self.modes:
            mode.validate(self.variables)
        if self.initial_mode not in mode_ids:
            raise ValueError("initial_mode is unknown")
        if any(item not in mode_ids for item in self.safe_modes):
            raise ValueError("safe_modes contains an unknown mode")
        if self.emergency_mode is not None and self.emergency_mode not in mode_ids:
            raise ValueError("emergency_mode is unknown")
        transition_ids: set[str] = set()
        for transition in self.transitions:
            transition.validate(self.variables, mode_ids)
            if transition.transition_id in transition_ids:
                raise ValueError("transition IDs must be unique")
            transition_ids.add(transition.transition_id)
        if any((self.physics_certified, self.safety_certified)):
            raise ValueError("R0.3 software cannot self-certify physics or safety")
        if not self.mode_map()[self.initial_mode].invariants_hold(self.initial_state):
            raise ValueError("initial state violates the initial-mode invariant")

    @property
    def evidence_hash(self) -> str:
        return _stable_hash(self.to_dict(include_hash=False))

    def outgoing(self, mode_id: str) -> tuple[HybridTransition, ...]:
        return tuple(sorted(
            (item for item in self.transitions if item.source_mode == mode_id),
            key=lambda item: (item.priority, item.transition_id),
        ))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        self.validate()
        payload = {
            "automaton_id": self.automaton_id,
            "variables": list(self.variables),
            "modes": [item.to_dict() for item in self.modes],
            "transitions": [item.to_dict() for item in self.transitions],
            "initial_mode": self.initial_mode,
            "initial_state": dict(self.initial_state),
            "safe_modes": list(self.safe_modes),
            "emergency_mode": self.emergency_mode,
            "permanent_total_cap": self.permanent_total_cap,
            "physics_certified": self.physics_certified,
            "safety_certified": self.safety_certified,
        }
        if include_hash:
            payload["evidence_hash"] = _stable_hash(payload)
        return payload


@dataclass(frozen=True)
class HybridEvent:
    time_s: float
    transition_id: str
    source_mode: str
    target_mode: str
    state_before: Mapping[str, float]
    state_after: Mapping[str, float]
    dwell_s: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "time_s": self.time_s,
            "transition_id": self.transition_id,
            "source_mode": self.source_mode,
            "target_mode": self.target_mode,
            "state_before": dict(self.state_before),
            "state_after": dict(self.state_after),
            "dwell_s": self.dwell_s,
        }


@dataclass(frozen=True)
class HybridSample:
    time_s: float
    mode_id: str
    state: Mapping[str, float]
    invariant_holds: bool
    safe_mode: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "time_s": self.time_s,
            "mode_id": self.mode_id,
            "state": dict(self.state),
            "invariant_holds": self.invariant_holds,
            "safe_mode": self.safe_mode,
        }


@dataclass(frozen=True)
class HybridSimulationReport:
    automaton_id: str
    horizon_s: float
    integration_step_s: float
    samples: tuple[HybridSample, ...]
    events: tuple[HybridEvent, ...]
    final_mode: str
    final_state: Mapping[str, float]
    invariant_violation_count: int
    unsafe_sample_count: int
    zeno_suspected: bool
    transition_limit_hit: bool
    finite: bool
    evidence_hash: str
    physics_certified: bool = False
    safety_certified: bool = False
    formal_reachability_proven: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "automaton_id": self.automaton_id,
            "horizon_s": self.horizon_s,
            "integration_step_s": self.integration_step_s,
            "samples": [item.to_dict() for item in self.samples],
            "events": [item.to_dict() for item in self.events],
            "sample_count": len(self.samples),
            "event_count": len(self.events),
            "final_mode": self.final_mode,
            "final_state": dict(self.final_state),
            "invariant_violation_count": self.invariant_violation_count,
            "unsafe_sample_count": self.unsafe_sample_count,
            "zeno_suspected": self.zeno_suspected,
            "transition_limit_hit": self.transition_limit_hit,
            "finite": self.finite,
            "evidence_hash": self.evidence_hash,
            "physics_certified": self.physics_certified,
            "safety_certified": self.safety_certified,
            "formal_reachability_proven": self.formal_reachability_proven,
            "limitations": [
                "explicit Euler integration with declared finite step",
                "guards are sampled at integration boundaries",
                "no theorem-prover or exact hybrid reachability claim",
                "Zeno detection is a finite-window computational warning",
                "no hardware, safety-integrity or regulatory certification",
            ],
        }


def simulate_hybrid_automaton(
    automaton: HybridAutomaton,
    *,
    horizon_s: float,
    integration_step_s: float,
    max_transitions_per_step: int = 8,
    zeno_window_s: float = 0.01,
    zeno_transition_threshold: int = 12,
) -> HybridSimulationReport:
    automaton.validate()
    if horizon_s <= 0 or integration_step_s <= 0 or integration_step_s > horizon_s:
        raise ValueError("simulation horizon and integration step are invalid")
    if max_transitions_per_step < 1 or zeno_window_s <= 0 or zeno_transition_threshold < 2:
        raise ValueError("transition and Zeno limits are invalid")

    modes = automaton.mode_map()
    mode_id = automaton.initial_mode
    state = {name: float(value) for name, value in automaton.initial_state.items()}
    dwell_s = 0.0
    samples: list[HybridSample] = []
    events: list[HybridEvent] = []
    invariant_violations = 0
    unsafe_samples = 0
    transition_limit_hit = False
    zeno_suspected = False
    steps = int(round(horizon_s / integration_step_s))

    for step in range(steps + 1):
        time_s = min(step * integration_step_s, horizon_s)
        mode = modes[mode_id]
        invariant_holds = mode.invariants_hold(state)
        safe_mode = mode_id in automaton.safe_modes and mode.safe
        invariant_violations += int(not invariant_holds)
        unsafe_samples += int(not safe_mode)
        samples.append(HybridSample(time_s, mode_id, dict(state), invariant_holds, safe_mode))
        if step == steps or mode.terminal:
            break

        derivative = mode.derivative(state)
        candidate = {
            name: state[name] + integration_step_s * derivative[name]
            for name in automaton.variables
        }
        dwell_s += integration_step_s
        state = candidate

        local_transition_count = 0
        while True:
            enabled = [item for item in automaton.outgoing(mode_id) if item.enabled(state, dwell_s)]
            if not enabled:
                break
            transition = enabled[0]
            before = dict(state)
            state = transition.apply(state)
            event = HybridEvent(
                time_s=min(time_s + integration_step_s, horizon_s),
                transition_id=transition.transition_id,
                source_mode=transition.source_mode,
                target_mode=transition.target_mode,
                state_before=before,
                state_after=dict(state),
                dwell_s=dwell_s,
            )
            events.append(event)
            mode_id = transition.target_mode
            dwell_s = 0.0
            local_transition_count += 1
            if not modes[mode_id].invariants_hold(state):
                invariant_violations += 1
            if local_transition_count >= max_transitions_per_step:
                transition_limit_hit = True
                break
        if transition_limit_hit:
            break

        recent = [item for item in events if events[-1].time_s - item.time_s <= zeno_window_s] if events else []
        if len(recent) >= zeno_transition_threshold:
            zeno_suspected = True
            break

    finite = all(
        isfinite(value)
        for sample in samples
        for value in sample.state.values()
    )
    payload = {
        "automaton_hash": automaton.evidence_hash,
        "horizon_s": horizon_s,
        "integration_step_s": integration_step_s,
        "samples": [item.to_dict() for item in samples],
        "events": [item.to_dict() for item in events],
        "invariant_violation_count": invariant_violations,
        "unsafe_sample_count": unsafe_samples,
        "zeno_suspected": zeno_suspected,
        "transition_limit_hit": transition_limit_hit,
        "finite": finite,
    }
    return HybridSimulationReport(
        automaton_id=automaton.automaton_id,
        horizon_s=horizon_s,
        integration_step_s=integration_step_s,
        samples=tuple(samples),
        events=tuple(events),
        final_mode=mode_id,
        final_state=dict(state),
        invariant_violation_count=invariant_violations,
        unsafe_sample_count=unsafe_samples,
        zeno_suspected=zeno_suspected,
        transition_limit_hit=transition_limit_hit,
        finite=finite,
        evidence_hash=_stable_hash(payload),
    )


def demo_hybrid_axis_automaton() -> HybridAutomaton:
    variables = ("position_m", "velocity_mps", "temperature_k", "clock_s")
    zero = AffineFlow()
    startup = HybridMode(
        "startup",
        flows={
            "position_m": zero,
            "velocity_mps": zero,
            "temperature_k": zero,
            "clock_s": AffineFlow(1.0),
        },
        invariants=(Predicate("clock_s", "<=", 0.051),),
        description="controller initialization and interlock check",
    )
    tracking = HybridMode(
        "tracking",
        flows={
            "position_m": AffineFlow(coefficients={"velocity_mps": 1.0}),
            "velocity_mps": AffineFlow(4.0, {"velocity_mps": -2.0}),
            "temperature_k": AffineFlow(20.0),
            "clock_s": AffineFlow(1.0),
        },
        invariants=(
            Predicate("position_m", "<=", 0.24),
            Predicate("temperature_k", "<=", 303.25),
        ),
        description="nominal servo tracking with synthetic heating",
    )
    derated = HybridMode(
        "derated",
        flows={
            "position_m": AffineFlow(coefficients={"velocity_mps": 1.0}),
            "velocity_mps": AffineFlow(0.6, {"velocity_mps": -4.0}),
            "temperature_k": AffineFlow(2.0, {"temperature_k": -0.005, "clock_s": -0.02}),
            "clock_s": AffineFlow(1.0),
        },
        invariants=(
            Predicate("position_m", "<=", 0.24),
            Predicate("temperature_k", "<=", 320.0),
        ),
        description="reduced authority after thermal threshold",
    )
    safe_shutdown = HybridMode(
        "safe_shutdown",
        flows={
            "position_m": AffineFlow(coefficients={"velocity_mps": 1.0}),
            "velocity_mps": AffineFlow(coefficients={"velocity_mps": -10.0}),
            "temperature_k": AffineFlow(1.46575, {"temperature_k": -0.005}),
            "clock_s": AffineFlow(1.0),
        },
        invariants=(
            Predicate("position_m", "<=", 0.26),
            Predicate("temperature_k", "<=", 330.0),
        ),
        safe=True,
        terminal=False,
        description="latched low-energy fallback state",
    )
    transitions = (
        HybridTransition(
            "startup-complete",
            "startup",
            "tracking",
            guards=(Predicate("clock_s", ">=", 0.05),),
            resets=(ResetRule("clock_s", offset=0.0),),
            priority=10,
            minimum_dwell_s=0.05,
        ),
        HybridTransition(
            "thermal-derate",
            "tracking",
            "derated",
            guards=(Predicate("temperature_k", ">=", 303.15),),
            resets=(ResetRule("clock_s", offset=0.0),),
            priority=10,
            minimum_dwell_s=0.05,
        ),
        HybridTransition(
            "position-fallback",
            "derated",
            "safe_shutdown",
            guards=(Predicate("position_m", ">=", 0.20),),
            resets=(ResetRule("clock_s", offset=0.0),),
            priority=10,
            minimum_dwell_s=0.05,
        ),
    )
    return HybridAutomaton(
        automaton_id="omega-cps-r03-demo-axis",
        variables=variables,
        modes=(startup, tracking, derated, safe_shutdown),
        transitions=transitions,
        initial_mode="startup",
        initial_state={
            "position_m": 0.0,
            "velocity_mps": 0.0,
            "temperature_k": 293.15,
            "clock_s": 0.0,
        },
        safe_modes=("startup", "tracking", "derated", "safe_shutdown"),
        emergency_mode="safe_shutdown",
    )


def demo_zeno_automaton() -> HybridAutomaton:
    variables = ("x",)
    mode_a = HybridMode("a", {"x": AffineFlow()}, invariants=(Predicate("x", ">=", 0.0),))
    mode_b = HybridMode("b", {"x": AffineFlow()}, invariants=(Predicate("x", ">=", 0.0),))
    transitions = (
        HybridTransition("a-to-b", "a", "b", (Predicate("x", ">=", 0.0),), priority=1),
        HybridTransition("b-to-a", "b", "a", (Predicate("x", ">=", 0.0),), priority=1),
    )
    return HybridAutomaton(
        automaton_id="omega-cps-r03-zeno-fixture",
        variables=variables,
        modes=(mode_a, mode_b),
        transitions=transitions,
        initial_mode="a",
        initial_state={"x": 0.0},
        safe_modes=("a", "b"),
    )
