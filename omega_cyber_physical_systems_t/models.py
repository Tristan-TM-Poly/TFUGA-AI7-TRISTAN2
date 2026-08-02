from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


DOMAINS = (
    "mechanical_translational",
    "mechanical_rotational",
    "electrical_power",
    "electronic_signal",
    "thermal",
    "fluid",
    "software",
    "data",
)
PORT_DIRECTIONS = ("input", "output", "bidirectional")
COMPARATORS = ("<=", ">=", "==")


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
class Port:
    port_id: str
    domain: str
    direction: str
    effort_unit: str
    flow_unit: str
    capacity: float | None = None
    description: str = ""

    def validate(self) -> None:
        if not self.port_id.strip():
            raise ValueError("port_id cannot be empty")
        if self.domain not in DOMAINS:
            raise ValueError(f"unknown port domain: {self.domain}")
        if self.direction not in PORT_DIRECTIONS:
            raise ValueError(f"unknown port direction: {self.direction}")
        if not self.effort_unit.strip() or not self.flow_unit.strip():
            raise ValueError("effort_unit and flow_unit are required")
        if self.capacity is not None and self.capacity <= 0:
            raise ValueError("port capacity must be positive when supplied")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class Component:
    component_id: str
    kind: str
    domains: tuple[str, ...]
    ports: tuple[Port, ...]
    parameters: Mapping[str, float | int | str | bool] = field(default_factory=dict)
    criticality: int = 1
    physical: bool = True
    software: bool = False
    provenance: str = "internal-conceptual-fixture"

    @classmethod
    def build(
        cls,
        *,
        component_id: str,
        kind: str,
        domains: Sequence[str],
        ports: Sequence[Port],
        parameters: Mapping[str, float | int | str | bool] | None = None,
        criticality: int = 1,
        physical: bool = True,
        software: bool = False,
        provenance: str = "internal-conceptual-fixture",
    ) -> "Component":
        return cls(
            component_id=component_id,
            kind=kind,
            domains=tuple(domains),
            ports=tuple(ports),
            parameters={} if parameters is None else dict(parameters),
            criticality=criticality,
            physical=physical,
            software=software,
            provenance=provenance,
        )

    def validate(self) -> None:
        if not self.component_id.strip() or not self.kind.strip():
            raise ValueError("component_id and kind are required")
        if not self.domains:
            raise ValueError("component must declare at least one domain")
        if any(domain not in DOMAINS for domain in self.domains):
            raise ValueError("component contains an unknown domain")
        if len(set(self.domains)) != len(self.domains):
            raise ValueError("component domains must be unique")
        if not 1 <= self.criticality <= 5:
            raise ValueError("criticality must lie in [1, 5]")
        if not self.provenance.strip():
            raise ValueError("component provenance is required")
        port_ids: set[str] = set()
        for port in self.ports:
            port.validate()
            if port.port_id in port_ids:
                raise ValueError(f"duplicate port_id on component {self.component_id}")
            port_ids.add(port.port_id)
            if port.domain not in self.domains:
                raise ValueError("port domain must be declared by its component")
        if self.software and "software" not in self.domains:
            raise ValueError("software components must declare the software domain")

    def port(self, port_id: str) -> Port:
        for item in self.ports:
            if item.port_id == port_id:
                return item
        raise KeyError(f"unknown port {self.component_id}.{port_id}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "component_id": self.component_id,
            "kind": self.kind,
            "domains": list(self.domains),
            "ports": [port.to_dict() for port in self.ports],
            "parameters": dict(self.parameters),
            "criticality": self.criticality,
            "physical": self.physical,
            "software": self.software,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class Connection:
    connection_id: str
    source_component: str
    source_port: str
    target_component: str
    target_port: str
    interface_contract: str
    latency_s: float = 0.0
    efficiency: float = 1.0

    def validate(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.connection_id,
                self.source_component,
                self.source_port,
                self.target_component,
                self.target_port,
                self.interface_contract,
            )
        ):
            raise ValueError("connection identifiers and interface_contract are required")
        if self.source_component == self.target_component and self.source_port == self.target_port:
            raise ValueError("a port cannot connect to itself")
        if self.latency_s < 0:
            raise ValueError("connection latency cannot be negative")
        if not 0.0 < self.efficiency <= 1.0:
            raise ValueError("connection efficiency must lie in (0, 1]")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    metric: str
    comparator: str
    limit: float
    unit: str
    evidence_tier: str
    rationale: str

    def validate(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.requirement_id,
                self.metric,
                self.unit,
                self.evidence_tier,
                self.rationale,
            )
        ):
            raise ValueError("requirement fields cannot be empty")
        if self.comparator not in COMPARATORS:
            raise ValueError(f"unknown requirement comparator: {self.comparator}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class FaultMode:
    fault_id: str
    component_id: str
    mode: str
    local_effect: str
    system_effect: str
    severity: int
    occurrence: int
    detectability: int
    safe_state: str

    @property
    def risk_priority_number(self) -> int:
        return self.severity * self.occurrence * self.detectability

    def validate(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.fault_id,
                self.component_id,
                self.mode,
                self.local_effect,
                self.system_effect,
                self.safe_state,
            )
        ):
            raise ValueError("fault-mode fields cannot be empty")
        for name in ("severity", "occurrence", "detectability"):
            value = getattr(self, name)
            if not 1 <= value <= 10:
                raise ValueError(f"{name} must lie in [1, 10]")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["risk_priority_number"] = self.risk_priority_number
        return payload


@dataclass(frozen=True)
class SystemBlueprint:
    system_id: str
    name: str
    components: tuple[Component, ...]
    connections: tuple[Connection, ...]
    requirements: tuple[Requirement, ...]
    fault_modes: tuple[FaultMode, ...]
    lifecycle_stage: str = "computational-prototype"
    permanent_total_cap: None = None
    physics_certified: bool = False
    software_certified: bool = False
    regulatory_certified: bool = False

    @classmethod
    def build(
        cls,
        *,
        system_id: str,
        name: str,
        components: Sequence[Component],
        connections: Sequence[Connection],
        requirements: Sequence[Requirement] = (),
        fault_modes: Sequence[FaultMode] = (),
        lifecycle_stage: str = "computational-prototype",
    ) -> "SystemBlueprint":
        return cls(
            system_id=system_id,
            name=name,
            components=tuple(components),
            connections=tuple(connections),
            requirements=tuple(requirements),
            fault_modes=tuple(fault_modes),
            lifecycle_stage=lifecycle_stage,
        )

    def component_map(self) -> dict[str, Component]:
        return {item.component_id: item for item in self.components}

    def validate(self) -> None:
        if not self.system_id.strip() or not self.name.strip() or not self.lifecycle_stage.strip():
            raise ValueError("system_id, name and lifecycle_stage are required")
        if not self.components:
            raise ValueError("system blueprint requires at least one component")
        component_ids: set[str] = set()
        for component in self.components:
            component.validate()
            if component.component_id in component_ids:
                raise ValueError(f"duplicate component_id: {component.component_id}")
            component_ids.add(component.component_id)
        connection_ids: set[str] = set()
        component_map = self.component_map()
        for connection in self.connections:
            connection.validate()
            if connection.connection_id in connection_ids:
                raise ValueError(f"duplicate connection_id: {connection.connection_id}")
            connection_ids.add(connection.connection_id)
            if connection.source_component not in component_map or connection.target_component not in component_map:
                raise ValueError("connection references an unknown component")
            source = component_map[connection.source_component].port(connection.source_port)
            target = component_map[connection.target_component].port(connection.target_port)
            if source.domain != target.domain:
                raise ValueError("connected ports must share a domain; conversion belongs inside components")
            if source.direction not in ("output", "bidirectional"):
                raise ValueError("source port must be output or bidirectional")
            if target.direction not in ("input", "bidirectional"):
                raise ValueError("target port must be input or bidirectional")
        requirement_ids: set[str] = set()
        for requirement in self.requirements:
            requirement.validate()
            if requirement.requirement_id in requirement_ids:
                raise ValueError(f"duplicate requirement_id: {requirement.requirement_id}")
            requirement_ids.add(requirement.requirement_id)
        fault_ids: set[str] = set()
        for fault in self.fault_modes:
            fault.validate()
            if fault.fault_id in fault_ids:
                raise ValueError(f"duplicate fault_id: {fault.fault_id}")
            fault_ids.add(fault.fault_id)
            if fault.component_id not in component_map:
                raise ValueError("fault mode references an unknown component")
        if any((self.physics_certified, self.software_certified, self.regulatory_certified)):
            raise ValueError("R0.1 software cannot self-certify physical, software or regulatory compliance")

    @property
    def domains(self) -> tuple[str, ...]:
        return tuple(sorted({domain for component in self.components for domain in component.domains}))

    @property
    def evidence_hash(self) -> str:
        return _stable_hash(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        self.validate()
        payload = {
            "system_id": self.system_id,
            "name": self.name,
            "components": [item.to_dict() for item in self.components],
            "connections": [item.to_dict() for item in self.connections],
            "requirements": [item.to_dict() for item in self.requirements],
            "fault_modes": [item.to_dict() for item in self.fault_modes],
            "domains": list(self.domains),
            "lifecycle_stage": self.lifecycle_stage,
            "permanent_total_cap": self.permanent_total_cap,
            "physics_certified": self.physics_certified,
            "software_certified": self.software_certified,
            "regulatory_certified": self.regulatory_certified,
        }
        if include_hash:
            payload["evidence_hash"] = _stable_hash(payload)
        return payload


def demo_electromechanical_axis_blueprint() -> SystemBlueprint:
    power = Component.build(
        component_id="dc_bus",
        kind="dc-power-source",
        domains=("electrical_power",),
        ports=(Port("power_out", "electrical_power", "output", "V", "A", 40.0),),
        parameters={"nominal_voltage_v": 24.0, "current_limit_a": 20.0},
        criticality=4,
    )
    drive = Component.build(
        component_id="motor_drive",
        kind="pwm-motor-drive",
        domains=("electrical_power", "electronic_signal", "software"),
        ports=(
            Port("power_in", "electrical_power", "input", "V", "A", 25.0),
            Port("motor_power_out", "electrical_power", "output", "V", "A", 25.0),
            Port("command_in", "electronic_signal", "input", "V", "bit/s"),
            Port("telemetry_out", "electronic_signal", "output", "V", "bit/s"),
        ),
        parameters={"pwm_bits": 12, "switching_frequency_hz": 20_000},
        criticality=5,
        software=True,
    )
    motor = Component.build(
        component_id="dc_motor",
        kind="permanent-magnet-dc-motor",
        domains=("electrical_power", "mechanical_rotational", "thermal"),
        ports=(
            Port("power_in", "electrical_power", "input", "V", "A", 25.0),
            Port("shaft_out", "mechanical_rotational", "output", "N*m", "rad/s", 8.0),
            Port("heat_out", "thermal", "output", "K", "W", 120.0),
        ),
        parameters={"resistance_ohm": 0.8, "inductance_h": 0.006, "torque_constant": 0.11},
        criticality=5,
    )
    transmission = Component.build(
        component_id="ball_screw",
        kind="rotary-to-linear-transmission",
        domains=("mechanical_rotational", "mechanical_translational"),
        ports=(
            Port("shaft_in", "mechanical_rotational", "input", "N*m", "rad/s", 8.0),
            Port("linear_out", "mechanical_translational", "output", "N", "m/s", 900.0),
        ),
        parameters={"motor_rad_per_m": 180.0, "efficiency": 0.88},
        criticality=4,
    )
    load = Component.build(
        component_id="linear_load",
        kind="mass-spring-damper-load",
        domains=("mechanical_translational",),
        ports=(Port("force_in", "mechanical_translational", "input", "N", "m/s", 900.0),),
        parameters={"mass_kg": 4.0, "damping_n_s_m": 8.0, "stiffness_n_m": 20.0},
        criticality=3,
    )
    sensor = Component.build(
        component_id="encoder",
        kind="position-sensor",
        domains=("mechanical_translational", "electronic_signal"),
        ports=(
            Port("position_in", "mechanical_translational", "input", "N", "m/s"),
            Port("signal_out", "electronic_signal", "output", "V", "sample/s"),
        ),
        parameters={"resolution_bits": 16, "range_m": 0.5},
        criticality=4,
    )
    controller = Component.build(
        component_id="controller",
        kind="real-time-pid-controller",
        domains=("software", "data", "electronic_signal"),
        ports=(
            Port("measurement_in", "electronic_signal", "input", "V", "sample/s"),
            Port("command_out", "electronic_signal", "output", "V", "bit/s"),
            Port("setpoint_in", "data", "input", "m", "sample/s"),
        ),
        parameters={"sample_period_s": 0.001, "deadline_s": 0.0008},
        criticality=5,
        physical=False,
        software=True,
    )
    connections = (
        Connection("bus_to_drive", "dc_bus", "power_out", "motor_drive", "power_in", "24-V DC power"),
        Connection("drive_to_motor", "motor_drive", "motor_power_out", "dc_motor", "power_in", "PWM-equivalent DC power", efficiency=0.96),
        Connection("controller_to_drive", "controller", "command_out", "motor_drive", "command_in", "signed normalized torque command", latency_s=0.0001),
        Connection("motor_to_transmission", "dc_motor", "shaft_out", "ball_screw", "shaft_in", "torque-speed shaft interface", efficiency=0.88),
        Connection("transmission_to_load", "ball_screw", "linear_out", "linear_load", "force_in", "linear force-velocity interface", efficiency=0.98),
        Connection("sensor_to_controller", "encoder", "signal_out", "controller", "measurement_in", "quantized position measurement", latency_s=0.0002),
    )
    requirements = (
        Requirement("REQ-POS-001", "steady_state_position_error", "<=", 0.002, "m", "D3_COSIMULATED_SYSTEM", "positioning fixture target"),
        Requirement("REQ-CUR-001", "peak_current", "<=", 18.0, "A", "D3_COSIMULATED_SYSTEM", "protect the synthetic drive fixture"),
        Requirement("REQ-TMP-001", "motor_temperature", "<=", 353.15, "K", "D5_BENCH_EXPERIMENT", "requires measured thermal validation before hardware use"),
    )
    faults = (
        FaultMode("F-SENSOR-BIAS", "encoder", "constant bias", "position measurement shifted", "tracking error or runaway", 8, 3, 4, "disable drive and require homing"),
        FaultMode("F-DRIVE-STUCK", "motor_drive", "stuck PWM command", "voltage command cannot change", "uncontrolled motion", 10, 2, 3, "open independent power contactor"),
        FaultMode("F-MOTOR-OPEN", "dc_motor", "open circuit", "torque lost", "motion unavailable", 6, 3, 2, "controlled stop using passive brake"),
    )
    return SystemBlueprint.build(
        system_id="omega-cps-demo-axis",
        name="OAK-safe electromechanical axis fixture",
        components=(power, drive, motor, transmission, load, sensor, controller),
        connections=connections,
        requirements=requirements,
        fault_modes=faults,
    )
