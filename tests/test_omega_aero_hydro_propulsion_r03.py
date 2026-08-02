from __future__ import annotations

import json
from math import isclose, log10

import pytest

from omega_aero_hydro_propulsion_t.acoustics import AcousticLimits, screen_rotor_acoustics
from omega_aero_hydro_propulsion_t.annular_bem import analyze_annular_bem
from omega_aero_hydro_propulsion_t.faults import FaultScenario, evaluate_fault_envelope
from omega_aero_hydro_propulsion_t.mission import demo_air_mission
from omega_aero_hydro_propulsion_t.models import default_air, demo_rotor
from omega_aero_hydro_propulsion_t.r03_oak import run_r03_benchmarks
from omega_aero_hydro_propulsion_t.robust_mission import MissionUncertaintyCase, default_uncertainty_cases, evaluate_robust_mission
from omega_aero_hydro_propulsion_t.structural import BladeMaterial, StructuralAssumptions, analyze_blade_structure, default_composite_material


def _inputs():
    rotor = demo_rotor(); medium = default_air(); mission = demo_air_mission()
    operating = mission.phases[0].operating_point
    aerodynamic = analyze_annular_bem(rotor, medium, operating)
    return rotor, medium, mission, operating, aerodynamic


def test_material_validation_rejects_nonpositive_modulus() -> None:
    with pytest.raises(ValueError):
        BladeMaterial("bad", 1000.0, 0.0, 1.0).validate()


def test_structural_report_contains_one_result_per_annulus() -> None:
    rotor, _, _, operating, aerodynamic = _inputs()
    report = analyze_blade_structure(rotor, operating, aerodynamic)
    assert report.rotor_mass > 0
    assert report.maximum_von_mises_stress >= 0
    assert report.minimum_safety_factor > 0
    assert len(report.sections) == len(aerodynamic.sections)
    assert report.physics_certified is False


def test_structural_aerodynamic_load_factor_is_monotonic() -> None:
    rotor, _, _, operating, aerodynamic = _inputs()
    lower = analyze_blade_structure(rotor, operating, aerodynamic, assumptions=StructuralAssumptions(aerodynamic_load_factor=1.0))
    higher = analyze_blade_structure(rotor, operating, aerodynamic, assumptions=StructuralAssumptions(aerodynamic_load_factor=2.0))
    assert higher.maximum_von_mises_stress >= lower.maximum_von_mises_stress


def test_stronger_material_increases_safety_factor() -> None:
    rotor, _, _, operating, aerodynamic = _inputs()
    base = default_composite_material()
    stronger = BladeMaterial(base.name + "-stronger", base.density, base.young_modulus, 2.0 * base.allowable_stress, None if base.fatigue_strength is None else 2.0 * base.fatigue_strength)
    first = analyze_blade_structure(rotor, operating, aerodynamic, material=base)
    second = analyze_blade_structure(rotor, operating, aerodynamic, material=stronger)
    assert isclose(second.minimum_safety_factor / first.minimum_safety_factor, 2.0, rel_tol=1e-12)


def test_acoustic_blade_passing_frequency_identity() -> None:
    rotor, _, _, operating, aerodynamic = _inputs()
    report = screen_rotor_acoustics(rotor, operating, aerodynamic)
    assert isclose(report.blade_passing_frequency_hz, rotor.blade_count * operating.rpm / 60.0)


def test_acoustic_distance_doubling_reduces_six_db() -> None:
    rotor, _, _, operating, aerodynamic = _inputs()
    near = screen_rotor_acoustics(rotor, operating, aerodynamic, observer_distance_m=10.0)
    far = screen_rotor_acoustics(rotor, operating, aerodynamic, observer_distance_m=20.0)
    assert isclose(near.estimated_overall_spl_db - far.estimated_overall_spl_db, 20.0 * log10(2.0), rel_tol=1e-12)


def test_acoustic_limit_violation_is_explicit() -> None:
    rotor, _, _, operating, aerodynamic = _inputs()
    report = screen_rotor_acoustics(rotor, operating, aerodynamic, limits=AcousticLimits(maximum_overall_spl_db=1.0))
    assert not report.feasible
    assert "maximum_overall_spl_db" in report.violations


def test_uncertainty_case_rejects_zero_scale() -> None:
    with pytest.raises(ValueError):
        MissionUncertaintyCase("bad", density_scale=0.0).validate()


def test_robust_mission_weights_and_energy_bounds() -> None:
    rotor, medium, mission, _, _ = _inputs()
    report = evaluate_robust_mission(rotor, medium, mission)
    assert isclose(sum(item.normalized_weight for item in report.cases), 1.0)
    assert report.minimum_shaft_energy_j <= report.expected_shaft_energy_j <= report.maximum_shaft_energy_j
    assert 0.0 <= report.feasible_probability <= 1.0
    assert len(report.cases) == len(default_uncertainty_cases())


def test_robust_mission_is_deterministic() -> None:
    rotor, medium, mission, _, _ = _inputs()
    assert evaluate_robust_mission(rotor, medium, mission).to_dict() == evaluate_robust_mission(rotor, medium, mission).to_dict()


def test_fault_scenario_rejects_invalid_power_scale() -> None:
    with pytest.raises(ValueError):
        FaultScenario("bad", available_power_scale=0.0).validate()


def test_motor_out_is_detected_as_infeasible() -> None:
    rotor, medium, mission, _, _ = _inputs()
    case = evaluate_fault_envelope(rotor, medium, mission, scenarios=(FaultScenario("motor-out", rpm_scale=0.0, available_power_scale=0.01),)).cases[0]
    assert not case.mission_feasible
    assert case.minimum_thrust_margin < 0


def test_blade_loss_preserves_dynamic_balance_limitation() -> None:
    rotor, medium, mission, _, _ = _inputs()
    case = evaluate_fault_envelope(rotor, medium, mission, scenarios=(FaultScenario("blade-loss", blade_count_delta=-1, requires_dynamic_balance_model=True, severity="hazardous"),)).cases[0]
    assert not case.safe_continuation_candidate
    assert "unmodeled_rotor_imbalance_and_transient_structural_response" in case.limitations


def test_r03_oak_benchmarks_pass_and_refuse_certification() -> None:
    report = run_r03_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_SYSTEM_SCREENING_R0_3"
    assert report.physics_certified is False
    json.dumps(report.to_dict())
