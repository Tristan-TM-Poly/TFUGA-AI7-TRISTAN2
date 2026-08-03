from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from .cosim import demo_fault_scenario, demo_nominal_scenario, run_closed_loop_axis
from .energy_graph import audit_closed_loop_energy
from .models import demo_electromechanical_axis_blueprint
from .unit_graph import audit_blueprint_units, default_unit_registry


@dataclass(frozen=True)
class CPSR02OAKGate:
    gate_id: str
    passed: bool
    detail: str
    measured: float | int | str | bool | None = None
    threshold: float | int | str | bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CPSR02OAKReport:
    status: str
    passed: bool
    gates: tuple[CPSR02OAKGate, ...]
    unit_graph_hash: str
    nominal_energy_hash: str
    faulted_energy_hash: str
    adversarial_energy_hash: str
    physics_certified: bool = False
    energy_conservation_proven: bool = False
    passivity_proven: bool = False
    standards_compliance_claim: bool = False
    hardware_validated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "gates": [item.to_dict() for item in self.gates],
            "unit_graph_hash": self.unit_graph_hash,
            "nominal_energy_hash": self.nominal_energy_hash,
            "faulted_energy_hash": self.faulted_energy_hash,
            "adversarial_energy_hash": self.adversarial_energy_hash,
            "physics_certified": self.physics_certified,
            "energy_conservation_proven": self.energy_conservation_proven,
            "passivity_proven": self.passivity_proven,
            "standards_compliance_claim": self.standards_compliance_claim,
            "hardware_validated": self.hardware_validated,
            "limitations": [
                "R0.2 certifies deterministic dimensional and energy-accounting invariants only",
                "a small numerical residual is not experimental proof of conservation or model accuracy",
                "passivity is classified inside the declared lumped model and is not formally proven",
                "thermal and conversion parameters remain synthetic fixtures without calibration",
            ],
        }


def run_cps_r02_benchmarks() -> CPSR02OAKReport:
    blueprint = demo_electromechanical_axis_blueprint()
    registry = default_unit_registry()
    units = audit_blueprint_units(blueprint, registry=registry)
    nominal_simulation = run_closed_loop_axis(demo_nominal_scenario())
    faulted_simulation = run_closed_loop_axis(demo_fault_scenario())
    nominal = audit_closed_loop_energy(nominal_simulation)
    faulted = audit_closed_loop_energy(faulted_simulation)
    adversarial = audit_closed_loop_energy(nominal_simulation, untracked_output_energy_j=5.0)

    rpm_conversion = registry.convert(60.0, "rpm", "rad/s")
    hydraulic_power_dimension = (
        tuple(registry.get("Pa").dimension[index] + registry.get("m^3/s").dimension[index] for index in range(7))
        == registry.get("W").dimension
    )
    hash_repeat = audit_closed_loop_energy(nominal_simulation).evidence_hash
    gates = (
        CPSR02OAKGate(
            "R02-UNIT-REGISTRY",
            len(registry.definitions) >= 20 and abs(rpm_conversion - 2.0 * 3.141592653589793) < 1e-12,
            "unit registry validates derived dimensions and scale conversions",
            len(registry.definitions),
            20,
        ),
        CPSR02OAKGate(
            "R02-UNIT-POWER",
            hydraulic_power_dimension,
            "pressure × volumetric flow resolves to watt dimensions",
            hydraulic_power_dimension,
            True,
        ),
        CPSR02OAKGate(
            "R02-BLUEPRINT-DIMENSIONS",
            units.dimensionally_valid and units.unknown_unit_count == 0,
            "all declared blueprint units are known and no physical port has a dimensional error",
            units.error_count,
            0,
        ),
        CPSR02OAKGate(
            "R02-CAUSAL-CONNECTIONS",
            units.causal_connections_valid and all(
                item.effort_dimension_compatible and item.flow_dimension_compatible
                for item in units.connection_assessments
            ),
            "every connected interface is dimensionally compatible and output-to-input causal",
            len(units.connection_assessments),
            len(blueprint.connections),
        ),
        CPSR02OAKGate(
            "R02-THERMAL-SEMANTICS",
            units.warning_count >= 1 and units.direct_power_port_count >= 1,
            "nonconjugate K/W thermal fixture is retained as an explicit direct heat-rate warning",
            units.warning_count,
            1,
        ),
        CPSR02OAKGate(
            "R02-NOMINAL-BALANCE",
            nominal.finite and nominal.balance_passed,
            "electrical, thermal, mechanical and global nominal balances close within declared tolerance",
            nominal.global_normalized_residual,
            0.02,
        ),
        CPSR02OAKGate(
            "R02-FAULTED-ACCOUNTING",
            faulted.finite and faulted.sample_count == len(faulted_simulation.samples),
            "faulted execution remains auditable without being promoted to physical validation",
            faulted.sample_count,
            len(faulted_simulation.samples),
        ),
        CPSR02OAKGate(
            "R02-ADVERSARIAL-RESIDUAL",
            not adversarial.balance("global").passed and abs(adversarial.global_residual_j) > adversarial.residual_tolerance_j,
            "an injected untracked five-joule output is rejected by the global balance",
            abs(adversarial.global_residual_j),
            adversarial.residual_tolerance_j,
        ),
        CPSR02OAKGate(
            "R02-DETERMINISM",
            nominal.evidence_hash == hash_repeat,
            "same source report and policy produce the same EnergyGraph SHA-256 receipt",
            nominal.evidence_hash,
            hash_repeat,
        ),
        CPSR02OAKGate(
            "R02-NONCERTIFICATION",
            not any(
                (
                    units.physics_certified,
                    units.standards_compliance_claim,
                    nominal.physics_certified,
                    nominal.hardware_validated,
                    nominal.energy_conservation_proven,
                    nominal.passivity.passivity_proven,
                )
            ),
            "software does not self-certify physics, passivity, standards, hardware or conservation laws",
            False,
            False,
        ),
    )
    passed = all(item.passed for item in gates)
    return CPSR02OAKReport(
        status=(
            "CERTIFIED_COMPUTATIONAL_UNIT_ENERGY_GRAPH_R0_2"
            if passed
            else "BLOCKED_COMPUTATIONAL_UNIT_ENERGY_GRAPH_R0_2"
        ),
        passed=passed,
        gates=gates,
        unit_graph_hash=units.evidence_hash,
        nominal_energy_hash=nominal.evidence_hash,
        faulted_energy_hash=faulted.evidence_hash,
        adversarial_energy_hash=adversarial.evidence_hash,
    )
