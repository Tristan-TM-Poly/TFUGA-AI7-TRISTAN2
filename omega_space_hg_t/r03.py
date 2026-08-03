"""Ω-SPACE-HG-T∞ R0.3 coupled physical and information networks."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import cos, radians, sin
from typing import Any, Callable

from .models import OrbitState, Vector3
from .networks import (
    BatteryConfig,
    DataQueueConfig,
    DataQueueState,
    GroundStation,
    LinkBudgetConfig,
    ThermalConductance,
    ThermalNetwork,
    ThermalNodeConfig,
    contact_windows,
    data_queue_step,
    elevation_angle_rad,
    initial_battery_state,
    link_budget,
    power_step,
)
from .oak import EARTH_MU_M3_S2, EARTH_RADIUS_M
from .orbit import dot, norm, orbital_period_s, scale, subtract
from .perturbations import propagate_perturbed
from .r02 import EARTH_ROTATION_RAD_S, canonical_inclined_orbit, canonical_perturbation_config


@dataclass(frozen=True)
class R03Check:
    name: str
    passed: bool
    observed: Any
    criterion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_ground_station() -> GroundStation:
    return GroundStation(
        station_id="Montreal-OAK-Ground",
        latitude_rad=radians(45.5019),
        longitude_rad=radians(-73.5674),
        altitude_m=35.0,
        minimum_elevation_rad=radians(8.0),
    )


def canonical_battery() -> BatteryConfig:
    return BatteryConfig(
        capacity_wh=420.0,
        initial_soc=0.78,
        nominal_voltage_v=28.0,
        internal_resistance_ohm=0.08,
        maximum_charge_current_a=8.0,
        maximum_discharge_current_a=10.0,
        charge_efficiency=0.96,
        discharge_efficiency=0.95,
        minimum_soc=0.15,
        maximum_soc=0.98,
    )


def canonical_thermal_network() -> ThermalNetwork:
    return ThermalNetwork(
        nodes=(
            ThermalNodeConfig("bus", 52_000.0, 293.15, 0.16, 0.82, 268.0, 323.0),
            ThermalNodeConfig("payload", 18_000.0, 293.15, 0.05, 0.78, 273.0, 318.0),
            ThermalNodeConfig("battery", 25_000.0, 291.15, 0.03, 0.70, 275.0, 313.0),
        ),
        conductances=(
            ThermalConductance("bus", "payload", 0.45),
            ThermalConductance("bus", "battery", 0.30),
            ThermalConductance("payload", "battery", 0.08),
        ),
    )


def _unit(vector: Vector3) -> Vector3:
    return scale(1.0 / norm(vector), vector)


def cylindrical_illumination(state: OrbitState, sun_direction_inertial: Vector3 = (1.0, 0.0, 0.0)) -> bool:
    """Return a binary cylindrical-shadow baseline."""

    sun = _unit(sun_direction_inertial)
    projection = dot(state.position_m, sun)
    if projection >= 0.0:
        return True
    perpendicular = subtract(state.position_m, scale(projection, sun))
    return norm(perpendicular) > EARTH_RADIUS_M


def _payload_active(epoch_s: float, period_s: float, illuminated: bool, contact: bool) -> bool:
    phase = (epoch_s % period_s) / period_s
    return illuminated and not contact and 0.08 <= phase < 0.34


def _link_for_distance(distance_m: float) -> LinkBudgetConfig:
    return LinkBudgetConfig(
        frequency_hz=2.2e9,
        distance_m=distance_m,
        transmit_power_w=8.0,
        transmit_gain_dbi=6.0,
        receive_gain_dbi=32.0,
        system_losses_db=3.0,
        system_noise_temperature_k=420.0,
        bandwidth_hz=10.0e6,
        required_eb_n0_db=4.5,
    )


def simulate_r03_networks(
    *,
    duration_orbits: float = 8.0,
    step_s: float = 20.0,
) -> dict[str, Any]:
    if duration_orbits <= 0.0 or step_s <= 0.0:
        raise ValueError("duration_orbits and step_s must be positive")
    initial_orbit = canonical_inclined_orbit()
    period_s = orbital_period_s(initial_orbit, EARTH_MU_M3_S2)
    orbit_states = propagate_perturbed(
        initial_orbit,
        duration_orbits * period_s,
        step_s,
        canonical_perturbation_config(),
    )
    station = canonical_ground_station()
    battery_config = canonical_battery()
    battery = initial_battery_state(battery_config)
    thermal_network = canonical_thermal_network()
    thermal = thermal_network.initial_state()
    data_config = DataQueueConfig(capacity_bits=256.0 * 8.0e9)
    data = DataQueueState()

    minimum_soc = battery.soc(battery_config)
    maximum_soc = minimum_soc
    maximum_stored_fraction = 0.0
    maximum_abs_thermal_residual_j = 0.0
    total_unmet_load_wh = 0.0
    total_curtailed_wh = 0.0
    total_contact_s = 0.0
    maximum_elevation_rad = -1.0
    maximum_link_margin_db = -1.0e9
    minimum_link_margin_db = 1.0e9
    violations: list[str] = []
    samples: list[dict[str, Any]] = []

    for index in range(len(orbit_states) - 1):
        state = orbit_states[index]
        next_state = orbit_states[index + 1]
        dt_s = next_state.epoch_s - state.epoch_s
        illuminated = cylindrical_illumination(state)
        elevation = elevation_angle_rad(state, station, EARTH_RADIUS_M, EARTH_ROTATION_RAD_S)
        contact = elevation >= station.minimum_elevation_rad
        payload_active = _payload_active(state.epoch_s, period_s, illuminated, contact)

        generated_power_w = 155.0 if illuminated else 0.0
        load_power_w = 34.0 + (38.0 if payload_active else 0.0) + (48.0 if contact else 0.0)
        power = power_step(
            battery,
            battery_config,
            dt_s,
            generated_power_w=generated_power_w,
            requested_load_w=load_power_w,
        )
        battery = power.state
        total_unmet_load_wh += power.unmet_load_w * dt_s / 3600.0
        total_curtailed_wh += power.curtailed_generation_w * dt_s / 3600.0
        minimum_soc = min(minimum_soc, battery.soc(battery_config))
        maximum_soc = max(maximum_soc, battery.soc(battery_config))
        violations.extend(power.violations)

        link_rate_bps = 0.0
        link_margin_db = None
        if contact:
            station_position = (
                (EARTH_RADIUS_M + station.altitude_m)
                * cos(station.latitude_rad)
                * cos(station.longitude_rad + EARTH_ROTATION_RAD_S * state.epoch_s),
                (EARTH_RADIUS_M + station.altitude_m)
                * cos(station.latitude_rad)
                * sin(station.longitude_rad + EARTH_ROTATION_RAD_S * state.epoch_s),
                (EARTH_RADIUS_M + station.altitude_m) * sin(station.latitude_rad),
            )
            distance_m = norm(subtract(state.position_m, station_position))
            link = link_budget(_link_for_distance(distance_m))
            link_rate_bps = min(20.0e6, link.maximum_bitrate_bps)
            link_margin_db = link.margin_at_bandwidth_db
            maximum_link_margin_db = max(maximum_link_margin_db, link_margin_db)
            minimum_link_margin_db = min(minimum_link_margin_db, link_margin_db)
            maximum_elevation_rad = max(maximum_elevation_rad, elevation)
            total_contact_s += dt_s

        data = data_queue_step(
            data,
            data_config,
            dt_s,
            generated_bps=12.0e6 if payload_active else 0.0,
            downlink_bps=link_rate_bps,
        )
        maximum_stored_fraction = max(maximum_stored_fraction, data.stored_bits / data_config.capacity_bits)

        heat = {
            "bus": 0.52 * 34.0 + (12.0 if illuminated else 0.0) + (0.45 * 48.0 if contact else 0.0),
            "payload": 0.72 * 38.0 if payload_active else 2.5,
            "battery": power.resistive_loss_w + 1.8,
        }
        thermal_report = thermal_network.step(thermal, dt_s, applied_heat_w=heat, sink_temperature_k=3.0)
        thermal = thermal_report.state
        maximum_abs_thermal_residual_j = max(
            maximum_abs_thermal_residual_j,
            abs(thermal_report.energy_balance_residual_j),
        )
        violations.extend(thermal_report.violations)

        if index % max(1, int(round(300.0 / step_s))) == 0:
            samples.append(
                {
                    "epoch_s": state.epoch_s,
                    "illuminated": illuminated,
                    "contact": contact,
                    "payload_active": payload_active,
                    "elevation_rad": elevation,
                    "link_margin_db": link_margin_db,
                    "battery_soc": battery.soc(battery_config),
                    "temperatures_k": dict(thermal.temperatures_k),
                    "stored_data_fraction": data.stored_bits / data_config.capacity_bits,
                }
            )

    windows = contact_windows(orbit_states, station, EARTH_RADIUS_M, EARTH_ROTATION_RAD_S)
    temperatures_by_node = {
        node_id: [sample["temperatures_k"][node_id] for sample in samples]
        for node_id in thermal.temperatures_k
    }
    temperature_extrema = {
        node_id: {"minimum_k": min(values), "maximum_k": max(values)}
        for node_id, values in temperatures_by_node.items()
    }
    unique_violations = tuple(sorted(set(violations)))
    return {
        "release": "R0.3",
        "duration_s": orbit_states[-1].epoch_s - orbit_states[0].epoch_s,
        "step_s": step_s,
        "orbit_state_count": len(orbit_states),
        "power": {
            "minimum_soc": minimum_soc,
            "maximum_soc": maximum_soc,
            "final": battery.to_dict(battery_config),
            "total_unmet_load_wh": total_unmet_load_wh,
            "total_curtailed_generation_wh": total_curtailed_wh,
        },
        "thermal": {
            "final": thermal.to_dict(),
            "temperature_extrema": temperature_extrema,
            "maximum_abs_energy_balance_residual_j": maximum_abs_thermal_residual_j,
        },
        "communications": {
            "ground_station": asdict(station),
            "contact_window_count": len(windows),
            "total_contact_s_sampled": total_contact_s,
            "maximum_elevation_rad": maximum_elevation_rad,
            "minimum_link_margin_db": None if minimum_link_margin_db == 1.0e9 else minimum_link_margin_db,
            "maximum_link_margin_db": None if maximum_link_margin_db == -1.0e9 else maximum_link_margin_db,
            "windows": [window.to_dict() for window in windows],
        },
        "data": {
            "final": data.to_dict(data_config),
            "maximum_stored_fraction": maximum_stored_fraction,
            "delivered_gb": data.delivered_bits / 8.0e9,
            "dropped_gb": data.dropped_bits / 8.0e9,
        },
        "sampled_history": samples,
        "violations": list(unique_violations),
        "safe_fixture": not unique_violations and data.dropped_bits == 0.0 and total_unmet_load_wh < 1e-9,
        "operational_network_claimed": False,
        "flight_qualified_claimed": False,
        "regulatory_approval_claimed": False,
    }


def _capture(name: str, criterion: str, function: Callable[[], tuple[bool, Any]]) -> R03Check:
    try:
        passed, observed = function()
        return R03Check(name, bool(passed), observed, criterion)
    except Exception as error:
        return R03Check(name, False, f"{type(error).__name__}: {error}", criterion)


def run_r03_oak_benchmarks() -> dict[str, Any]:
    def thermal_conservation_check() -> tuple[bool, Any]:
        network = ThermalNetwork(
            (
                ThermalNodeConfig("a", 1000.0, 310.0),
                ThermalNodeConfig("b", 2000.0, 290.0),
            ),
            (ThermalConductance("a", "b", 4.0),),
        )
        state = network.initial_state()
        initial_energy = 1000.0 * 310.0 + 2000.0 * 290.0
        maximum_residual = 0.0
        for _ in range(50):
            report = network.step(state, 0.5)
            state = report.state
            maximum_residual = max(maximum_residual, abs(report.energy_balance_residual_j))
        final_energy = 1000.0 * state.temperatures_k["a"] + 2000.0 * state.temperatures_k["b"]
        error = abs(final_energy - initial_energy)
        return error < 1e-8 and maximum_residual < 1e-8, {
            "closed_network_energy_error_j": error,
            "maximum_step_residual_j": maximum_residual,
        }

    def inverse_square_link_check() -> tuple[bool, Any]:
        near = link_budget(_link_for_distance(1.0e6))
        far = link_budget(_link_for_distance(2.0e6))
        increase = far.free_space_path_loss_db - near.free_space_path_loss_db
        return abs(increase - 6.020599913279624) < 1e-10, increase

    def integrated_network_check() -> tuple[bool, Any]:
        report = simulate_r03_networks(duration_orbits=8.0, step_s=20.0)
        observed = {
            "safe_fixture": report["safe_fixture"],
            "minimum_soc": report["power"]["minimum_soc"],
            "contact_window_count": report["communications"]["contact_window_count"],
            "delivered_gb": report["data"]["delivered_gb"],
            "dropped_gb": report["data"]["dropped_gb"],
            "maximum_stored_fraction": report["data"]["maximum_stored_fraction"],
        }
        passed = (
            report["safe_fixture"]
            and observed["minimum_soc"] > 0.15
            and observed["contact_window_count"] >= 1
            and observed["delivered_gb"] > 0.0
            and observed["dropped_gb"] == 0.0
            and observed["maximum_stored_fraction"] < 0.95
        )
        return passed, observed

    def deterministic_replay_check() -> tuple[bool, Any]:
        first = simulate_r03_networks(duration_orbits=2.0, step_s=30.0)
        second = simulate_r03_networks(duration_orbits=2.0, step_s=30.0)
        keys = ("power", "thermal", "communications", "data", "safe_fixture")
        return all(first[key] == second[key] for key in keys), {
            "safe_fixture": first["safe_fixture"],
            "final_soc": first["power"]["final"]["soc"],
            "final_stored_bits": first["data"]["final"]["stored_bits"],
        }

    def battery_limits_check() -> tuple[bool, Any]:
        config = BatteryConfig(100.0, 0.5, 10.0, 0.1, 2.0, 2.0, minimum_soc=0.2, maximum_soc=0.9)
        state = initial_battery_state(config)
        charge = power_step(state, config, 3600.0, generated_power_w=1000.0, requested_load_w=0.0)
        discharge = power_step(charge.state, config, 3600.0, generated_power_w=0.0, requested_load_w=1000.0)
        observed = {
            "charged_soc": charge.state.soc(config),
            "discharged_soc": discharge.state.soc(config),
            "unmet_load_w": discharge.unmet_load_w,
        }
        return (
            charge.state.soc(config) <= config.maximum_soc + 1e-12
            and discharge.state.soc(config) >= config.minimum_soc - 1e-12
            and discharge.unmet_load_w > 0.0
        ), observed

    def claim_boundary_check() -> tuple[bool, Any]:
        boundaries = {
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
            "flight_qualified_claimed": False,
            "operational_network_claimed": False,
            "regulatory_approval_claimed": False,
        }
        return not any(boundaries.values()), boundaries

    checks = (
        _capture("closed_thermal_energy_conservation", "closed conductive network conserves energy to 1e-8 J", thermal_conservation_check),
        _capture("free_space_inverse_square", "doubling distance adds 6.020599913 dB path loss", inverse_square_link_check),
        _capture("integrated_network_fixture", "power thermal contact and data gates pass without drops", integrated_network_check),
        _capture("network_deterministic_replay", "identical network inputs reproduce metrics exactly", deterministic_replay_check),
        _capture("battery_bounds_and_shedding", "SOC bounds hold and impossible load is reported", battery_limits_check),
        _capture("r03_claim_boundaries", "no proof validation flight operational or regulatory claim", claim_boundary_check),
    )
    return {
        "suite": "OMEGA-SPACE-HG-T-R0.3-OAKBench",
        "passed": all(check.passed for check in checks),
        "checks": [check.to_dict() for check in checks],
        "theorem_claimed": False,
        "scientific_validation_claimed": False,
        "flight_qualified_claimed": False,
        "operational_network_claimed": False,
        "regulatory_approval_claimed": False,
        "limitations": [
            "explicit-Euler lumped thermal network with caller-selected nodes and conductances",
            "battery model uses energy, current limits and ohmic loss without electrochemical dynamics or aging calibration",
            "free-space link budget omits atmosphere, polarization, coding implementation, interference and regulatory coordination",
            "spherical rotating-body ground visibility sampled at the simulation cadence",
            "binary cylindrical eclipse and fixed solar-array output",
            "deterministic mode schedule and no flight or operations qualification",
        ],
    }
