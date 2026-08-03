from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .compiler import compile_prototype, demo_integrated_robot_intent
from .cosim import demo_fault_scenario, demo_nominal_scenario, run_closed_loop_axis
from .dynamics import dc_motor_model, mass_spring_damper_model, simulate_state_space
from .evidence import (
    SystemEvidenceReceipt,
    assess_evidence_ledger,
    assess_receipt,
    computational_demo_receipts,
)
from .fault_analysis import analyze_fault_propagation
from .inventory import InventoryConfig, discover_repository_systems
from .models import demo_electromechanical_axis_blueprint


@dataclass(frozen=True)
class CPSOAKGate:
    name: str
    passed: bool
    observation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CPSOAKReport:
    passed: bool
    status: str
    gates: tuple[CPSOAKGate, ...]
    model_class: str = "whole-system-cyberphysical-computational-research"
    physics_certified: bool = False
    software_certified: bool = False
    safety_certified: bool = False
    regulatory_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "gates": [item.to_dict() for item in self.gates],
            "model_class": self.model_class,
            "physics_certified": self.physics_certified,
            "software_certified": self.software_certified,
            "safety_certified": self.safety_certified,
            "regulatory_certified": self.regulatory_certified,
            "certification_notice": (
                "This status certifies deterministic software invariants for declared synthetic fixtures only. "
                "It does not certify hardware, physics, functional safety, EMC, machinery, vehicles, medical devices, "
                "industrial installations or regulatory compliance."
            ),
        }


def run_cps_benchmarks(*, repository_root: str | Path | None = None) -> CPSOAKReport:
    blueprint = demo_electromechanical_axis_blueprint()
    blueprint.validate()

    mechanical = mass_spring_damper_model(mass_kg=2.0, damping_n_s_m=1.5, stiffness_n_m=8.0)
    mechanical_trace = simulate_state_space(
        mechanical,
        initial_state=(0.0, 0.0),
        input_sequence=((3.0,),) * 200,
        dt_s=0.002,
    )
    motor = dc_motor_model(
        resistance_ohm=1.2,
        inductance_h=0.01,
        torque_constant_nm_a=0.08,
        back_emf_v_s_rad=0.08,
        inertia_kg_m2=0.004,
        viscous_friction_nm_s_rad=0.002,
    )
    motor_trace = simulate_state_space(
        motor,
        initial_state=(0.0, 0.0),
        input_sequence=((12.0, 0.02),) * 300,
        dt_s=0.001,
    )

    nominal = run_closed_loop_axis(demo_nominal_scenario())
    faulted = run_closed_loop_axis(demo_fault_scenario())
    compiler_report = compile_prototype(demo_integrated_robot_intent())
    fault_report = analyze_fault_propagation(blueprint)
    test_hash = hashlib.sha256(b"omega-cps-r0.1-focused-tests").hexdigest()
    receipts = computational_demo_receipts(
        blueprint_hash=blueprint.evidence_hash,
        simulation_hash=nominal.evidence_hash,
        test_definition_hash=test_hash,
        test_count=1,
    )
    evidence = assess_evidence_ledger(receipts)
    phantom_hil = SystemEvidenceReceipt(
        receipt_id="phantom-hil",
        tier="D4_HIL_SIL",
        artifact_sha256="0" * 64,
        provenance="synthetic negative control",
        method="unsupported HIL claim",
        limitations=("no hardware, firmware, timing log or raw data",),
        metadata={"hardware_ids": [], "firmware_hash": "", "raw_logs_retained": False},
        origin="synthetic_fixture",
    )
    phantom_assessment = assess_receipt(phantom_hil)
    root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[1]
    inventory = discover_repository_systems(
        root,
        config=InventoryConfig(max_files_per_system=64, max_bytes_per_file=32_000),
    )

    gates = (
        CPSOAKGate(
            "multi-domain-blueprint",
            len(blueprint.components) == 7
            and len(blueprint.connections) == 6
            and {
                "mechanical_translational",
                "mechanical_rotational",
                "electrical_power",
                "electronic_signal",
                "thermal",
                "software",
                "data",
            }.issubset(set(blueprint.domains)),
            f"components={len(blueprint.components)}, connections={len(blueprint.connections)}, domains={blueprint.domains}",
        ),
        CPSOAKGate(
            "blueprint-evidence-hash",
            len(blueprint.evidence_hash) == 64 and blueprint.to_dict()["evidence_hash"] == blueprint.evidence_hash,
            f"hash={blueprint.evidence_hash[:16]}...",
        ),
        CPSOAKGate(
            "mechanical-dynamics-finite",
            mechanical_trace.finite
            and mechanical_trace.samples[-1].outputs[0] > 0
            and len(mechanical_trace.evidence_hash) == 64,
            f"position={mechanical_trace.samples[-1].outputs[0]:.6g}",
        ),
        CPSOAKGate(
            "electromechanical-dynamics-finite",
            motor_trace.finite
            and motor_trace.samples[-1].outputs[0] > 0
            and motor_trace.samples[-1].outputs[1] > 0,
            (
                f"current={motor_trace.samples[-1].outputs[0]:.6g}, "
                f"speed={motor_trace.samples[-1].outputs[1]:.6g}"
            ),
        ),
        CPSOAKGate(
            "whole-loop-cosimulation-finite",
            nominal.finite
            and len(nominal.samples) > 1_000
            and abs(nominal.final_error_m) < abs(nominal.scenario.setpoint_m)
            and nominal.absolute_electrical_energy_j >= abs(nominal.net_electrical_energy_j),
            (
                f"samples={len(nominal.samples)}, final_error={nominal.final_error_m:.6g}, "
                f"energy={nominal.absolute_electrical_energy_j:.6g}"
            ),
        ),
        CPSOAKGate(
            "software-timing-fault-observed",
            faulted.deadline_miss_count > 0
            and any(item.deadline_missed for item in faulted.samples)
            and len(faulted.evidence_hash) == 64,
            f"deadline_misses={faulted.deadline_miss_count}, shutdowns={faulted.shutdown_reasons}",
        ),
        CPSOAKGate(
            "prototype-compiler-cross-domain",
            compiler_report.best is not None
            and compiler_report.best.architecture.architecture_id == "mobile-robot-platform"
            and compiler_report.eligible_count >= 2
            and compiler_report.permanent_total_cap is None,
            (
                f"best={None if compiler_report.best is None else compiler_report.best.architecture.architecture_id}, "
                f"eligible={compiler_report.eligible_count}"
            ),
        ),
        CPSOAKGate(
            "fault-propagation-retains-negative-memory",
            len(fault_report.records) == len(blueprint.fault_modes)
            and fault_report.highest_rpn > 0
            and fault_report.probability_claim is False
            and fault_report.safety_certified is False,
            (
                f"records={len(fault_report.records)}, highest_rpn={fault_report.highest_rpn}, "
                f"single_points={fault_report.single_point_risk_count}"
            ),
        ),
        CPSOAKGate(
            "evidence-contiguous-through-cosimulation",
            evidence.contiguous_tier == "D3_COSIMULATED_SYSTEM"
            and evidence.highest_supported_tier == "D3_COSIMULATED_SYSTEM"
            and not evidence.missing_lower_tiers,
            f"contiguous={evidence.contiguous_tier}, highest={evidence.highest_supported_tier}",
        ),
        CPSOAKGate(
            "phantom-hil-blocked",
            not phantom_assessment.accepted
            and "hil_sil_raw_logs_not_retained" in phantom_assessment.blockers
            and "missing_metadata:timing_log_hash" in phantom_assessment.blockers,
            f"blockers={phantom_assessment.blockers}",
        ),
        CPSOAKGate(
            "repository-wide-inventory",
            inventory.cyberphysical_candidate_count >= 2
            and inventory.integrated_candidate_count >= 1
            and inventory.permanent_total_cap is None
            and inventory.exhaustive_claim is False,
            (
                f"records={len(inventory.records)}, cps={inventory.cyberphysical_candidate_count}, "
                f"integrated={inventory.integrated_candidate_count}"
            ),
        ),
        CPSOAKGate(
            "no-self-certification",
            not any(
                (
                    blueprint.physics_certified,
                    blueprint.software_certified,
                    blueprint.regulatory_certified,
                    nominal.physics_certified,
                    nominal.software_certified,
                    nominal.hardware_validated,
                    evidence.physics_certified,
                    evidence.software_certified,
                    evidence.regulatory_certified,
                )
            ),
            "all physical, software, safety and regulatory certification flags remain false",
        ),
    )
    passed = all(item.passed for item in gates)
    return CPSOAKReport(
        passed=passed,
        status=(
            "CERTIFIED_COMPUTATIONAL_CYBER_PHYSICAL_SYSTEMS_R0_1"
            if passed
            else "FAILED_COMPUTATIONAL_CYBER_PHYSICAL_SYSTEMS_R0_1"
        ),
        gates=gates,
    )
