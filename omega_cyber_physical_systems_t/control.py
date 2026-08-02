from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PIDConfig:
    kp: float
    ki: float
    kd: float
    output_min: float
    output_max: float
    integral_min: float
    integral_max: float
    derivative_filter_hz: float = 50.0

    def validate(self) -> None:
        if self.kp < 0 or self.ki < 0 or self.kd < 0:
            raise ValueError("PID gains cannot be negative")
        if self.output_max <= self.output_min:
            raise ValueError("PID output_max must exceed output_min")
        if self.integral_max <= self.integral_min:
            raise ValueError("PID integral_max must exceed integral_min")
        if self.derivative_filter_hz <= 0:
            raise ValueError("derivative_filter_hz must be positive")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PIDState:
    integral: float = 0.0
    previous_error: float = 0.0
    filtered_derivative: float = 0.0
    initialized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PIDStep:
    output: float
    proportional: float
    integral_term: float
    derivative_term: float
    saturated: bool
    state: PIDState

    def to_dict(self) -> dict[str, Any]:
        return {
            "output": self.output,
            "proportional": self.proportional,
            "integral_term": self.integral_term,
            "derivative_term": self.derivative_term,
            "saturated": self.saturated,
            "state": self.state.to_dict(),
        }


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def pid_step(
    config: PIDConfig,
    state: PIDState,
    *,
    setpoint: float,
    measurement: float,
    dt_s: float,
    feedforward: float = 0.0,
) -> PIDStep:
    config.validate()
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    error = setpoint - measurement
    raw_derivative = 0.0 if not state.initialized else (error - state.previous_error) / dt_s
    alpha = dt_s / (dt_s + 1.0 / (2.0 * 3.141592653589793 * config.derivative_filter_hz))
    filtered_derivative = state.filtered_derivative + alpha * (raw_derivative - state.filtered_derivative)
    candidate_integral = _clip(
        state.integral + error * dt_s,
        config.integral_min,
        config.integral_max,
    )
    proportional = config.kp * error
    integral_term = config.ki * candidate_integral
    derivative_term = config.kd * filtered_derivative
    unsaturated = feedforward + proportional + integral_term + derivative_term
    output = _clip(unsaturated, config.output_min, config.output_max)
    saturated = output != unsaturated

    # Conditional integration: retain the prior integral when it would push farther into saturation.
    pushes_high = unsaturated > config.output_max and error > 0
    pushes_low = unsaturated < config.output_min and error < 0
    integral = state.integral if saturated and (pushes_high or pushes_low) else candidate_integral
    if integral != candidate_integral:
        integral_term = config.ki * integral
        unsaturated = feedforward + proportional + integral_term + derivative_term
        output = _clip(unsaturated, config.output_min, config.output_max)
        saturated = output != unsaturated

    next_state = PIDState(
        integral=integral,
        previous_error=error,
        filtered_derivative=filtered_derivative,
        initialized=True,
    )
    return PIDStep(output, proportional, integral_term, derivative_term, saturated, next_state)
