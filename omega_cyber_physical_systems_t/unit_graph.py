from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from math import isclose, pi
from typing import Any, Mapping

from .models import Connection, Port, SystemBlueprint


DIMENSION_NAMES = ("mass", "length", "time", "current", "temperature", "amount", "luminous_intensity")
POWER_DIMENSION = (1, 2, -3, 0, 0, 0, 0)
DIMENSIONLESS = (0, 0, 0, 0, 0, 0, 0)


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _add_dimensions(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(a + b for a, b in zip(left, right))


def _dimension_payload(exponents: tuple[int, ...]) -> dict[str, int]:
    return {name: value for name, value in zip(DIMENSION_NAMES, exponents) if value}


@dataclass(frozen=True)
class UnitDefinition:
    symbol: str
    scale_to_si: float
    dimension: tuple[int, int, int, int, int, int, int]
    description: str

    def validate(self) -> None:
        if not self.symbol.strip() or not self.description.strip():
            raise ValueError("unit symbol and description are required")
        if self.scale_to_si <= 0:
            raise ValueError("unit scale_to_si must be positive")
        if len(self.dimension) != len(DIMENSION_NAMES):
            raise ValueError("unit dimension vector must use seven SI base dimensions")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "symbol": self.symbol,
            "scale_to_si": self.scale_to_si,
            "dimension": _dimension_payload(self.dimension),
            "description": self.description,
        }


@dataclass(frozen=True)
class UnitRegistry:
    definitions: Mapping[str, UnitDefinition]

    def validate(self) -> None:
        if not self.definitions:
            raise ValueError("unit registry cannot be empty")
        for symbol, definition in self.definitions.items():
            definition.validate()
            if symbol != definition.symbol:
                raise ValueError("unit registry key must match definition symbol")

    def get(self, symbol: str) -> UnitDefinition:
        self.validate()
        try:
            return self.definitions[symbol]
        except KeyError as exc:
            raise KeyError(f"unknown unit symbol: {symbol}") from exc

    def compatible(self, left: str, right: str) -> bool:
        return self.get(left).dimension == self.get(right).dimension

    def convert(self, value: float, source: str, target: str) -> float:
        source_unit = self.get(source)
        target_unit = self.get(target)
        if source_unit.dimension != target_unit.dimension:
            raise ValueError(f"cannot convert incompatible units {source} and {target}")
        return value * source_unit.scale_to_si / target_unit.scale_to_si

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {symbol: definition.to_dict() for symbol, definition in sorted(self.definitions.items())}


@dataclass(frozen=True)
class DomainPortSemantics:
    domain: str
    effort_dimension: tuple[int, int, int, int, int, int, int] | None
    flow_dimension: tuple[int, int, int, int, int, int, int] | None
    mode: str
    note: str

    def validate(self) -> None:
        if self.mode not in ("power_conjugate", "direct_power_flow", "nonenergetic"):
            raise ValueError("unknown domain-port semantic mode")
        if not self.domain.strip() or not self.note.strip():
            raise ValueError("domain and semantic note are required")


@dataclass(frozen=True)
class PortUnitAssessment:
    component_id: str
    port_id: str
    domain: str
    effort_unit: str
    flow_unit: str
    effort_known: bool
    flow_known: bool
    effort_dimension: dict[str, int]
    flow_dimension: dict[str, int]
    product_dimension: dict[str, int]
    semantic_mode: str
    power_conjugate: bool
    direct_power_flow: bool
    findings: tuple[str, ...]
    severity: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = list(self.findings)
        return payload


@dataclass(frozen=True)
class ConnectionUnitAssessment:
    connection_id: str
    source: str
    target: str
    domain: str
    effort_dimension_compatible: bool
    flow_dimension_compatible: bool
    effort_scale_ratio: float | None
    flow_scale_ratio: float | None
    causal_direction_valid: bool
    findings: tuple[str, ...]
    severity: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = list(self.findings)
        return payload


@dataclass(frozen=True)
class UnitGraphReport:
    system_id: str
    port_assessments: tuple[PortUnitAssessment, ...]
    connection_assessments: tuple[ConnectionUnitAssessment, ...]
    error_count: int
    warning_count: int
    informational_count: int
    known_unit_count: int
    unknown_unit_count: int
    power_conjugate_port_count: int
    direct_power_port_count: int
    nonenergetic_port_count: int
    dimensionally_valid: bool
    causal_connections_valid: bool
    evidence_hash: str
    physics_certified: bool = False
    standards_compliance_claim: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_id": self.system_id,
            "port_assessments": [item.to_dict() for item in self.port_assessments],
            "connection_assessments": [item.to_dict() for item in self.connection_assessments],
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "informational_count": self.informational_count,
            "known_unit_count": self.known_unit_count,
            "unknown_unit_count": self.unknown_unit_count,
            "power_conjugate_port_count": self.power_conjugate_port_count,
            "direct_power_port_count": self.direct_power_port_count,
            "nonenergetic_port_count": self.nonenergetic_port_count,
            "dimensionally_valid": self.dimensionally_valid,
            "causal_connections_valid": self.causal_connections_valid,
            "evidence_hash": self.evidence_hash,
            "physics_certified": self.physics_certified,
            "standards_compliance_claim": self.standards_compliance_claim,
            "limitations": [
                "registry covers declared R0.2 units, not every SI-derived or industry-specific unit",
                "dimension compatibility does not prove calibration, sign convention or physical correctness",
                "software, data and signal ports are classified as nonenergetic information channels",
                "thermal ports using heat-rate W instead of entropy-rate W/K are declared direct-power-flow semantics",
            ],
        }


def default_unit_registry() -> UnitRegistry:
    M = (1, 0, 0, 0, 0, 0, 0)
    L = (0, 1, 0, 0, 0, 0, 0)
    T = (0, 0, 1, 0, 0, 0, 0)
    I = (0, 0, 0, 1, 0, 0, 0)
    TH = (0, 0, 0, 0, 1, 0, 0)
    definitions = {
        "1": UnitDefinition("1", 1.0, DIMENSIONLESS, "dimensionless"),
        "rad": UnitDefinition("rad", 1.0, DIMENSIONLESS, "radian treated as dimensionless"),
        "bit": UnitDefinition("bit", 1.0, DIMENSIONLESS, "information token; not an SI physical dimension"),
        "sample": UnitDefinition("sample", 1.0, DIMENSIONLESS, "sample token; not an SI physical dimension"),
        "s": UnitDefinition("s", 1.0, T, "second"),
        "Hz": UnitDefinition("Hz", 1.0, (0, 0, -1, 0, 0, 0, 0), "hertz"),
        "sample/s": UnitDefinition("sample/s", 1.0, (0, 0, -1, 0, 0, 0, 0), "sample rate"),
        "bit/s": UnitDefinition("bit/s", 1.0, (0, 0, -1, 0, 0, 0, 0), "bit rate"),
        "m": UnitDefinition("m", 1.0, L, "metre"),
        "mm": UnitDefinition("mm", 1e-3, L, "millimetre"),
        "kg": UnitDefinition("kg", 1.0, M, "kilogram"),
        "A": UnitDefinition("A", 1.0, I, "ampere"),
        "K": UnitDefinition("K", 1.0, TH, "kelvin"),
        "N": UnitDefinition("N", 1.0, (1, 1, -2, 0, 0, 0, 0), "newton"),
        "Pa": UnitDefinition("Pa", 1.0, (1, -1, -2, 0, 0, 0, 0), "pascal"),
        "J": UnitDefinition("J", 1.0, (1, 2, -2, 0, 0, 0, 0), "joule"),
        "W": UnitDefinition("W", 1.0, POWER_DIMENSION, "watt"),
        "V": UnitDefinition("V", 1.0, (1, 2, -3, -1, 0, 0, 0), "volt"),
        "C": UnitDefinition("C", 1.0, (0, 0, 1, 1, 0, 0, 0), "coulomb"),
        "ohm": UnitDefinition("ohm", 1.0, (1, 2, -3, -2, 0, 0, 0), "ohm"),
        "H": UnitDefinition("H", 1.0, (1, 2, -2, -2, 0, 0, 0), "henry"),
        "N*m": UnitDefinition("N*m", 1.0, (1, 2, -2, 0, 0, 0, 0), "newton metre"),
        "rad/s": UnitDefinition("rad/s", 1.0, (0, 0, -1, 0, 0, 0, 0), "angular velocity"),
        "rpm": UnitDefinition("rpm", 2.0 * pi / 60.0, (0, 0, -1, 0, 0, 0, 0), "revolutions per minute converted to rad/s"),
        "m/s": UnitDefinition("m/s", 1.0, (0, 1, -1, 0, 0, 0, 0), "linear velocity"),
        "m^3/s": UnitDefinition("m^3/s", 1.0, (0, 3, -1, 0, 0, 0, 0), "volumetric flow"),
        "L/min": UnitDefinition("L/min", 1e-3 / 60.0, (0, 3, -1, 0, 0, 0, 0), "litres per minute"),
        "W/K": UnitDefinition("W/K", 1.0, (1, 2, -3, 0, -1, 0, 0), "entropy-flow-equivalent thermal conjugate"),
    }
    registry = UnitRegistry(definitions)
    registry.validate()
    return registry


def default_domain_semantics() -> dict[str, DomainPortSemantics]:
    registry = default_unit_registry()
    return {
        "mechanical_translational": DomainPortSemantics(
            "mechanical_translational", registry.get("N").dimension, registry.get("m/s").dimension,
            "power_conjugate", "force multiplied by linear velocity yields power",
        ),
        "mechanical_rotational": DomainPortSemantics(
            "mechanical_rotational", registry.get("N*m").dimension, registry.get("rad/s").dimension,
            "power_conjugate", "torque multiplied by angular velocity yields power",
        ),
        "electrical_power": DomainPortSemantics(
            "electrical_power", registry.get("V").dimension, registry.get("A").dimension,
            "power_conjugate", "voltage multiplied by current yields power",
        ),
        "fluid": DomainPortSemantics(
            "fluid", registry.get("Pa").dimension, registry.get("m^3/s").dimension,
            "power_conjugate", "pressure multiplied by volumetric flow yields hydraulic power",
        ),
        "thermal": DomainPortSemantics(
            "thermal", registry.get("K").dimension, registry.get("W/K").dimension,
            "direct_power_flow", "temperature and entropy flow are conjugate; W is accepted only as declared heat-rate flow",
        ),
        "electronic_signal": DomainPortSemantics(
            "electronic_signal", None, None, "nonenergetic", "signal amplitude and data rate are not treated as a power bond",
        ),
        "software": DomainPortSemantics(
            "software", None, None, "nonenergetic", "software ports carry causality and information, not physical power",
        ),
        "data": DomainPortSemantics(
            "data", None, None, "nonenergetic", "data ports carry semantic values, not physical power",
        ),
    }


def _assess_port(component_id: str, port: Port, registry: UnitRegistry) -> PortUnitAssessment:
    semantics = default_domain_semantics()[port.domain]
    findings: list[str] = []
    severity = "info"
    effort = registry.definitions.get(port.effort_unit)
    flow = registry.definitions.get(port.flow_unit)
    if effort is None:
        findings.append("unknown_effort_unit")
        severity = "error"
    if flow is None:
        findings.append("unknown_flow_unit")
        severity = "error"
    effort_dim = DIMENSIONLESS if effort is None else effort.dimension
    flow_dim = DIMENSIONLESS if flow is None else flow.dimension
    product_dim = _add_dimensions(effort_dim, flow_dim)
    power_conjugate = False
    direct_power_flow = False
    if effort is not None and flow is not None:
        if semantics.mode == "power_conjugate":
            if effort.dimension != semantics.effort_dimension:
                findings.append("effort_dimension_mismatch")
                severity = "error"
            if flow.dimension != semantics.flow_dimension:
                findings.append("flow_dimension_mismatch")
                severity = "error"
            power_conjugate = product_dim == POWER_DIMENSION and not any("mismatch" in item for item in findings)
            if not power_conjugate and severity != "error":
                findings.append("effort_flow_product_is_not_power")
                severity = "error"
        elif semantics.mode == "direct_power_flow":
            if effort.dimension != semantics.effort_dimension:
                findings.append("thermal_effort_dimension_mismatch")
                severity = "error"
            if flow.symbol == "W":
                direct_power_flow = True
                findings.append("thermal_heat_rate_used_instead_of_entropy_flow")
                if severity != "error":
                    severity = "warning"
            elif flow.dimension == semantics.flow_dimension:
                power_conjugate = product_dim == POWER_DIMENSION
            else:
                findings.append("thermal_flow_dimension_mismatch")
                severity = "error"
        else:
            findings.append("nonenergetic_information_channel")
            severity = "info"
    return PortUnitAssessment(
        component_id=component_id,
        port_id=port.port_id,
        domain=port.domain,
        effort_unit=port.effort_unit,
        flow_unit=port.flow_unit,
        effort_known=effort is not None,
        flow_known=flow is not None,
        effort_dimension=_dimension_payload(effort_dim),
        flow_dimension=_dimension_payload(flow_dim),
        product_dimension=_dimension_payload(product_dim),
        semantic_mode=semantics.mode,
        power_conjugate=power_conjugate,
        direct_power_flow=direct_power_flow,
        findings=tuple(findings),
        severity=severity,
    )


def _connection_assessment(
    blueprint: SystemBlueprint,
    connection: Connection,
    registry: UnitRegistry,
) -> ConnectionUnitAssessment:
    components = blueprint.component_map()
    source = components[connection.source_component].port(connection.source_port)
    target = components[connection.target_component].port(connection.target_port)
    findings: list[str] = []
    severity = "info"
    effort_compatible = False
    flow_compatible = False
    effort_ratio: float | None = None
    flow_ratio: float | None = None
    source_effort = registry.definitions.get(source.effort_unit)
    target_effort = registry.definitions.get(target.effort_unit)
    source_flow = registry.definitions.get(source.flow_unit)
    target_flow = registry.definitions.get(target.flow_unit)
    if source_effort is None or target_effort is None:
        findings.append("connection_unknown_effort_unit")
        severity = "error"
    else:
        effort_compatible = source_effort.dimension == target_effort.dimension
        if not effort_compatible:
            findings.append("connection_effort_dimension_mismatch")
            severity = "error"
        else:
            effort_ratio = source_effort.scale_to_si / target_effort.scale_to_si
            if not isclose(effort_ratio, 1.0, rel_tol=1e-12, abs_tol=1e-12):
                findings.append("effort_scale_conversion_required")
                if severity != "error":
                    severity = "warning"
    if source_flow is None or target_flow is None:
        findings.append("connection_unknown_flow_unit")
        severity = "error"
    else:
        flow_compatible = source_flow.dimension == target_flow.dimension
        if not flow_compatible:
            findings.append("connection_flow_dimension_mismatch")
            severity = "error"
        else:
            flow_ratio = source_flow.scale_to_si / target_flow.scale_to_si
            if not isclose(flow_ratio, 1.0, rel_tol=1e-12, abs_tol=1e-12):
                findings.append("flow_scale_conversion_required")
                if severity != "error":
                    severity = "warning"
    causal = source.direction in ("output", "bidirectional") and target.direction in ("input", "bidirectional")
    if not causal:
        findings.append("invalid_connection_causality")
        severity = "error"
    if not findings:
        findings.append("dimension_and_causality_contract_satisfied")
    return ConnectionUnitAssessment(
        connection_id=connection.connection_id,
        source=f"{connection.source_component}.{connection.source_port}",
        target=f"{connection.target_component}.{connection.target_port}",
        domain=source.domain,
        effort_dimension_compatible=effort_compatible,
        flow_dimension_compatible=flow_compatible,
        effort_scale_ratio=effort_ratio,
        flow_scale_ratio=flow_ratio,
        causal_direction_valid=causal,
        findings=tuple(findings),
        severity=severity,
    )


def audit_blueprint_units(
    blueprint: SystemBlueprint,
    *,
    registry: UnitRegistry | None = None,
) -> UnitGraphReport:
    blueprint.validate()
    unit_registry = registry or default_unit_registry()
    unit_registry.validate()
    ports = tuple(
        _assess_port(component.component_id, port, unit_registry)
        for component in blueprint.components
        for port in component.ports
    )
    connections = tuple(
        _connection_assessment(blueprint, connection, unit_registry)
        for connection in blueprint.connections
    )
    all_severities = [item.severity for item in ports] + [item.severity for item in connections]
    error_count = all_severities.count("error")
    warning_count = all_severities.count("warning")
    informational_count = all_severities.count("info")
    known_units = sum(int(item.effort_known) + int(item.flow_known) for item in ports)
    unknown_units = 2 * len(ports) - known_units
    stable = {
        "system_id": blueprint.system_id,
        "ports": [item.to_dict() for item in ports],
        "connections": [item.to_dict() for item in connections],
        "registry_symbols": sorted(unit_registry.definitions),
    }
    return UnitGraphReport(
        system_id=blueprint.system_id,
        port_assessments=ports,
        connection_assessments=connections,
        error_count=error_count,
        warning_count=warning_count,
        informational_count=informational_count,
        known_unit_count=known_units,
        unknown_unit_count=unknown_units,
        power_conjugate_port_count=sum(item.power_conjugate for item in ports),
        direct_power_port_count=sum(item.direct_power_flow for item in ports),
        nonenergetic_port_count=sum(item.semantic_mode == "nonenergetic" for item in ports),
        dimensionally_valid=error_count == 0,
        causal_connections_valid=all(item.causal_direction_valid for item in connections),
        evidence_hash=_stable_hash(stable),
    )
