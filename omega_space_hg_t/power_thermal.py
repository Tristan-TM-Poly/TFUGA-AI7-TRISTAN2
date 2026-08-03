"""Reduced coupled power, thermal and data-bus simulation."""
from __future__ import annotations

from dataclasses import dataclass
from math import fmod

from .models import SpacecraftConfig


STEFAN_BOLTZMANN_W_M2_K4 = 5.670374419e-8


@dataclass(frozen=True)
class BusState:
    battery_wh: float
    temperature_k: float
    stored_data_gb: float


@dataclass(frozen=True)
class BusStep:
    state: BusState
    in_eclipse: bool
    payload_active: bool
    downlink_active: bool
    generated_power_w: float
    load_power_w: float


def _window_active(phase: float, start: float, duty_cycle: float) -> bool:
    if duty_cycle <= 0.0:
        return False
    if duty_cycle >= 1.0:
        return True
    end = start + duty_cycle
    if end <= 1.0:
        return start <= phase < end
    return phase >= start or phase < end - 1.0


def orbital_mode_schedule(
    time_s: float,
    period_s: float,
    eclipse_fraction: float,
    payload_duty_cycle: float,
    downlink_duty_cycle: float,
) -> tuple[bool, bool, bool]:
    """Return deterministic eclipse, payload and downlink flags."""

    if period_s <= 0.0:
        raise ValueError("period_s must be positive")
    phase = fmod(time_s, period_s) / period_s
    in_eclipse = _window_active(phase, 0.5 - eclipse_fraction / 2.0, eclipse_fraction)
    payload_active = _window_active(phase, 0.05, payload_duty_cycle) and not in_eclipse
    downlink_active = _window_active(phase, 0.78, downlink_duty_cycle)
    return in_eclipse, payload_active, downlink_active


def initial_bus_state(spacecraft: SpacecraftConfig) -> BusState:
    return BusState(
        battery_wh=spacecraft.battery_capacity_wh * spacecraft.initial_battery_fraction,
        temperature_k=spacecraft.initial_temperature_k,
        stored_data_gb=0.0,
    )


def advance_bus(
    state: BusState,
    spacecraft: SpacecraftConfig,
    dt_s: float,
    *,
    time_s: float,
    period_s: float,
    eclipse_fraction: float,
    payload_duty_cycle: float,
    downlink_duty_cycle: float,
    solar_flux_w_m2: float,
    albedo_flux_w_m2: float,
    deep_space_temperature_k: float,
) -> BusStep:
    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")
    in_eclipse, payload_active, downlink_active = orbital_mode_schedule(
        time_s,
        period_s,
        eclipse_fraction,
        payload_duty_cycle,
        downlink_duty_cycle,
    )
    illumination_factor = 0.0 if in_eclipse else 0.72
    generated_power_w = (
        solar_flux_w_m2
        * spacecraft.panel_area_m2
        * spacecraft.panel_efficiency
        * illumination_factor
    )
    load_power_w = spacecraft.base_load_w
    if payload_active:
        load_power_w += spacecraft.payload_load_w
    if downlink_active:
        load_power_w += spacecraft.downlink_load_w

    battery_wh = state.battery_wh + (generated_power_w - load_power_w) * dt_s / 3600.0
    battery_wh = min(spacecraft.battery_capacity_wh, max(0.0, battery_wh))

    absorbed_solar_w = (
        0.0
        if in_eclipse
        else spacecraft.absorptivity * spacecraft.panel_area_m2 * solar_flux_w_m2 * 0.18
    )
    absorbed_albedo_w = spacecraft.absorptivity * spacecraft.panel_area_m2 * albedo_flux_w_m2
    internal_heat_w = 0.82 * load_power_w
    radiated_w = (
        spacecraft.emissivity
        * STEFAN_BOLTZMANN_W_M2_K4
        * spacecraft.radiator_area_m2
        * (state.temperature_k**4 - deep_space_temperature_k**4)
    )
    temperature_k = state.temperature_k + (
        internal_heat_w + absorbed_solar_w + absorbed_albedo_w - radiated_w
    ) * dt_s / spacecraft.thermal_capacity_j_k
    temperature_k = max(deep_space_temperature_k, temperature_k)

    generated_gb = spacecraft.data_generation_mbps * dt_s / 8000.0 if payload_active else 0.0
    transmitted_gb = spacecraft.downlink_rate_mbps * dt_s / 8000.0 if downlink_active else 0.0
    stored_data_gb = min(
        spacecraft.storage_capacity_gb,
        max(0.0, state.stored_data_gb + generated_gb - transmitted_gb),
    )

    return BusStep(
        state=BusState(battery_wh, temperature_k, stored_data_gb),
        in_eclipse=in_eclipse,
        payload_active=payload_active,
        downlink_active=downlink_active,
        generated_power_w=generated_power_w,
        load_power_w=load_power_w,
    )
