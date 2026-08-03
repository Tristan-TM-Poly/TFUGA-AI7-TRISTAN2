from math import pi

from omega_rigid_body_t.r02 import (
    PrincipalMoments,
    exact_omega,
    exact_parameters_from_state,
    integrate_midpoint_torque_free,
    invariants,
    phase_closure_report,
    principal_axis_stability,
    simulate_adaptive,
)
from omega_rigid_body_t.r02.atlas import atlas_manifest, default_atlas_config, stroboscopic_map
from omega_rigid_body_t.r02.geometry import oriented_solid_angle_closed_polygon
from omega_rigid_body_t.r02.linalg import norm
from omega_rigid_body_t.r02.oak import run_oak_benchmarks


def test_exact_phase_recovery_supports_all_valid_sign_sectors() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    for initial in ((0.2, 0.3, 1.0), (-0.2, -0.3, 1.0), (1.0, 0.25, 0.15), (-1.0, 0.25, -0.15)):
        parameters = exact_parameters_from_state(model, initial, phase_grid=512)
        recovered = exact_omega(0.0, parameters)
        assert max(abs(recovered[i] - initial[i]) for i in range(3)) < 2e-11
        assert parameters.signature[0] * parameters.signature[1] * parameters.signature[2] == 1


def test_exact_solution_is_periodic_and_preserves_invariants() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    parameters = exact_parameters_from_state(model, (0.2, 0.3, 1.0), phase_grid=512)
    initial = exact_omega(0.0, parameters)
    repeated = exact_omega(parameters.period, parameters)
    assert max(abs(initial[i] - repeated[i]) for i in range(3)) < 2e-13
    reference = invariants(model, initial)
    for fraction in (0.13, 0.37, 0.71, 0.93):
        observed = invariants(model, exact_omega(fraction * parameters.period, parameters))
        assert abs(observed.energy - reference.energy) < 2e-13
        assert abs(observed.angular_momentum_squared - reference.angular_momentum_squared) < 2e-12


def test_implicit_midpoint_preserves_both_quadratic_invariants_long_horizon() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    result = integrate_midpoint_torque_free(model, (0.2, 0.3, 1.0), t_end=100.0, steps=20_000)
    assert result.max_energy_residual < 2e-9
    assert result.max_momentum_squared_residual < 2e-9
    assert max(result.iterations) <= 5


def test_montgomery_phase_matches_full_quaternion_monodromy() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    parameters = exact_parameters_from_state(model, (0.2, 0.3, 1.0), phase_grid=512)
    report = phase_closure_report(model, parameters, samples=1024, rtol=1e-11, atol=1e-13)
    assert report.phase_residual < 6e-7
    assert report.monodromy_axis_error < 3e-7
    assert report.closure_error_body_momentum < 2e-9


def test_spherical_octant_has_solid_angle_pi_over_two() -> None:
    area = oriented_solid_angle_closed_polygon(((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    assert abs(abs(area) - pi / 2.0) < 2e-14


def test_forced_energy_and_angular_impulse_ledgers_close() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    torque = lambda time, omega, q: (0.003, -0.002, 0.004)
    result = simulate_adaptive(
        model,
        (0.4, -0.2, 0.8),
        t_end=12.0,
        samples=120,
        torque=torque,
        damping=0.01,
        rtol=2e-11,
        atol=2e-13,
    )
    assert abs(result.balance.energy_balance_residual) < 2e-9
    assert norm(result.balance.angular_impulse_balance_residual) < 3e-9


def test_torque_free_adaptive_orientation_keeps_quaternion_normalized() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    result = simulate_adaptive(model, (0.2, 0.3, 1.0), t_end=10.0, samples=50)
    for quaternion in result.quaternions:
        assert abs(sum(value * value for value in quaternion) - 1.0) < 3e-15


def test_intermediate_axis_is_the_unique_unstable_principal_rotation() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    modes = [principal_axis_stability(model, axis, 2.0) for axis in (1, 2, 3)]
    assert [mode.stable for mode in modes] == [True, False, True]
    assert all(mode.rate > 0.0 for mode in modes)


def test_atlas_is_deterministic_and_skips_invalid_inertia_pairs() -> None:
    config = default_atlas_config(inertia_count=3, energy_count=8)
    first = atlas_manifest(config)
    second = atlas_manifest(config)
    assert first["sha256"] == second["sha256"]
    assert first["materialized_cells"] == second["materialized_cells"]
    assert first["materialized_cells"] > 0
    assert first["claims"]["physical_certification"] is False


def test_stroboscopic_map_returns_one_state_per_forcing_cycle() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    trajectory = stroboscopic_map(
        model,
        (0.2, 0.3, 1.0),
        forcing_period=0.5,
        cycles=12,
        torque=lambda time, omega, q: (1e-3, 0.0, 0.0),
    )
    assert len(trajectory.times) == 13
    assert trajectory.times[-1] == 6.0


def test_input_guards_reject_nonordered_moments() -> None:
    try:
        PrincipalMoments(1.0, 1.0, 3.0)
    except ValueError as exc:
        assert "ordered distinct" in str(exc)
    else:
        raise AssertionError("equal principal moments must be rejected by R0.2")


def test_oak_report_passes_without_claiming_experimental_certification() -> None:
    report = run_oak_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_ANALYTIC_COMPUTATIONAL_CORE_R0_2"
    assert report.certified_physics is False
    assert report.experimental_validation is False
    assert report.new_law_of_physics_claimed is False
    assert len(report.results) == 9
