from __future__ import annotations

from math import radians

import pytest

from omega_space_hg_t.attitude import (
    AttitudeControlConfig,
    GyroModel,
    StarTrackerModel,
    magnetic_dipole_torque,
    quaternion_from_axis_angle,
    quaternion_multiply,
    quaternion_norm,
    rotate_vector,
    simulate_attitude_control,
)
from omega_space_hg_t.oak import EARTH_MU_M3_S2, EARTH_RADIUS_M
from omega_space_hg_t.orbit import norm
from omega_space_hg_t.perturbations import (
    PerturbationConfig,
    drag_acceleration,
    j2_acceleration,
    keplerian_to_cartesian,
    osculating_elements,
    solar_radiation_pressure_acceleration,
)
from omega_space_hg_t.r02 import (
    canonical_attitude_case,
    canonical_inclined_orbit,
    canonical_perturbation_config,
    run_r02_oak_benchmarks,
    simulate_r02_attitude,
    simulate_r02_orbit,
)


def test_keplerian_cartesian_round_trip_preserves_primary_elements() -> None:
    state = keplerian_to_cartesian(
        EARTH_RADIUS_M + 700_000.0,
        0.01,
        radians(63.4),
        radians(25.0),
        radians(40.0),
        radians(15.0),
        EARTH_MU_M3_S2,
    )
    elements = osculating_elements(state, EARTH_MU_M3_S2)
    assert elements.semimajor_axis_m == pytest.approx(EARTH_RADIUS_M + 700_000.0, rel=1e-12)
    assert elements.eccentricity == pytest.approx(0.01, rel=1e-11)
    assert elements.inclination_rad == pytest.approx(radians(63.4), rel=1e-12)
    assert elements.raan_rad == pytest.approx(radians(25.0), rel=1e-12)


def test_j2_numerical_raan_drift_matches_first_order_theory() -> None:
    report = simulate_r02_orbit(duration_orbits=10.0, step_s=20.0)
    assert report["relative_raan_rate_error"] < 0.02
    assert report["operational_ephemeris_claimed"] is False


def test_perturbation_components_have_expected_direction_and_zero_modes() -> None:
    state = canonical_inclined_orbit()
    base = PerturbationConfig(
        mu_m3_s2=EARTH_MU_M3_S2,
        body_radius_m=EARTH_RADIUS_M,
        mass_kg=10.0,
    )
    assert j2_acceleration(state.position_m, base) == (0.0, 0.0, 0.0)
    assert drag_acceleration(state, base) == (0.0, 0.0, 0.0)
    assert solar_radiation_pressure_acceleration(state, base) == (0.0, 0.0, 0.0)

    srp = canonical_perturbation_config(include_srp=True)
    acceleration = solar_radiation_pressure_acceleration(state, srp)
    assert acceleration[0] > 0.0
    assert acceleration[1] == pytest.approx(0.0)
    assert acceleration[2] == pytest.approx(0.0)


def test_drag_reduces_relative_velocity_energy() -> None:
    config = canonical_perturbation_config(include_drag=True)
    state = canonical_inclined_orbit()
    acceleration = drag_acceleration(state, config)
    atmosphere_velocity = (
        -config.body_rotation_rad_s * state.position_m[1],
        config.body_rotation_rad_s * state.position_m[0],
        0.0,
    )
    relative_velocity = tuple(
        state.velocity_m_s[index] - atmosphere_velocity[index] for index in range(3)
    )
    assert sum(acceleration[index] * relative_velocity[index] for index in range(3)) < 0.0


def test_quaternion_composition_rotation_and_norm() -> None:
    qz = quaternion_from_axis_angle((0.0, 0.0, 1.0), radians(90.0))
    qy = quaternion_from_axis_angle((0.0, 1.0, 0.0), radians(90.0))
    composite = quaternion_multiply(qz, qy)
    rotated = rotate_vector(composite, (1.0, 0.0, 0.0))
    assert quaternion_norm(composite) == pytest.approx(1.0, abs=1e-15)
    assert norm(rotated) == pytest.approx(1.0, abs=1e-15)


def test_closed_loop_attitude_reduces_error_without_wheel_saturation() -> None:
    report = simulate_r02_attitude()
    metrics = report["metrics"]
    assert metrics["final_error_rad"] < radians(0.5)
    assert metrics["final_error_rad"] < 0.02 * metrics["initial_error_rad"]
    assert metrics["quaternion_norm_error"] < 1e-12
    assert metrics["wheel_saturation_count"] == 0
    assert report["flight_software_claimed"] is False


def test_sensor_sequences_and_closed_loop_are_deterministic() -> None:
    first = simulate_r02_attitude()
    second = simulate_r02_attitude()
    assert first["deterministic_sensor_digest"] == second["deterministic_sensor_digest"]
    assert first["metrics"] == second["metrics"]


def test_reaction_wheel_limits_are_enforced() -> None:
    initial, target, controller = canonical_attitude_case()
    constrained = AttitudeControlConfig(
        inertia_kg_m2=controller.inertia_kg_m2,
        kp_n_m_per_quaternion=controller.kp_n_m_per_quaternion,
        kd_n_m_s=controller.kd_n_m_s,
        max_wheel_torque_n_m=(1e-4, 1e-4, 1e-4),
        max_wheel_momentum_nms=(5e-4, 5e-4, 5e-4),
    )
    result = simulate_attitude_control(
        initial,
        target,
        20.0,
        0.1,
        constrained,
        gyro=GyroModel(),
        star_tracker=StarTrackerModel(),
    )
    assert result.metrics.torque_saturation_count > 0
    assert result.metrics.maximum_wheel_momentum_fraction <= 1.0
    assert all(
        abs(state.wheel_momentum_nms[axis]) <= constrained.max_wheel_momentum_nms[axis]
        for state in result.states
        for axis in range(3)
    )


def test_magnetic_dipole_torque_obeys_cross_product_geometry() -> None:
    torque = magnetic_dipole_torque((1.0, 0.0, 0.0), (0.0, 2e-5, 0.0))
    assert torque == pytest.approx((0.0, 0.0, 2e-5))


def test_r02_oakbench_passes_reduced_order_fixtures_only() -> None:
    report = run_r02_oak_benchmarks()
    assert report["passed"] is True
    assert len(report["checks"]) >= 6
    assert report["flight_qualified_claimed"] is False
    assert report["operational_ephemeris_claimed"] is False
    assert report["conjunction_assessment_claimed"] is False
    assert report["stability_proof_claimed"] is False
