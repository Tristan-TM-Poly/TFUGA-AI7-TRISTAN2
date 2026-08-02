from __future__ import annotations

from math import isclose

import pytest

from omega_aero_hydro_propulsion_t.annular_bem import analyze_annular_bem
from omega_aero_hydro_propulsion_t.mission import (
    MissionGenome,
    MissionPhase,
    demo_air_mission,
    evaluate_mission,
)
from omega_aero_hydro_propulsion_t.models import (
    BladeStation,
    OperatingPoint,
    RotorDesign,
    default_air,
    demo_rotor,
)
from omega_aero_hydro_propulsion_t.polars import (
    PolarRegistry,
    PolarSample,
    PolarTable,
    demo_polar_table,
)
from omega_aero_hydro_propulsion_t.r02_oak import run_r02_benchmarks


def test_polar_exact_state_and_alpha_interpolation() -> None:
    table = PolarTable.from_samples(
        "linear",
        (
            PolarSample(0.0, 100_000.0, 0.1, 0.0, 0.01),
            PolarSample(10.0, 100_000.0, 0.1, 1.0, 0.05),
            PolarSample(0.0, 500_000.0, 0.2, 0.0, 0.009),
            PolarSample(10.0, 500_000.0, 0.2, 1.1, 0.04),
        ),
        source_type="test",
        provenance="unit-test",
    )
    point = table.evaluate(5.0, reynolds=100_000.0, mach=0.1)
    assert isclose(point.lift_coefficient, 0.5, abs_tol=1e-12)
    assert not point.condition_extrapolated


def test_polar_registry_csv_import() -> None:
    text = (
        "alpha_deg,reynolds,mach,cl,cd,cm\n"
        "0,100000,0.1,0,0.01,-0.02\n"
        "10,100000,0.1,1,0.05,-0.03\n"
    )
    table = PolarTable.from_csv_text("csv-polar", text, source_type="fixture")
    registry = PolarRegistry([table])
    assert registry.contains("csv-polar")
    assert registry.evaluate("csv-polar", 5.0, reynolds=100_000.0, mach=0.1).lift_coefficient == pytest.approx(0.5)


def test_polar_duplicate_sample_is_rejected() -> None:
    sample = PolarSample(0.0, 100_000.0, 0.1, 0.0, 0.01)
    with pytest.raises(ValueError):
        PolarTable.from_samples("duplicate", (sample, sample), source_type="test", provenance="test")


def test_annular_bem_converges_with_positive_load() -> None:
    result = analyze_annular_bem(demo_rotor(), default_air(), OperatingPoint(22.0, 2_200.0))
    assert result.converged
    assert result.maximum_section_residual <= 1e-6
    assert result.thrust > 0
    assert result.torque > 0
    assert result.shaft_power > 0
    assert all(0.0 < section.tip_hub_loss_factor <= 1.0 for section in result.sections)


def test_annular_bem_dispatches_tabulated_polars() -> None:
    base = demo_rotor()
    design = RotorDesign(
        name="tabulated-test",
        blade_count=base.blade_count,
        hub_radius=base.hub_radius,
        tip_radius=base.tip_radius,
        stations=tuple(
            BladeStation(station.radius, station.chord, station.twist_deg, "demo-tabulated-symmetric")
            for station in base.stations
        ),
    )
    result = analyze_annular_bem(
        design,
        default_air(),
        OperatingPoint(22.0, 2_200.0),
        registry=PolarRegistry([demo_polar_table()]),
    )
    assert result.converged
    assert all(section.polar_model.startswith("tabulated") for section in result.sections)


def test_stationary_annular_rotor_has_zero_load() -> None:
    result = analyze_annular_bem(demo_rotor(), default_air(), OperatingPoint(20.0, 0.0))
    assert result.converged
    assert result.thrust == 0.0
    assert result.torque == 0.0
    assert result.shaft_power == 0.0


def test_mission_evaluation_is_multipoint_and_energy_conservative() -> None:
    report = evaluate_mission(demo_rotor(), default_air(), demo_air_mission())
    assert len(report.phases) == 3
    assert report.feasible
    assert report.total_shaft_energy_j > 0
    assert report.total_shaft_energy_j == pytest.approx(
        sum(phase.shaft_energy_j for phase in report.phases)
    )
    assert 0.0 <= report.mission_efficiency <= 1.0


def test_mission_phase_names_are_unique() -> None:
    phase = MissionPhase("duplicate", 1.0, OperatingPoint(1.0, 100.0))
    with pytest.raises(ValueError):
        MissionGenome.from_phases(
            name="invalid",
            domain="aerial",
            vehicle="test",
            phases=(phase, phase),
        )


def test_r02_oak_gates_pass_without_physics_certification() -> None:
    report = run_r02_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_MULTIPOINT_R0_2"
    assert not report.physics_certified
