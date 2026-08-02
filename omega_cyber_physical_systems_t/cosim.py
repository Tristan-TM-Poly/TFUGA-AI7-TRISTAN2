from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from typing import Any, Sequence

from .control import PIDConfig, PIDState, pid_step


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _quantize(value: float, lower: float, upper: float, bits: int) -> float:
    clipped = _clip(value, lower, upper)
    levels = (1 << bits) - 1
    index = round((clipped - lower) * levels / (upper - lower))
    return lower + index * (upper - lower) / levels


@dataclass(frozen=True)
class AxisPlantConfig:
    resistance_ohm: float = 0.8
    inductance_h: float = 0.006
    torque_constant_nm_a: float = 0.11
    back_emf_v_s_rad: float = 0.11
    motor_rad_per_m: float = 180.0
    transmission_efficiency: float = 0.88
    mass_kg: float = 4.0
    damping_n_s_m: float = 8.0
    stiffness_n_m: float = 20.0
    thermal_capacitance_j_k: float = 180.0
    thermal_resistance_k_w: float = 1.8
    ambient_temperature_k: float = 293.15

    def validate(self) -> None:
        positive = (
            self.resistance_ohm,
            self.inductance_h,
            self.torque_constant_nm_a,
            self.back_emf_v_s_rad,
            self.motor_rad_per_m,
            self.mass_kg,
            self.thermal_capacitance_j_k,
            self.thermal_resistance_k_w,
            self.ambient_temperature_k,
        )
        if any(item <= 0 for item in positive):
            raise ValueError("positive plant parameters must exceed zero")
        if not 0.0 < self.transmission_efficiency <= 1.0:
            raise ValueError("transmission_efficiency must lie in (0, 1]")
        if self.damping_n_s_m < 0 or self.stiffness_n_m < 0:
            raise ValueError("damping and stiffness cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class ElectronicsConfig:
    adc_bits: int = 16
    pwm_bits: int = 12
    sensor_min_m: float = -0.5
    sensor_max_m: float = 0.5
    sample_period_s: float = 0.001
    controller_compute_time_s: float = 0.00035
    voltage_limit_v: float = 24.0

    def validate(self) -> None:
        if self.adc_bits < 2 or self.pwm_bits < 2:
            raise ValueError("ADC and PWM need at least two bits")
        if self.sensor_max_m <= self.sensor_min_m:
            raise ValueError("sensor range is invalid")
        if self.sample_period_s <= 0 or self.controller_compute_time_s < 0:
            raise ValueError("electronic timing parameters are invalid")
        if self.voltage_limit_v <= 0:
            raise ValueError("voltage_limit_v must be positive")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class SafetyLimits:
    current_limit_a: float = 18.0
    temperature_limit_k: float = 353.15
    absolute_position_limit_m: float = 0.25
    absolute_velocity_limit_mps: float = 1.5

    def validate(self) -> None:
        if min(
            self.current_limit_a,
            self.temperature_limit_k,
            self.absolute_position_limit_m,
            self.absolute_velocity_limit_mps,
        ) <= 0:
            raise ValueError("safety limits must be positive")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class FaultEvent:
    fault_id: str
    start_s: float
    end_s: float
    sensor_bias_m: float = 0.0
    voltage_scale: float = 1.0
    motor_force_scale: float = 1.0
    compute_time_scale: float = 1.0
    external_force_n: float = 0.0
    stuck_voltage_v: float | None = None

    def validate(self) -> None:
        if not self.fault_id.strip():
            raise ValueError("fault_id cannot be empty")
        if self.start_s < 0 or self.end_s <= self.start_s:
            raise ValueError("fault interval is invalid")
        if self.voltage_scale < 0 or self.motor_force_scale < 0 or self.compute_time_scale < 0:
            raise ValueError("fault scales cannot be negative")

    def active(self, time_s: float) -> bool:
        return self.start_s <= time_s < self.end_s

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class ClosedLoopScenario:
    scenario_id: str
    duration_s: float
    integration_step_s: float
    setpoint_m: float
    external_force_n: float = 0.0
    faults: tuple[FaultEvent, ...] = ()

    def validate(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id cannot be empty")
        if self.duration_s <= 0 or self.integration_step_s <= 0:
            raise ValueError("scenario duration and integration step must be positive")
        if self.integration_step_s > self.duration_s:
            raise ValueError("integration step cannot exceed duration")
        fault_ids: set[str] = set()
        for fault in self.faults:
            fault.validate()
            if fault.fault_id in fault_ids:
                raise ValueError("fault IDs must be unique")
            fault_ids.add(fault.fault_id)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "scenario_id": self.scenario_id,
            "duration_s": self.duration_s,
            "integration_step_s": self.integration_step_s,
            "setpoint_m": self.setpoint_m,
            "external_force_n": self.external_force_n,
            "faults": [item.to_dict() for item in self.faults],
        }


@dataclass(frozen=True)
class ClosedLoopSample:
    time_s: float
    setpoint_m: float
    true_position_m: float
    measured_position_m: float
    velocity_mps: float
    current_a: float
    motor_temperature_k: float
    voltage_command_v: float
    tracking_error_m: float
    electrical_power_w: float
    mechanical_power_w: float
    deadline_missed: bool
    shutdown_latched: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClosedLoopReport:
    scenario: ClosedLoopScenario
    plant: AxisPlantConfig
    electronics: ElectronicsConfig
    safety: SafetyLimits
    controller: PIDConfig
    samples: tuple[ClosedLoopSample, ...]
    final_position_m: float
    final_error_m: float
    rms_error_m: float
    overshoot_fraction: float
    settling_time_s: float | None
    peak_current_a: float
    peak_temperature_k: float
    peak_velocity_mps: float
    net_electrical_energy_j: float
    absolute_electrical_energy_j: float
    positive_mechanical_energy_j: float
    deadline_miss_count: int
    saturation_count: int
    shutdown_reasons: tuple[str, ...]
    finite: bool
    evidence_hash: str
    physics_certified: bool = False
    software_certified: bool = False
    hardware_validated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario.to_dict(),
            "plant": self.plant.to_dict(),
            "electronics": self.electronics.to_dict(),
            "safety": self.safety.to_dict(),
            "controller": self.controller.to_dict(),
            "samples": [item.to_dict() for item in self.samples],
            "sample_count": len(self.samples),
            "final_position_m": self.final_position_m,
            "final_error_m": self.final_error_m,
            "rms_error_m": self.rms_error_m,
            "overshoot_fraction": self.overshoot_fraction,
            "settling_time_s": self.settling_time_s,
            "peak_current_a": self.peak_current_a,
            "peak_temperature_k": self.peak_temperature_k,
            "peak_velocity_mps": self.peak_velocity_mps,
            "net_electrical_energy_j": self.net_electrical_energy_j,
            "absolute_electrical_energy_j": self.absolute_electrical_energy_j,
            "positive_mechanical_energy_j": self.positive_mechanical_energy_j,
            "deadline_miss_count": self.deadline_miss_count,
            "saturation_count": self.saturation_count,
            "shutdown_reasons": list(self.shutdown_reasons),
            "finite": self.finite,
            "evidence_hash": self.evidence_hash,
            "physics_certified": self.physics_certified,
            "software_certified": self.software_certified,
            "hardware_validated": self.hardware_validated,
            "limitations": [
                "lumped deterministic models only",
                "no switching ripple, backlash, Coulomb friction or structural flexibility",
                "software timing is a declared synthetic fixture, not measured WCET",
                "thermal parameters are illustrative and require calibration",
                "no hardware, EMC, functional-safety or regulatory certification",
            ],
        }


def _active_fault_state(faults: Sequence[FaultEvent], time_s: float) -> dict[str, float | None]:
    state: dict[str, float | None] = {
        "sensor_bias_m": 0.0,
        "voltage_scale": 1.0,
        "motor_force_scale": 1.0,
        "compute_time_scale": 1.0,
        "external_force_n": 0.0,
        "stuck_voltage_v": None,
    }
    for fault in faults:
        if not fault.active(time_s):
            continue
        state["sensor_bias_m"] = float(state["sensor_bias_m"]) + fault.sensor_bias_m
        state["voltage_scale"] = float(state["voltage_scale"]) * fault.voltage_scale
        state["motor_force_scale"] = float(state["motor_force_scale"]) * fault.motor_force_scale
        state["compute_time_scale"] = float(state["compute_time_scale"]) * fault.compute_time_scale
        state["external_force_n"] = float(state["external_force_n"]) + fault.external_force_n
        if fault.stuck_voltage_v is not None:
            state["stuck_voltage_v"] = fault.stuck_voltage_v
    return state


def _derivative(
    state: tuple[float, float, float, float],
    *,
    voltage_v: float,
    external_force_n: float,
    motor_force_scale: float,
    plant: AxisPlantConfig,
) -> tuple[float, float, float, float]:
    current, position, velocity, temperature = state
    motor_speed = plant.motor_rad_per_m * velocity
    current_dot = (
        voltage_v - plant.resistance_ohm * current - plant.back_emf_v_s_rad * motor_speed
    ) / plant.inductance_h
    motor_force = (
        plant.torque_constant_nm_a
        * current
        * plant.motor_rad_per_m
        * plant.transmission_efficiency
        * motor_force_scale
    )
    acceleration = (
        motor_force
        - plant.damping_n_s_m * velocity
        - plant.stiffness_n_m * position
        - external_force_n
    ) / plant.mass_kg
    copper_loss = current * current * plant.resistance_ohm
    cooling = (temperature - plant.ambient_temperature_k) / plant.thermal_resistance_k_w
    temperature_dot = (copper_loss - cooling) / plant.thermal_capacitance_j_k
    return current_dot, velocity, acceleration, temperature_dot


def _rk4_axis(
    state: tuple[float, float, float, float],
    *,
    dt_s: float,
    voltage_v: float,
    external_force_n: float,
    motor_force_scale: float,
    plant: AxisPlantConfig,
) -> tuple[float, float, float, float]:
    def add_scaled(base: tuple[float, ...], delta: tuple[float, ...], scale: float) -> tuple[float, ...]:
        return tuple(a + scale * b for a, b in zip(base, delta))

    kwargs = {
        "voltage_v": voltage_v,
        "external_force_n": external_force_n,
        "motor_force_scale": motor_force_scale,
        "plant": plant,
    }
    k1 = _derivative(state, **kwargs)
    k2 = _derivative(add_scaled(state, k1, 0.5 * dt_s), **kwargs)
    k3 = _derivative(add_scaled(state, k2, 0.5 * dt_s), **kwargs)
    k4 = _derivative(add_scaled(state, k3, dt_s), **kwargs)
    return tuple(
        value + dt_s * (a + 2.0 * b + 2.0 * c + d) / 6.0
        for value, a, b, c, d in zip(state, k1, k2, k3, k4)
    )  # type: ignore[return-value]


def _settling_time(samples: Sequence[ClosedLoopSample], setpoint: float) -> float | None:
    if not samples:
        return None
    tolerance = max(0.0005, 0.02 * max(abs(setpoint), 0.01))
    suffix_max: list[float] = [0.0] * len(samples)
    running = 0.0
    for index in range(len(samples) - 1, -1, -1):
        running = max(running, abs(samples[index].tracking_error_m))
        suffix_max[index] = running
    for sample, maximum in zip(samples, suffix_max):
        if maximum <= tolerance:
            return sample.time_s
    return None


def run_closed_loop_axis(
    scenario: ClosedLoopScenario,
    *,
    plant: AxisPlantConfig | None = None,
    electronics: ElectronicsConfig | None = None,
    safety: SafetyLimits | None = None,
    controller: PIDConfig | None = None,
) -> ClosedLoopReport:
    scenario.validate()
    plant_cfg = plant or AxisPlantConfig()
    electronics_cfg = electronics or ElectronicsConfig()
    safety_cfg = safety or SafetyLimits()
    controller_cfg = controller or PIDConfig(
        kp=95.0,
        ki=35.0,
        kd=7.0,
        output_min=-electronics_cfg.voltage_limit_v,
        output_max=electronics_cfg.voltage_limit_v,
        integral_min=-0.5,
        integral_max=0.5,
        derivative_filter_hz=70.0,
    )
    plant_cfg.validate()
    electronics_cfg.validate()
    safety_cfg.validate()
    controller_cfg.validate()
    if scenario.integration_step_s > electronics_cfg.sample_period_s:
        raise ValueError("integration step must not exceed controller sample period")

    state = (0.0, 0.0, 0.0, plant_cfg.ambient_temperature_k)
    pid_state = PIDState()
    voltage_command = 0.0
    next_control_time = 0.0
    samples: list[ClosedLoopSample] = []
    shutdown_reasons: list[str] = []
    shutdown_latched = False
    deadline_misses = 0
    saturation_count = 0
    net_energy = 0.0
    absolute_energy = 0.0
    mechanical_energy = 0.0
    steps = int(round(scenario.duration_s / scenario.integration_step_s))

    for step in range(steps + 1):
        time_s = min(step * scenario.integration_step_s, scenario.duration_s)
        current, position, velocity, temperature = state
        fault = _active_fault_state(scenario.faults, time_s)
        measurement = _quantize(
            position + float(fault["sensor_bias_m"]),
            electronics_cfg.sensor_min_m,
            electronics_cfg.sensor_max_m,
            electronics_cfg.adc_bits,
        )
        deadline_missed = False
        if time_s + 1e-15 >= next_control_time:
            compute_time = electronics_cfg.controller_compute_time_s * float(fault["compute_time_scale"])
            deadline_missed = compute_time > electronics_cfg.sample_period_s
            if deadline_missed:
                deadline_misses += 1
            elif not shutdown_latched:
                control = pid_step(
                    controller_cfg,
                    pid_state,
                    setpoint=scenario.setpoint_m,
                    measurement=measurement,
                    dt_s=electronics_cfg.sample_period_s,
                )
                pid_state = control.state
                voltage_command = control.output
                saturation_count += int(control.saturated)
            next_control_time += electronics_cfg.sample_period_s

        if fault["stuck_voltage_v"] is not None:
            voltage_command = float(fault["stuck_voltage_v"])
        voltage_command = _quantize(
            voltage_command,
            -electronics_cfg.voltage_limit_v,
            electronics_cfg.voltage_limit_v,
            electronics_cfg.pwm_bits,
        )

        local_reasons: list[str] = []
        if abs(current) > safety_cfg.current_limit_a:
            local_reasons.append("overcurrent")
        if temperature > safety_cfg.temperature_limit_k:
            local_reasons.append("overtemperature")
        if abs(position) > safety_cfg.absolute_position_limit_m:
            local_reasons.append("position_limit")
        if abs(velocity) > safety_cfg.absolute_velocity_limit_mps:
            local_reasons.append("velocity_limit")
        if local_reasons:
            shutdown_latched = True
            for reason in local_reasons:
                if reason not in shutdown_reasons:
                    shutdown_reasons.append(reason)
        applied_voltage = 0.0 if shutdown_latched else voltage_command * float(fault["voltage_scale"])
        external_force = scenario.external_force_n + float(fault["external_force_n"])
        motor_force = (
            plant_cfg.torque_constant_nm_a
            * current
            * plant_cfg.motor_rad_per_m
            * plant_cfg.transmission_efficiency
            * float(fault["motor_force_scale"])
        )
        electrical_power = applied_voltage * current
        mechanical_power = motor_force * velocity
        samples.append(
            ClosedLoopSample(
                time_s=time_s,
                setpoint_m=scenario.setpoint_m,
                true_position_m=position,
                measured_position_m=measurement,
                velocity_mps=velocity,
                current_a=current,
                motor_temperature_k=temperature,
                voltage_command_v=applied_voltage,
                tracking_error_m=scenario.setpoint_m - position,
                electrical_power_w=electrical_power,
                mechanical_power_w=mechanical_power,
                deadline_missed=deadline_missed,
                shutdown_latched=shutdown_latched,
            )
        )
        if step == steps:
            break
        dt_s = scenario.integration_step_s
        net_energy += electrical_power * dt_s
        absolute_energy += abs(electrical_power) * dt_s
        mechanical_energy += max(0.0, mechanical_power) * dt_s
        state = _rk4_axis(
            state,
            dt_s=dt_s,
            voltage_v=applied_voltage,
            external_force_n=external_force,
            motor_force_scale=float(fault["motor_force_scale"]),
            plant=plant_cfg,
        )

    errors = [item.tracking_error_m for item in samples]
    final_position = samples[-1].true_position_m
    final_error = scenario.setpoint_m - final_position
    rms_error = sqrt(sum(item * item for item in errors) / len(errors))
    if scenario.setpoint_m > 0:
        overshoot = max(0.0, max(item.true_position_m for item in samples) - scenario.setpoint_m) / scenario.setpoint_m
    elif scenario.setpoint_m < 0:
        overshoot = max(0.0, scenario.setpoint_m - min(item.true_position_m for item in samples)) / abs(scenario.setpoint_m)
    else:
        overshoot = 0.0
    finite = all(
        isfinite(value)
        for item in samples
        for value in (
            item.time_s,
            item.true_position_m,
            item.measured_position_m,
            item.velocity_mps,
            item.current_a,
            item.motor_temperature_k,
            item.voltage_command_v,
            item.electrical_power_w,
            item.mechanical_power_w,
        )
    )
    payload = {
        "scenario": scenario.to_dict(),
        "plant": plant_cfg.to_dict(),
        "electronics": electronics_cfg.to_dict(),
        "safety": safety_cfg.to_dict(),
        "controller": controller_cfg.to_dict(),
        "samples": [item.to_dict() for item in samples],
        "shutdown_reasons": shutdown_reasons,
        "finite": finite,
    }
    return ClosedLoopReport(
        scenario=scenario,
        plant=plant_cfg,
        electronics=electronics_cfg,
        safety=safety_cfg,
        controller=controller_cfg,
        samples=tuple(samples),
        final_position_m=final_position,
        final_error_m=final_error,
        rms_error_m=rms_error,
        overshoot_fraction=overshoot,
        settling_time_s=_settling_time(samples, scenario.setpoint_m),
        peak_current_a=max(abs(item.current_a) for item in samples),
        peak_temperature_k=max(item.motor_temperature_k for item in samples),
        peak_velocity_mps=max(abs(item.velocity_mps) for item in samples),
        net_electrical_energy_j=net_energy,
        absolute_electrical_energy_j=absolute_energy,
        positive_mechanical_energy_j=mechanical_energy,
        deadline_miss_count=deadline_misses,
        saturation_count=saturation_count,
        shutdown_reasons=tuple(shutdown_reasons),
        finite=finite,
        evidence_hash=_stable_hash(payload),
    )


def demo_nominal_scenario() -> ClosedLoopScenario:
    return ClosedLoopScenario(
        scenario_id="cps-axis-nominal",
        duration_s=1.5,
        integration_step_s=0.0002,
        setpoint_m=0.05,
        external_force_n=1.0,
    )


def demo_fault_scenario() -> ClosedLoopScenario:
    return ClosedLoopScenario(
        scenario_id="cps-axis-faults",
        duration_s=1.5,
        integration_step_s=0.0002,
        setpoint_m=0.05,
        external_force_n=1.0,
        faults=(
            FaultEvent(
                fault_id="encoder-bias",
                start_s=0.55,
                end_s=0.85,
                sensor_bias_m=0.012,
            ),
            FaultEvent(
                fault_id="compute-overrun",
                start_s=0.90,
                end_s=1.10,
                compute_time_scale=4.0,
            ),
            FaultEvent(
                fault_id="load-pulse",
                start_s=1.10,
                end_s=1.25,
                external_force_n=18.0,
            ),
        ),
    )
