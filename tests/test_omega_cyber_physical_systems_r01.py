from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from omega_cyber_physical_systems_t.compiler import (
    PrototypeIntent,
    compile_prototype,
    default_prototype_architectures,
    demo_integrated_robot_intent,
)
from omega_cyber_physical_systems_t.control import PIDConfig, PIDState, pid_step
from omega_cyber_physical_systems_t.cosim import (
    ClosedLoopScenario,
    FaultEvent,
    SafetyLimits,
    demo_fault_scenario,
    demo_nominal_scenario,
    run_closed_loop_axis,
)
from omega_cyber_physical_systems_t.dynamics import (
    StateSpaceModel,
    dc_motor_model,
    mass_spring_damper_model,
    simulate_state_space,
)
from omega_cyber_physical_systems_t.evidence import (
    SystemEvidenceReceipt,
    assess_evidence_ledger,
    assess_receipt,
    computational_demo_receipts,
)
from omega_cyber_physical_systems_t.fault_analysis import analyze_fault_propagation
from omega_cyber_physical_systems_t.inventory import (
    InventoryConfig,
    discover_repository_systems,
    summarize_inventory,
)
from omega_cyber_physical_systems_t.models import (
    Component,
    Connection,
    Port,
    SystemBlueprint,
    demo_electromechanical_axis_blueprint,
)
from omega_cyber_physical_systems_t.oak import run_cps_benchmarks


def test_port_rejects_unknown_domain():
    with pytest.raises(ValueError, match="unknown port domain"):
        Port("bad", "magic", "input", "x", "y").validate()


def test_software_component_requires_software_domain():
    component = Component.build(
        component_id="controller",
        kind="controller",
        domains=("data",),
        ports=(Port("in", "data", "input", "bit", "bit/s"),),
        software=True,
    )
    with pytest.raises(ValueError, match="software components"):
        component.validate()


def test_demo_blueprint_is_multidomain_and_hashed():
    blueprint = demo_electromechanical_axis_blueprint()
    blueprint.validate()
    assert len(blueprint.components) == 7
    assert len(blueprint.connections) == 6
    assert "mechanical_translational" in blueprint.domains
    assert "mechanical_rotational" in blueprint.domains
    assert "electrical_power" in blueprint.domains
    assert "electronic_signal" in blueprint.domains
    assert "software" in blueprint.domains
    assert len(blueprint.evidence_hash) == 64
    assert blueprint.to_dict()["evidence_hash"] == blueprint.evidence_hash
    assert blueprint.physics_certified is False
    assert blueprint.regulatory_certified is False


def test_blueprint_rejects_cross_domain_connection():
    left = Component.build(
        component_id="left",
        kind="source",
        domains=("electrical_power",),
        ports=(Port("out", "electrical_power", "output", "V", "A"),),
    )
    right = Component.build(
        component_id="right",
        kind="load",
        domains=("mechanical_translational",),
        ports=(Port("in", "mechanical_translational", "input", "N", "m/s"),),
    )
    blueprint = SystemBlueprint.build(
        system_id="invalid",
        name="invalid",
        components=(left, right),
        connections=(Connection("bad", "left", "out", "right", "in", "invalid direct conversion"),),
    )
    with pytest.raises(ValueError, match="connected ports must share a domain"):
        blueprint.validate()


def test_blueprint_rejects_self_certification():
    blueprint = replace(demo_electromechanical_axis_blueprint(), physics_certified=True)
    with pytest.raises(ValueError, match="cannot self-certify"):
        blueprint.validate()


def test_fault_modes_expose_rpn():
    blueprint = demo_electromechanical_axis_blueprint()
    assert all(item.risk_priority_number > 0 for item in blueprint.fault_modes)
    assert blueprint.fault_modes[1].risk_priority_number == 60


def test_mass_spring_damper_simulation_is_finite():
    model = mass_spring_damper_model(mass_kg=2.0, damping_n_s_m=1.5, stiffness_n_m=8.0)
    trace = simulate_state_space(
        model,
        initial_state=(0.0, 0.0),
        input_sequence=((3.0,),) * 200,
        dt_s=0.002,
    )
    assert trace.finite
    assert trace.samples[-1].outputs[0] > 0
    assert len(trace.evidence_hash) == 64
    assert trace.physics_certified is False


def test_dc_motor_simulation_is_finite_and_rotates():
    model = dc_motor_model(
        resistance_ohm=1.2,
        inductance_h=0.01,
        torque_constant_nm_a=0.08,
        back_emf_v_s_rad=0.08,
        inertia_kg_m2=0.004,
        viscous_friction_nm_s_rad=0.002,
    )
    trace = simulate_state_space(
        model,
        initial_state=(0.0, 0.0),
        input_sequence=((12.0, 0.02),) * 300,
        dt_s=0.001,
    )
    assert trace.finite
    assert trace.samples[-1].outputs[0] > 0
    assert trace.samples[-1].outputs[1] > 0


def test_state_space_rejects_bad_dimensions():
    model = StateSpaceModel(
        model_id="bad",
        a=((0.0,),),
        b=((1.0,),),
        c=((1.0, 0.0),),
        d=((0.0,),),
        state_names=("x",),
        input_names=("u",),
        output_names=("y",),
        assumptions=("bad fixture",),
    )
    with pytest.raises(ValueError, match="C dimensions"):
        model.validate()


def test_pid_saturates_and_bounds_integral():
    config = PIDConfig(
        kp=100.0,
        ki=50.0,
        kd=0.0,
        output_min=-10.0,
        output_max=10.0,
        integral_min=-0.2,
        integral_max=0.2,
    )
    state = PIDState()
    for _ in range(100):
        step = pid_step(config, state, setpoint=1.0, measurement=0.0, dt_s=0.01)
        state = step.state
    assert step.output == 10.0
    assert step.saturated
    assert config.integral_min <= state.integral <= config.integral_max


@pytest.fixture(scope="module")
def nominal_report():
    return run_closed_loop_axis(demo_nominal_scenario())


@pytest.fixture(scope="module")
def fault_report():
    return run_closed_loop_axis(demo_fault_scenario())


def test_nominal_cosimulation_is_finite_and_tracks(nominal_report):
    assert nominal_report.finite
    assert len(nominal_report.samples) == 7501
    assert abs(nominal_report.final_error_m) < abs(nominal_report.scenario.setpoint_m)
    assert nominal_report.absolute_electrical_energy_j >= abs(nominal_report.net_electrical_energy_j)
    assert nominal_report.peak_temperature_k >= nominal_report.plant.ambient_temperature_k
    assert nominal_report.physics_certified is False
    assert nominal_report.software_certified is False
    assert nominal_report.hardware_validated is False


def test_fault_cosimulation_observes_deadline_misses(fault_report):
    assert fault_report.finite
    assert fault_report.deadline_miss_count > 0
    assert any(item.deadline_missed for item in fault_report.samples)
    assert len(fault_report.evidence_hash) == 64


def test_cosimulation_is_deterministic(nominal_report):
    again = run_closed_loop_axis(demo_nominal_scenario())
    assert again.evidence_hash == nominal_report.evidence_hash
    assert again.final_position_m == nominal_report.final_position_m


def test_low_current_limit_latches_shutdown():
    scenario = ClosedLoopScenario(
        scenario_id="low-current-limit",
        duration_s=0.2,
        integration_step_s=0.0002,
        setpoint_m=0.05,
    )
    report = run_closed_loop_axis(
        scenario,
        safety=SafetyLimits(
            current_limit_a=0.1,
            temperature_limit_k=353.15,
            absolute_position_limit_m=0.25,
            absolute_velocity_limit_mps=1.5,
        ),
    )
    assert "overcurrent" in report.shutdown_reasons
    assert any(item.shutdown_latched for item in report.samples)


def test_stuck_voltage_fault_is_represented():
    scenario = ClosedLoopScenario(
        scenario_id="stuck-voltage",
        duration_s=0.1,
        integration_step_s=0.0002,
        setpoint_m=0.0,
        faults=(FaultEvent("stuck", 0.01, 0.08, stuck_voltage_v=12.0),),
    )
    report = run_closed_loop_axis(scenario)
    assert any(abs(item.voltage_command_v) > 1.0 for item in report.samples if 0.02 <= item.time_s <= 0.07)


def test_default_architecture_ids_are_unique():
    templates = default_prototype_architectures()
    assert len(templates) >= 10
    assert len({item.architecture_id for item in templates}) == len(templates)
    for item in templates:
        item.validate()


def test_integrated_robot_compiles_to_mobile_platform():
    report = compile_prototype(demo_integrated_robot_intent())
    assert report.best is not None
    assert report.best.architecture.architecture_id == "mobile-robot-platform"
    assert report.eligible_count >= 2
    assert report.permanent_total_cap is None
    assert report.heuristic_only
    assert report.engineering_recommendation is False


def test_impossible_intent_can_reject_all_templates():
    intent = PrototypeIntent(
        intent_id="impossible",
        name="Impossible fixture",
        required_domains=("mechanical_translational", "electrical_power", "software"),
        motion_type="linear",
        continuous_power_w=1_000_000.0,
        peak_power_w=2_000_000.0,
        supply_voltage_v=5.0,
        installation_volume_m3=0.000001,
        payload_or_load=1.0,
    )
    report = compile_prototype(intent)
    assert report.best is None
    assert report.eligible_count == 0
    assert all(not item.eligible for item in report.candidates)


def test_fault_propagation_is_deterministic_and_not_probability():
    blueprint = demo_electromechanical_axis_blueprint()
    left = analyze_fault_propagation(blueprint)
    right = analyze_fault_propagation(blueprint)
    assert left.evidence_hash == right.evidence_hash
    assert len(left.records) == len(blueprint.fault_modes)
    assert left.highest_rpn > 0
    assert left.probability_claim is False
    assert left.safety_certified is False
    assert any(item.single_point_risk for item in left.records)


def test_evidence_chain_is_contiguous_through_d3(nominal_report):
    blueprint = demo_electromechanical_axis_blueprint()
    test_hash = hashlib.sha256(b"tests").hexdigest()
    receipts = computational_demo_receipts(
        blueprint_hash=blueprint.evidence_hash,
        simulation_hash=nominal_report.evidence_hash,
        test_definition_hash=test_hash,
        test_count=3,
    )
    ledger = assess_evidence_ledger(receipts)
    assert ledger.contiguous_tier == "D3_COSIMULATED_SYSTEM"
    assert ledger.highest_supported_tier == "D3_COSIMULATED_SYSTEM"
    assert not ledger.missing_lower_tiers
    assert ledger.automatic_model_promotion is False
    assert ledger.software_granted_certification is False
    assert ledger.regulatory_certified is False


def test_duplicate_evidence_receipts_are_rejected(nominal_report):
    blueprint = demo_electromechanical_axis_blueprint()
    test_hash = hashlib.sha256(b"tests").hexdigest()
    receipts = computational_demo_receipts(
        blueprint_hash=blueprint.evidence_hash,
        simulation_hash=nominal_report.evidence_hash,
        test_definition_hash=test_hash,
        test_count=1,
    )
    with pytest.raises(ValueError, match="duplicate receipt_id"):
        assess_evidence_ledger(receipts + (receipts[0],))


def test_phantom_hil_receipt_is_blocked():
    receipt = SystemEvidenceReceipt(
        receipt_id="phantom-hil",
        tier="D4_HIL_SIL",
        artifact_sha256="0" * 64,
        provenance="negative test",
        method="claim without hardware evidence",
        limitations=("no hardware evidence",),
        metadata={"hardware_ids": [], "firmware_hash": "", "raw_logs_retained": False},
        origin="synthetic_fixture",
    )
    assessment = assess_receipt(receipt)
    assert not assessment.accepted
    assert "missing_metadata:timing_log_hash" in assessment.blockers
    assert "hil_sil_raw_logs_not_retained" in assessment.blockers


def test_internal_regulatory_receipt_is_blocked():
    receipt = SystemEvidenceReceipt(
        receipt_id="internal-d8",
        tier="D8_REGULATORY_CERTIFICATION",
        artifact_sha256="1" * 64,
        provenance="internal software",
        method="invalid self-certification fixture",
        limitations=("negative control",),
        metadata={
            "authority": "self",
            "certificate_id": "none",
            "scope": "none",
            "expiry": "never",
            "independently_verified": True,
        },
        origin="internal_software",
        certification_claim=True,
    )
    assessment = assess_receipt(receipt)
    assert not assessment.accepted
    assert "internal_software_cannot_issue_regulatory_certification" in assessment.blockers


def test_inventory_detects_synthetic_integrated_system(tmp_path):
    system = tmp_path / "robot_axis"
    system.mkdir()
    (system / "controller.py").write_text(
        """
        # software controller with sensor ADC PWM telemetry
        # electric motor voltage current inverter battery
        # mechanical position velocity force torque shaft gear actuator
        # thermal temperature cooling data json schema
        """,
        encoding="utf-8",
    )
    report = discover_repository_systems(tmp_path)
    assert report.cyberphysical_candidate_count == 1
    assert report.integrated_candidate_count == 1
    record = report.records[0]
    assert record.path == "robot_axis"
    assert "electrical_power" in record.domains
    assert "electronic_signal" in record.domains
    assert "software" in record.domains
    assert record.manual_review_required


def test_inventory_distinguishes_software_only(tmp_path):
    system = tmp_path / "software_tool"
    system.mkdir()
    (system / "cli.py").write_text("python software cli api algorithm json schema data report", encoding="utf-8")
    report = discover_repository_systems(tmp_path)
    assert report.software_only_candidate_count == 1
    assert report.cyberphysical_candidate_count == 0


def test_inventory_summary_preserves_no_permanent_cap(tmp_path):
    system = tmp_path / "motor_system"
    system.mkdir()
    (system / "model.py").write_text("python simulation motor torque rpm voltage current sensor", encoding="utf-8")
    report = discover_repository_systems(
        tmp_path,
        config=InventoryConfig(max_files_per_system=4, max_bytes_per_file=1024),
    )
    summary = summarize_inventory(report)
    assert summary["permanent_total_cap"] is None
    assert summary["exhaustive_claim"] is False
    assert len(summary["evidence_hash"]) == 64


def test_reports_are_json_serializable(nominal_report, fault_report):
    payloads = (
        demo_electromechanical_axis_blueprint().to_dict(),
        nominal_report.to_dict(),
        fault_report.to_dict(),
        compile_prototype(demo_integrated_robot_intent()).to_dict(),
        analyze_fault_propagation(demo_electromechanical_axis_blueprint()).to_dict(),
    )
    for payload in payloads:
        assert json.loads(json.dumps(payload)) == payload


def test_cps_oak_benchmark_passes_repository_fixture():
    report = run_cps_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_CYBER_PHYSICAL_SYSTEMS_R0_1"
    assert report.physics_certified is False
    assert report.software_certified is False
    assert report.safety_certified is False
    assert report.regulatory_certified is False
