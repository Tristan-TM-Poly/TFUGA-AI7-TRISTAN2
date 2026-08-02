from __future__ import annotations

from math import isclose, isinf

import pytest

from omega_aero_hydro_propulsion_t.airfoil import analytic_polar
from omega_aero_hydro_propulsion_t.analysis import analyze_rotor
from omega_aero_hydro_propulsion_t.cavitation import assess_cavitation, cavitation_number
from omega_aero_hydro_propulsion_t.models import (
    BladeStation,
    FluidMedium,
    OperatingPoint,
    RotorDesign,
    default_air,
    default_water,
    demo_rotor,
)
from omega_aero_hydro_propulsion_t.oak import run_propulsion_benchmarks
from omega_aero_hydro_propulsion_t.optimizer import OptimizationConstraints, grid_optimize, scale_rotor


def test_demo_rotor_validates() -> None:
    rotor = demo_rotor()
    rotor.validate()
    assert rotor.disk_area > 0
    assert rotor.diameter == 1.2


def test_rotor_rejects_unsorted_stations() -> None:
    rotor = RotorDesign.from_stations(
        name="bad",
        blade_count=2,
        hub_radius=0.1,
        tip_radius=0.5,
        stations=(BladeStation(0.4, 0.1, 10), BladeStation(0.2, 0.1, 20)),
    )
    with pytest.raises(ValueError):
        rotor.validate()


def test_analytic_polar_is_antisymmetric_in_lift() -> None:
    positive = analytic_polar(5.0, reynolds=500_000, mach=0.1)
    negative = analytic_polar(-5.0, reynolds=500_000, mach=0.1)
    assert isclose(positive.lift_coefficient, -negative.lift_coefficient, rel_tol=1e-12)
    assert isclose(positive.drag_coefficient, negative.drag_coefficient, rel_tol=1e-12)


def test_zero_rpm_produces_zero_load() -> None:
    result = analyze_rotor(demo_rotor(), default_air(), OperatingPoint(20.0, 0.0))
    assert result.thrust == 0
    assert result.torque == 0
    assert result.shaft_power == 0


def test_air_rotor_produces_positive_load_and_converges() -> None:
    result = analyze_rotor(demo_rotor(), default_air(), OperatingPoint(22.0, 2200.0))
    assert result.thrust > 0
    assert result.torque > 0
    assert result.shaft_power > 0
    assert result.converged
    assert result.tip_mach > 0


def test_density_scaling_without_induction() -> None:
    air = default_air()
    double = FluidMedium(
        "double",
        2 * air.density,
        2 * air.dynamic_viscosity,
        air.sound_speed,
        air.ambient_pressure,
    )
    a = analyze_rotor(demo_rotor(), air, OperatingPoint(22.0, 2200.0), max_iterations=0)
    b = analyze_rotor(demo_rotor(), double, OperatingPoint(22.0, 2200.0), max_iterations=0)
    assert isclose(b.thrust / a.thrust, 2.0, rel_tol=1e-12)


def test_cavitation_number_infinite_at_zero_speed() -> None:
    assert isinf(cavitation_number(ambient_pressure=101325, vapor_pressure=2339, density=998, speed=0))


def test_water_cavitation_assessment_is_applicable() -> None:
    water = default_water()
    result = analyze_rotor(demo_rotor(), water, OperatingPoint(3.0, 700.0))
    assessment = assess_cavitation(result, water)
    assert assessment.applicable
    assert assessment.minimum_cavitation_number is not None
    assert assessment.minimum_margin is not None


def test_air_cavitation_assessment_not_applicable() -> None:
    air = default_air()
    result = analyze_rotor(demo_rotor(), air, OperatingPoint(20.0, 2000.0))
    assert not assess_cavitation(result, air).applicable


def test_scale_rotor_preserves_topology() -> None:
    base = demo_rotor()
    scaled = scale_rotor(base, diameter_scale=1.2, chord_scale=0.9, pitch_delta_deg=2.0)
    assert isclose(scaled.tip_radius, 1.2 * base.tip_radius)
    assert len(scaled.stations) == len(base.stations)
    assert isclose(scaled.stations[0].chord, 0.9 * base.stations[0].chord)


def test_optimizer_returns_deterministic_feasible_candidate() -> None:
    report = grid_optimize(
        demo_rotor(),
        default_air(),
        OperatingPoint(22.0, 2200.0),
        diameter_scales=(0.9, 1.0),
        chord_scales=(0.9, 1.0),
        pitch_deltas_deg=(-2.0, 0.0, 2.0),
        constraints=OptimizationConstraints(minimum_thrust=1.0, maximum_tip_mach=0.85),
    )
    assert report.candidate_count == 12
    assert report.feasible_count > 0
    assert report.best is not None
    assert report.pareto_front


def test_oak_benchmark_passes_and_refuses_physics_certification() -> None:
    report = run_propulsion_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_LOW_ORDER"
    assert report.physics_certified is False
