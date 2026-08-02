from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Sequence


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _mat_vec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> tuple[float, ...]:
    return tuple(sum(float(value) * float(item) for value, item in zip(row, vector)) for row in matrix)


def _add(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(float(a) + float(b) for a, b in zip(left, right))


def _scale(vector: Sequence[float], scalar: float) -> tuple[float, ...]:
    return tuple(float(item) * scalar for item in vector)


@dataclass(frozen=True)
class StateSpaceModel:
    model_id: str
    a: tuple[tuple[float, ...], ...]
    b: tuple[tuple[float, ...], ...]
    c: tuple[tuple[float, ...], ...]
    d: tuple[tuple[float, ...], ...]
    state_names: tuple[str, ...]
    input_names: tuple[str, ...]
    output_names: tuple[str, ...]
    assumptions: tuple[str, ...]
    physics_certified: bool = False

    def validate(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id cannot be empty")
        n_state = len(self.state_names)
        n_input = len(self.input_names)
        n_output = len(self.output_names)
        if min(n_state, n_input, n_output) < 1:
            raise ValueError("state, input and output names cannot be empty")
        if len(set(self.state_names)) != n_state or len(set(self.input_names)) != n_input:
            raise ValueError("state and input names must be unique")
        if len(self.a) != n_state or any(len(row) != n_state for row in self.a):
            raise ValueError("A must be square with state dimension")
        if len(self.b) != n_state or any(len(row) != n_input for row in self.b):
            raise ValueError("B dimensions do not match")
        if len(self.c) != n_output or any(len(row) != n_state for row in self.c):
            raise ValueError("C dimensions do not match")
        if len(self.d) != n_output or any(len(row) != n_input for row in self.d):
            raise ValueError("D dimensions do not match")
        if not self.assumptions or any(not item.strip() for item in self.assumptions):
            raise ValueError("model assumptions are required")
        coefficients = [value for matrix in (self.a, self.b, self.c, self.d) for row in matrix for value in row]
        if not all(isfinite(value) for value in coefficients):
            raise ValueError("state-space coefficients must be finite")
        if self.physics_certified:
            raise ValueError("R0.1 state-space models cannot self-certify physics")

    def derivative(self, state: Sequence[float], inputs: Sequence[float]) -> tuple[float, ...]:
        self.validate()
        if len(state) != len(self.state_names) or len(inputs) != len(self.input_names):
            raise ValueError("state or input dimension mismatch")
        return _add(_mat_vec(self.a, state), _mat_vec(self.b, inputs))

    def output(self, state: Sequence[float], inputs: Sequence[float]) -> tuple[float, ...]:
        self.validate()
        if len(state) != len(self.state_names) or len(inputs) != len(self.input_names):
            raise ValueError("state or input dimension mismatch")
        return _add(_mat_vec(self.c, state), _mat_vec(self.d, inputs))

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "model_id": self.model_id,
            "a": [list(row) for row in self.a],
            "b": [list(row) for row in self.b],
            "c": [list(row) for row in self.c],
            "d": [list(row) for row in self.d],
            "state_names": list(self.state_names),
            "input_names": list(self.input_names),
            "output_names": list(self.output_names),
            "assumptions": list(self.assumptions),
            "physics_certified": self.physics_certified,
        }


@dataclass(frozen=True)
class SimulationSample:
    time_s: float
    state: tuple[float, ...]
    inputs: tuple[float, ...]
    outputs: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "time_s": self.time_s,
            "state": list(self.state),
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
        }


@dataclass(frozen=True)
class SimulationTrace:
    model_id: str
    dt_s: float
    samples: tuple[SimulationSample, ...]
    finite: bool
    evidence_hash: str
    physics_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "dt_s": self.dt_s,
            "samples": [item.to_dict() for item in self.samples],
            "finite": self.finite,
            "evidence_hash": self.evidence_hash,
            "physics_certified": self.physics_certified,
        }


def rk4_step(
    model: StateSpaceModel,
    state: Sequence[float],
    inputs: Sequence[float],
    dt_s: float,
) -> tuple[float, ...]:
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    x = tuple(float(item) for item in state)
    u = tuple(float(item) for item in inputs)
    k1 = model.derivative(x, u)
    k2 = model.derivative(_add(x, _scale(k1, 0.5 * dt_s)), u)
    k3 = model.derivative(_add(x, _scale(k2, 0.5 * dt_s)), u)
    k4 = model.derivative(_add(x, _scale(k3, dt_s)), u)
    return tuple(
        value + dt_s * (a + 2.0 * b + 2.0 * c + d) / 6.0
        for value, a, b, c, d in zip(x, k1, k2, k3, k4)
    )


def simulate_state_space(
    model: StateSpaceModel,
    *,
    initial_state: Sequence[float],
    input_sequence: Sequence[Sequence[float]],
    dt_s: float,
) -> SimulationTrace:
    model.validate()
    if dt_s <= 0 or not input_sequence:
        raise ValueError("positive dt_s and non-empty input_sequence are required")
    state = tuple(float(item) for item in initial_state)
    if len(state) != len(model.state_names):
        raise ValueError("initial_state dimension mismatch")
    samples: list[SimulationSample] = []
    for index, inputs in enumerate(input_sequence):
        u = tuple(float(item) for item in inputs)
        outputs = model.output(state, u)
        samples.append(SimulationSample(index * dt_s, state, u, outputs))
        state = rk4_step(model, state, u, dt_s)
    final_inputs = tuple(float(item) for item in input_sequence[-1])
    samples.append(
        SimulationSample(
            len(input_sequence) * dt_s,
            state,
            final_inputs,
            model.output(state, final_inputs),
        )
    )
    finite = all(
        isfinite(value)
        for sample in samples
        for vector in (sample.state, sample.inputs, sample.outputs)
        for value in vector
    )
    payload = {
        "model": model.to_dict(),
        "dt_s": dt_s,
        "samples": [item.to_dict() for item in samples],
        "finite": finite,
    }
    return SimulationTrace(model.model_id, dt_s, tuple(samples), finite, _stable_hash(payload))


def mass_spring_damper_model(*, mass_kg: float, damping_n_s_m: float, stiffness_n_m: float) -> StateSpaceModel:
    if mass_kg <= 0 or damping_n_s_m < 0 or stiffness_n_m < 0:
        raise ValueError("invalid mass-spring-damper parameters")
    return StateSpaceModel(
        model_id="mass-spring-damper-r0.1",
        a=((0.0, 1.0), (-stiffness_n_m / mass_kg, -damping_n_s_m / mass_kg)),
        b=((0.0,), (1.0 / mass_kg,)),
        c=((1.0, 0.0), (0.0, 1.0)),
        d=((0.0,), (0.0,)),
        state_names=("position_m", "velocity_mps"),
        input_names=("force_n",),
        output_names=("position_m", "velocity_mps"),
        assumptions=(
            "single translational degree of freedom",
            "linear spring and viscous damping",
            "constant parameters and rigid reference frame",
        ),
    )


def dc_motor_model(
    *,
    resistance_ohm: float,
    inductance_h: float,
    torque_constant_nm_a: float,
    back_emf_v_s_rad: float,
    inertia_kg_m2: float,
    viscous_friction_nm_s_rad: float,
) -> StateSpaceModel:
    values = (
        resistance_ohm,
        inductance_h,
        torque_constant_nm_a,
        back_emf_v_s_rad,
        inertia_kg_m2,
    )
    if any(value <= 0 for value in values) or viscous_friction_nm_s_rad < 0:
        raise ValueError("invalid DC motor parameters")
    return StateSpaceModel(
        model_id="dc-motor-electromechanical-r0.1",
        a=(
            (-resistance_ohm / inductance_h, -back_emf_v_s_rad / inductance_h),
            (torque_constant_nm_a / inertia_kg_m2, -viscous_friction_nm_s_rad / inertia_kg_m2),
        ),
        b=((1.0 / inductance_h, 0.0), (0.0, -1.0 / inertia_kg_m2)),
        c=((1.0, 0.0), (0.0, 1.0), (torque_constant_nm_a, 0.0)),
        d=((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        state_names=("current_a", "angular_speed_rad_s"),
        input_names=("voltage_v", "load_torque_nm"),
        output_names=("current_a", "angular_speed_rad_s", "motor_torque_nm"),
        assumptions=(
            "linear permanent-magnet DC motor",
            "constant winding resistance and flux",
            "lumped inertia and viscous friction",
            "no commutation ripple, saturation or switching dynamics",
        ),
    )


def electromechanical_axis_model(
    *,
    resistance_ohm: float = 0.8,
    inductance_h: float = 0.006,
    torque_constant_nm_a: float = 0.11,
    back_emf_v_s_rad: float = 0.11,
    motor_rad_per_m: float = 180.0,
    transmission_efficiency: float = 0.88,
    mass_kg: float = 4.0,
    damping_n_s_m: float = 8.0,
    stiffness_n_m: float = 20.0,
) -> StateSpaceModel:
    positives = (
        resistance_ohm,
        inductance_h,
        torque_constant_nm_a,
        back_emf_v_s_rad,
        motor_rad_per_m,
        mass_kg,
    )
    if any(value <= 0 for value in positives):
        raise ValueError("axis positive parameters must exceed zero")
    if not 0.0 < transmission_efficiency <= 1.0 or damping_n_s_m < 0 or stiffness_n_m < 0:
        raise ValueError("invalid axis efficiency, damping or stiffness")
    force_per_amp = torque_constant_nm_a * motor_rad_per_m * transmission_efficiency
    return StateSpaceModel(
        model_id="electromechanical-linear-axis-r0.1",
        a=(
            (-resistance_ohm / inductance_h, 0.0, -back_emf_v_s_rad * motor_rad_per_m / inductance_h),
            (0.0, 0.0, 1.0),
            (force_per_amp / mass_kg, -stiffness_n_m / mass_kg, -damping_n_s_m / mass_kg),
        ),
        b=((1.0 / inductance_h, 0.0), (0.0, 0.0), (0.0, -1.0 / mass_kg)),
        c=((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
        d=((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        state_names=("motor_current_a", "position_m", "velocity_mps"),
        input_names=("drive_voltage_v", "external_force_n"),
        output_names=("position_m", "velocity_mps", "motor_current_a"),
        assumptions=(
            "rigid loss-scaled rotary-to-linear transmission",
            "linear motor electrical model",
            "single translational load mode",
            "no backlash, Coulomb friction or elastic transmission mode",
        ),
    )
