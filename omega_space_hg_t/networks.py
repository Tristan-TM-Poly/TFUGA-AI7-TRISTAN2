"""R0.3 physical and information network models for Ω-SPACE-HG-T∞.

The models are transparent reduced-order design baselines. They do not replace
mission-specific electrical, thermal, RF, ground-network or flight analyses.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import asin, log10, pi, sin, cos, sqrt
from typing import Any, Iterable, Mapping

from .models import OrbitState, Vector3
from .orbit import dot, norm, subtract


STEFAN_BOLTZMANN_W_M2_K4 = 5.670374419e-8
BOLTZMANN_J_K = 1.380649e-23
SPEED_OF_LIGHT_M_S = 299_792_458.0


@dataclass(frozen=True)
class ThermalNodeConfig:
    node_id: str
    heat_capacity_j_k: float
    initial_temperature_k: float
    radiator_area_m2: float = 0.0
    emissivity: float = 0.0
    minimum_temperature_k: float = 0.0
    maximum_temperature_k: float = 1.0e9

    def validate(self) -> None:
        if not self.node_id:
            raise ValueError("thermal node id cannot be empty")
        if self.heat_capacity_j_k <= 0.0 or self.initial_temperature_k <= 0.0:
            raise ValueError("thermal capacity and temperature must be positive")
        if self.radiator_area_m2 < 0.0 or not 0.0 <= self.emissivity <= 1.0:
            raise ValueError("invalid radiator parameters")
        if self.minimum_temperature_k > self.maximum_temperature_k:
            raise ValueError("thermal temperature bounds are inverted")


@dataclass(frozen=True)
class ThermalConductance:
    node_a: str
    node_b: str
    conductance_w_k: float

    def validate(self) -> None:
        if self.node_a == self.node_b:
            raise ValueError("thermal conductance requires two different nodes")
        if self.conductance_w_k < 0.0:
            raise ValueError("thermal conductance cannot be negative")


@dataclass(frozen=True)
class ThermalNetworkState:
    temperatures_k: dict[str, float]
    epoch_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"temperatures_k": dict(sorted(self.temperatures_k.items())), "epoch_s": self.epoch_s}


@dataclass(frozen=True)
class ThermalStepReport:
    state: ThermalNetworkState
    node_net_heat_w: dict[str, float]
    radiated_heat_w: dict[str, float]
    conductive_exchange_w: dict[str, float]
    internal_energy_change_j: float
    external_energy_input_j: float
    energy_balance_residual_j: float
    violations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.to_dict()
        payload["violations"] = list(self.violations)
        return payload


class ThermalNetwork:
    def __init__(self, nodes: Iterable[ThermalNodeConfig], conductances: Iterable[ThermalConductance] = ()):
        node_list = tuple(nodes)
        if not node_list:
            raise ValueError("thermal network requires at least one node")
        self.nodes = {node.node_id: node for node in node_list}
        if len(self.nodes) != len(node_list):
            raise ValueError("thermal node ids must be unique")
        for node in self.nodes.values():
            node.validate()
        self.conductances = tuple(conductances)
        for edge in self.conductances:
            edge.validate()
            if edge.node_a not in self.nodes or edge.node_b not in self.nodes:
                raise ValueError("thermal conductance references an unknown node")

    def initial_state(self) -> ThermalNetworkState:
        return ThermalNetworkState(
            {node_id: node.initial_temperature_k for node_id, node in self.nodes.items()},
            0.0,
        )

    def step(
        self,
        state: ThermalNetworkState,
        dt_s: float,
        *,
        applied_heat_w: Mapping[str, float] | None = None,
        sink_temperature_k: float = 3.0,
    ) -> ThermalStepReport:
        if dt_s <= 0.0 or sink_temperature_k < 0.0:
            raise ValueError("time step must be positive and sink temperature nonnegative")
        if set(state.temperatures_k) != set(self.nodes):
            raise ValueError("thermal state node set does not match network")
        applied = {node_id: float((applied_heat_w or {}).get(node_id, 0.0)) for node_id in self.nodes}
        conductive = {node_id: 0.0 for node_id in self.nodes}
        for edge in self.conductances:
            temperature_a = state.temperatures_k[edge.node_a]
            temperature_b = state.temperatures_k[edge.node_b]
            heat_a_to_b = edge.conductance_w_k * (temperature_a - temperature_b)
            conductive[edge.node_a] -= heat_a_to_b
            conductive[edge.node_b] += heat_a_to_b

        radiated: dict[str, float] = {}
        net: dict[str, float] = {}
        next_temperatures: dict[str, float] = {}
        violations: list[str] = []
        internal_energy_change = 0.0
        for node_id, node in self.nodes.items():
            temperature = state.temperatures_k[node_id]
            radiation = (
                node.emissivity
                * STEFAN_BOLTZMANN_W_M2_K4
                * node.radiator_area_m2
                * (temperature**4 - sink_temperature_k**4)
            )
            radiated[node_id] = radiation
            net_heat = applied[node_id] + conductive[node_id] - radiation
            net[node_id] = net_heat
            next_temperature = temperature + net_heat * dt_s / node.heat_capacity_j_k
            if next_temperature <= 0.0:
                violations.append(f"{node_id}: nonphysical temperature")
                next_temperature = max(1e-9, next_temperature)
            if not node.minimum_temperature_k <= next_temperature <= node.maximum_temperature_k:
                violations.append(f"{node_id}: temperature outside declared bounds")
            next_temperatures[node_id] = next_temperature
            internal_energy_change += node.heat_capacity_j_k * (next_temperature - temperature)

        external_power = sum(applied.values()) - sum(radiated.values())
        external_energy = external_power * dt_s
        residual = internal_energy_change - external_energy
        return ThermalStepReport(
            state=ThermalNetworkState(next_temperatures, state.epoch_s + dt_s),
            node_net_heat_w=net,
            radiated_heat_w=radiated,
            conductive_exchange_w=conductive,
            internal_energy_change_j=internal_energy_change,
            external_energy_input_j=external_energy,
            energy_balance_residual_j=residual,
            violations=tuple(violations),
        )


@dataclass(frozen=True)
class BatteryConfig:
    capacity_wh: float
    initial_soc: float
    nominal_voltage_v: float
    internal_resistance_ohm: float
    maximum_charge_current_a: float
    maximum_discharge_current_a: float
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    minimum_soc: float = 0.10
    maximum_soc: float = 1.0

    def validate(self) -> None:
        if self.capacity_wh <= 0.0 or self.nominal_voltage_v <= 0.0:
            raise ValueError("battery capacity and voltage must be positive")
        if self.internal_resistance_ohm < 0.0:
            raise ValueError("battery resistance cannot be negative")
        if self.maximum_charge_current_a <= 0.0 or self.maximum_discharge_current_a <= 0.0:
            raise ValueError("battery current limits must be positive")
        for value in (self.initial_soc, self.charge_efficiency, self.discharge_efficiency, self.minimum_soc, self.maximum_soc):
            if not 0.0 <= value <= 1.0:
                raise ValueError("battery fractions and efficiencies must lie in [0, 1]")
        if self.minimum_soc > self.maximum_soc:
            raise ValueError("battery SOC bounds are inverted")


@dataclass(frozen=True)
class BatteryState:
    stored_energy_wh: float
    throughput_wh: float = 0.0
    epoch_s: float = 0.0

    def soc(self, config: BatteryConfig) -> float:
        return self.stored_energy_wh / config.capacity_wh

    def to_dict(self, config: BatteryConfig) -> dict[str, float]:
        return {
            "stored_energy_wh": self.stored_energy_wh,
            "throughput_wh": self.throughput_wh,
            "epoch_s": self.epoch_s,
            "soc": self.soc(config),
        }


@dataclass(frozen=True)
class PowerStepReport:
    state: BatteryState
    generated_power_w: float
    requested_load_w: float
    served_load_w: float
    curtailed_generation_w: float
    unmet_load_w: float
    battery_terminal_power_w: float
    resistive_loss_w: float
    battery_current_a: float
    violations: tuple[str, ...]

    def to_dict(self, config: BatteryConfig) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.to_dict(config)
        payload["violations"] = list(self.violations)
        return payload


def initial_battery_state(config: BatteryConfig) -> BatteryState:
    config.validate()
    return BatteryState(config.capacity_wh * config.initial_soc)


def power_step(
    state: BatteryState,
    config: BatteryConfig,
    dt_s: float,
    *,
    generated_power_w: float,
    requested_load_w: float,
) -> PowerStepReport:
    config.validate()
    if dt_s <= 0.0 or generated_power_w < 0.0 or requested_load_w < 0.0:
        raise ValueError("power step inputs must be nonnegative and dt positive")

    net_generation_w = generated_power_w - requested_load_w
    stored = state.stored_energy_wh
    throughput = state.throughput_wh
    served_load = requested_load_w
    curtailed = 0.0
    unmet = 0.0
    terminal_power = 0.0
    current = 0.0
    resistive_loss = 0.0

    if net_generation_w >= 0.0:
        current_limit_power = config.maximum_charge_current_a * config.nominal_voltage_v
        accepted_terminal_power = min(net_generation_w, current_limit_power)
        current = accepted_terminal_power / config.nominal_voltage_v
        resistive_loss = current * current * config.internal_resistance_ohm
        chemical_power = max(0.0, accepted_terminal_power - resistive_loss) * config.charge_efficiency
        available_capacity_wh = config.capacity_wh * config.maximum_soc - stored
        accepted_chemical_wh = min(chemical_power * dt_s / 3600.0, max(0.0, available_capacity_wh))
        stored += accepted_chemical_wh
        throughput += accepted_chemical_wh
        terminal_power = accepted_terminal_power
        actual_input_power = (
            accepted_chemical_wh * 3600.0 / dt_s / max(config.charge_efficiency, 1e-30)
            + resistive_loss
        )
        curtailed = max(0.0, net_generation_w - actual_input_power)
    else:
        deficit_w = -net_generation_w
        current_limit_power = config.maximum_discharge_current_a * config.nominal_voltage_v
        usable_energy_wh = max(0.0, stored - config.capacity_wh * config.minimum_soc)
        maximum_chemical_power = usable_energy_wh * 3600.0 / dt_s
        quadratic = config.internal_resistance_ohm / config.nominal_voltage_v**2
        if quadratic <= 0.0:
            requested_chemical_power = deficit_w / max(config.discharge_efficiency, 1e-30)
        else:
            discriminant = config.discharge_efficiency**2 - 4.0 * quadratic * deficit_w
            requested_chemical_power = (
                config.discharge_efficiency - sqrt(max(0.0, discriminant))
            ) / (2.0 * quadratic)
            if discriminant < 0.0:
                requested_chemical_power = current_limit_power
        chemical_power = min(requested_chemical_power, maximum_chemical_power, current_limit_power)
        current = -chemical_power / config.nominal_voltage_v
        resistive_loss = current * current * config.internal_resistance_ohm
        delivered_power = max(0.0, chemical_power * config.discharge_efficiency - resistive_loss)
        stored -= chemical_power * dt_s / 3600.0
        throughput += chemical_power * dt_s / 3600.0
        terminal_power = -delivered_power
        unmet = max(0.0, deficit_w - delivered_power)
        served_load = requested_load_w - unmet

    soc = stored / config.capacity_wh
    violations: list[str] = []
    if soc < config.minimum_soc - 1e-12:
        violations.append("battery SOC below minimum")
    if soc > config.maximum_soc + 1e-12:
        violations.append("battery SOC above maximum")
    if unmet > 1e-9:
        violations.append("load shedding required")
    return PowerStepReport(
        state=BatteryState(stored, throughput, state.epoch_s + dt_s),
        generated_power_w=generated_power_w,
        requested_load_w=requested_load_w,
        served_load_w=served_load,
        curtailed_generation_w=curtailed,
        unmet_load_w=unmet,
        battery_terminal_power_w=terminal_power,
        resistive_loss_w=resistive_loss,
        battery_current_a=current,
        violations=tuple(violations),
    )


@dataclass(frozen=True)
class LinkBudgetConfig:
    frequency_hz: float
    distance_m: float
    transmit_power_w: float
    transmit_gain_dbi: float
    receive_gain_dbi: float
    system_losses_db: float
    system_noise_temperature_k: float
    bandwidth_hz: float
    required_eb_n0_db: float = 3.0

    def validate(self) -> None:
        positives = (
            self.frequency_hz,
            self.distance_m,
            self.transmit_power_w,
            self.system_noise_temperature_k,
            self.bandwidth_hz,
        )
        if any(value <= 0.0 for value in positives):
            raise ValueError("link frequency, distance, power, noise temperature and bandwidth must be positive")


@dataclass(frozen=True)
class LinkBudgetResult:
    wavelength_m: float
    free_space_path_loss_db: float
    received_power_dbw: float
    noise_power_dbw: float
    carrier_to_noise_db: float
    carrier_to_noise_density_dbhz: float
    maximum_bitrate_bps: float
    margin_at_bandwidth_db: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def watts_to_dbw(power_w: float) -> float:
    if power_w <= 0.0:
        raise ValueError("power must be positive")
    return 10.0 * log10(power_w)


def link_budget(config: LinkBudgetConfig) -> LinkBudgetResult:
    config.validate()
    wavelength = SPEED_OF_LIGHT_M_S / config.frequency_hz
    path_loss = 20.0 * log10(4.0 * pi * config.distance_m / wavelength)
    received_dbw = (
        watts_to_dbw(config.transmit_power_w)
        + config.transmit_gain_dbi
        + config.receive_gain_dbi
        - path_loss
        - config.system_losses_db
    )
    noise_dbw = 10.0 * log10(BOLTZMANN_J_K * config.system_noise_temperature_k * config.bandwidth_hz)
    carrier_to_noise = received_dbw - noise_dbw
    c_n0 = received_dbw - 10.0 * log10(BOLTZMANN_J_K * config.system_noise_temperature_k)
    maximum_bitrate = 10.0 ** ((c_n0 - config.required_eb_n0_db) / 10.0)
    margin_at_bandwidth = c_n0 - 10.0 * log10(config.bandwidth_hz) - config.required_eb_n0_db
    return LinkBudgetResult(
        wavelength,
        path_loss,
        received_dbw,
        noise_dbw,
        carrier_to_noise,
        c_n0,
        maximum_bitrate,
        margin_at_bandwidth,
    )


@dataclass(frozen=True)
class GroundStation:
    station_id: str
    latitude_rad: float
    longitude_rad: float
    altitude_m: float = 0.0
    minimum_elevation_rad: float = 0.0

    def validate(self) -> None:
        if not self.station_id:
            raise ValueError("ground-station id cannot be empty")
        if not -0.5 * pi <= self.latitude_rad <= 0.5 * pi:
            raise ValueError("ground-station latitude outside valid range")
        if not -pi <= self.longitude_rad <= pi:
            raise ValueError("ground-station longitude outside valid range")
        if not 0.0 <= self.minimum_elevation_rad < 0.5 * pi:
            raise ValueError("minimum elevation outside valid range")


def station_position_inertial(
    station: GroundStation,
    body_radius_m: float,
    epoch_s: float,
    body_rotation_rad_s: float,
) -> Vector3:
    station.validate()
    radius = body_radius_m + station.altitude_m
    longitude = station.longitude_rad + body_rotation_rad_s * epoch_s
    cos_latitude = cos(station.latitude_rad)
    return (
        radius * cos_latitude * cos(longitude),
        radius * cos_latitude * sin(longitude),
        radius * sin(station.latitude_rad),
    )


def elevation_angle_rad(
    state: OrbitState,
    station: GroundStation,
    body_radius_m: float,
    body_rotation_rad_s: float,
) -> float:
    station_position = station_position_inertial(
        station,
        body_radius_m,
        state.epoch_s,
        body_rotation_rad_s,
    )
    line_of_sight = subtract(state.position_m, station_position)
    los_norm = norm(line_of_sight)
    station_norm = norm(station_position)
    sine_elevation = dot(line_of_sight, station_position) / (los_norm * station_norm)
    return asin(max(-1.0, min(1.0, sine_elevation)))


@dataclass(frozen=True)
class ContactWindow:
    start_s: float
    end_s: float
    maximum_elevation_rad: float

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s

    def to_dict(self) -> dict[str, float]:
        return {
            "start_s": self.start_s,
            "end_s": self.end_s,
            "duration_s": self.duration_s,
            "maximum_elevation_rad": self.maximum_elevation_rad,
        }


def contact_windows(
    states: Iterable[OrbitState],
    station: GroundStation,
    body_radius_m: float,
    body_rotation_rad_s: float,
) -> tuple[ContactWindow, ...]:
    samples = tuple(states)
    if not samples:
        return ()
    windows: list[ContactWindow] = []
    start: float | None = None
    maximum = -0.5 * pi
    previous_epoch = samples[0].epoch_s
    for state in samples:
        elevation = elevation_angle_rad(state, station, body_radius_m, body_rotation_rad_s)
        visible = elevation >= station.minimum_elevation_rad
        if visible and start is None:
            start = state.epoch_s
            maximum = elevation
        elif visible:
            maximum = max(maximum, elevation)
        elif start is not None:
            windows.append(ContactWindow(start, previous_epoch, maximum))
            start = None
            maximum = -0.5 * pi
        previous_epoch = state.epoch_s
    if start is not None:
        windows.append(ContactWindow(start, samples[-1].epoch_s, maximum))
    return tuple(windows)


@dataclass(frozen=True)
class DataQueueConfig:
    capacity_bits: float

    def validate(self) -> None:
        if self.capacity_bits <= 0.0:
            raise ValueError("data queue capacity must be positive")


@dataclass(frozen=True)
class DataQueueState:
    stored_bits: float = 0.0
    delivered_bits: float = 0.0
    dropped_bits: float = 0.0
    epoch_s: float = 0.0

    def to_dict(self, config: DataQueueConfig) -> dict[str, float]:
        return {
            "stored_bits": self.stored_bits,
            "stored_fraction": self.stored_bits / config.capacity_bits,
            "delivered_bits": self.delivered_bits,
            "dropped_bits": self.dropped_bits,
            "epoch_s": self.epoch_s,
        }


def data_queue_step(
    state: DataQueueState,
    config: DataQueueConfig,
    dt_s: float,
    *,
    generated_bps: float,
    downlink_bps: float,
) -> DataQueueState:
    config.validate()
    if dt_s <= 0.0 or generated_bps < 0.0 or downlink_bps < 0.0:
        raise ValueError("data queue rates must be nonnegative and dt positive")
    available = state.stored_bits + generated_bps * dt_s
    delivered = min(available, downlink_bps * dt_s)
    remaining = available - delivered
    stored = min(config.capacity_bits, remaining)
    dropped = max(0.0, remaining - config.capacity_bits)
    return DataQueueState(
        stored_bits=stored,
        delivered_bits=state.delivered_bits + delivered,
        dropped_bits=state.dropped_bits + dropped,
        epoch_s=state.epoch_s + dt_s,
    )
