from __future__ import annotations

from dataclasses import replace

import pytest

from omega_cyber_physical_systems_t.cosim import (
    demo_fault_scenario,
    demo_nominal_scenario,
    run_closed_loop_axis,
)
from omega_cyber_physical_systems_t.energy_graph import audit_closed_loop_energy
from omega_cyber_physical_systems_t.models import (
    Component,
    Connection,
    Port,
    SystemBlueprint,
    demo_electromechanical_axis_blueprint,
)
from omega_cyber_physical_systems_t.r02_oak import run_cps_r02_benchmarks
from omega_cyber_physical_systems_t.unit_graph import (
    POWER_DIMENSION,
    UnitDefinition,
    UnitRegistry,
    audit_blueprint_units,
    default_unit_registry,
)


def test_default_unit_registry_validates_and_has_power_dimension() -> None:
    registry = default_unit_registry()
    registry.validate()
    assert registry.get("W").dimension == POWER_DIMENSION
    assert len(registry.definitions) >= 20


def test_rpm_conversion_is_two_pi_radians_per_second() -> None:
    registry = default_unit_registry()
    assert registry.convert(60.0, "rpm", "rad/s") == pytest.approx(2.0 * 3.141592653589793)


def test_litre_per_minute_conversion() -> None:
    registry = default_unit_registry()
    assert registry.convert(60.0, "L/min", "m^3/s") == pytest.approx(0.001)


def test_incompatible_conversion_is_blocked() -> None:
    registry = default_unit_registry()
    with pytest.raises(ValueError):
        registry.convert(1.0, "V", "N")


def test_invalid_unit_scale_is_blocked() -> None:
    bad = UnitDefinition("bad", 0.0, (0, 0, 0, 0, 0, 0, 0), "bad fixture")
    with pytest.raises(ValueError):
        bad.validate()


def test_registry_key_must_match_symbol() -> None:
    definition = UnitDefinition("m", 1.0, (0, 1, 0, 0, 0, 0, 0), "metre")
    registry = UnitRegistry({"wrong": definition})
    with pytest.raises(ValueError):
        registry.validate()


def test_demo_blueprint_unit_graph_is_dimensionally_valid() -> None:
    report = audit_blueprint_units(demo_electromechanical_axis_blueprint())
    assert report.dimensionally_valid
    assert report.unknown_unit_count == 0
    assert report.error_count == 0


def test_demo_blueprint_connections_are_causal_and_compatible() -> None:
    report = audit_blueprint_units(demo_electromechanical_axis_blueprint())
    assert report.causal_connections_valid
    assert all(item.effort_dimension_compatible for item in report.connection_assessments)
    assert all(item.flow_dimension_compatible for item in report.connection_assessments)


def test_thermal_direct_heat_rate_is_explicit_warning() -> None:
    report = audit_blueprint_units(demo_electromechanical_axis_blueprint())
    thermal = [item for item in report.port_assessments if item.domain == "thermal"]
    assert len(thermal) == 1
    assert thermal[0].direct_power_flow
    assert "thermal_heat_rate_used_instead_of_entropy_flow" in thermal[0].findings
    assert report.warning_count >= 1


def test_nonenergetic_ports_are_not_mislabeled_as_power() -> None:
    report = audit_blueprint_units(demo_electromechanical_axis_blueprint())
    signal_ports = [
        item for item in report.port_assessments
        if item.domain in ("electronic_signal", "software", "data")
    ]
    assert signal_ports
    assert all(not item.power_conjugate for item in signal_ports)


def test_unknown_unit_is_detected() -> None:
    blueprint = demo_electromechanical_axis_blueprint()
    component = blueprint.components[0]
    altered_port = replace(component.ports[0], effort_unit="mystery-unit")
    altered_component = replace(component, ports=(altered_port,))
    altered = replace(blueprint, components=(altered_component,) + blueprint.components[1:])
    report = audit_blueprint_units(altered)
    assert not report.dimensionally_valid
    assert report.unknown_unit_count == 1
    assert report.error_count >= 1


def test_physical_dimension_mismatch_is_detected() -> None:
    bad_port = Port("bad", "mechanical_translational", "output", "V", "A")
    bad_component = Component.build(
        component_id="bad",
        kind="bad-fixture",
        domains=("mechanical_translational",),
        ports=(bad_port,),
    )
    blueprint = SystemBlueprint.build(
        system_id="bad-units",
        name="bad units",
        components=(bad_component,),
        connections=(),
    )
    report = audit_blueprint_units(blueprint)
    assert not report.dimensionally_valid
    assert report.error_count == 1


def test_scale_conversion_connection_is_warning_not_error() -> None:
    source = Component.build(
        component_id="source",
        kind="source",
        domains=("data",),
        ports=(Port("out", "data", "output", "mm", "sample/s"),),
        physical=False,
    )
    target = Component.build(
        component_id="target",
        kind="target",
        domains=("data",),
        ports=(Port("in", "data", "input", "m", "sample/s"),),
        physical=False,
    )
    blueprint = SystemBlueprint.build(
        system_id="scale-adapter",
        name="scale adapter",
        components=(source, target),
        connections=(Connection("scale", "source", "out", "target", "in", "declared scale adapter"),),
    )
    report = audit_blueprint_units(blueprint)
    assert report.dimensionally_valid
    assert report.connection_assessments[0].severity == "warning"
    assert report.connection_assessments[0].effort_scale_ratio == pytest.approx(0.001)


def test_nominal_energy_audit_is_finite_and_balanced() -> None:
    simulation = run_closed_loop_axis(demo_nominal_scenario())
    report = audit_closed_loop_energy(simulation)
    assert report.finite
    assert report.balance_passed
    assert report.global_normalized_residual <= 0.02


def test_nominal_domain_balances_close() -> None:
    report = audit_closed_loop_energy(run_closed_loop_axis(demo_nominal_scenario()))
    assert report.balance("electrical").passed
    assert report.balance("thermal").passed
    assert report.balance("mechanical").passed
    assert report.balance("global").passed


def test_energy_audit_is_deterministic() -> None:
    simulation = run_closed_loop_axis(demo_nominal_scenario())
    first = audit_closed_loop_energy(simulation)
    second = audit_closed_loop_energy(simulation)
    assert first.evidence_hash == second.evidence_hash


def test_untracked_energy_probe_breaks_global_balance() -> None:
    simulation = run_closed_loop_axis(demo_nominal_scenario())
    report = audit_closed_loop_energy(simulation, untracked_output_energy_j=5.0)
    assert not report.balance("global").passed
    assert not report.balance_passed
    assert abs(report.global_residual_j) > report.residual_tolerance_j


def test_negative_untracked_energy_is_blocked() -> None:
    simulation = run_closed_loop_axis(demo_nominal_scenario())
    with pytest.raises(ValueError):
        audit_closed_loop_energy(simulation, untracked_output_energy_j=-1.0)


def test_invalid_energy_tolerance_is_blocked() -> None:
    simulation = run_closed_loop_axis(demo_nominal_scenario())
    with pytest.raises(ValueError):
        audit_closed_loop_energy(simulation, residual_tolerance_fraction=0.0)


def test_faulted_energy_audit_remains_finite() -> None:
    simulation = run_closed_loop_axis(demo_fault_scenario())
    report = audit_closed_loop_energy(simulation)
    assert report.finite
    assert report.sample_count == len(simulation.samples)
    assert report.source_report_hash == simulation.evidence_hash


def test_loss_terms_are_nonnegative_in_nominal_fixture() -> None:
    report = audit_closed_loop_energy(run_closed_loop_axis(demo_nominal_scenario()))
    assert report.term("copper_loss").energy_j >= 0
    assert report.term("damping_loss").energy_j >= 0
    assert report.term("cooling_loss").energy_j >= 0


def test_passivity_is_never_formally_proven_by_software() -> None:
    report = audit_closed_loop_energy(run_closed_loop_axis(demo_nominal_scenario()))
    assert not report.passivity.passivity_proven
    assert not report.passivity.physical_validation
    assert not report.energy_conservation_proven
    assert not report.physics_certified
    assert not report.hardware_validated


def test_unknown_energy_term_lookup_fails() -> None:
    report = audit_closed_loop_energy(run_closed_loop_axis(demo_nominal_scenario()))
    with pytest.raises(KeyError):
        report.term("unknown")


def test_unknown_balance_lookup_fails() -> None:
    report = audit_closed_loop_energy(run_closed_loop_axis(demo_nominal_scenario()))
    with pytest.raises(KeyError):
        report.balance("unknown")


def test_r02_oak_benchmark_passes_without_overclaiming() -> None:
    report = run_cps_r02_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_UNIT_ENERGY_GRAPH_R0_2"
    assert all(gate.passed for gate in report.gates)
    assert not report.physics_certified
    assert not report.energy_conservation_proven
    assert not report.passivity_proven
    assert not report.standards_compliance_claim
    assert not report.hardware_validated


def test_r02_hashes_are_sha256_length() -> None:
    report = run_cps_r02_benchmarks()
    assert len(report.unit_graph_hash) == 64
    assert len(report.nominal_energy_hash) == 64
    assert len(report.faulted_energy_hash) == 64
    assert len(report.adversarial_energy_hash) == 64
