from math import isfinite

from omega_rigid_body_t import (
    Invariants,
    PrincipalInertia,
    analytic_omega,
    classify_regime,
    complete_elliptic_k,
    elliptic_parameters,
    integrate_orientation_quaternion,
    integrate_rk4,
    invariants_from_state,
    jacobi_sncndn,
    quaternion_to_matrix,
    run_oak_benchmarks,
    separatrix_omega,
)


def test_jacobi_real_identities_and_limits() -> None:
    for m in (0.0, 0.1, 0.5, 0.9, 1.0):
        for u in (-2.0, -0.1, 0.0, 0.7, 3.0):
            sn, cn, dn = jacobi_sncndn(u, m)
            assert abs(sn * sn + cn * cn - 1.0) < 1e-12
            assert abs(dn * dn + m * sn * sn - 1.0) < 1e-12
    assert complete_elliptic_k(0.0) > 1.5


def test_invariant_regime_classification() -> None:
    inertia = PrincipalInertia(1.0, 2.0, 3.0)
    assert classify_regime(inertia, Invariants(1.8, 9.0)) == "stable_axis_3"
    assert classify_regime(inertia, Invariants(2.25, 9.0)) == "separatrix_intermediate_axis"
    assert classify_regime(inertia, Invariants(3.6, 9.0)) == "stable_axis_1"


def test_exact_axis3_solution_is_periodic_and_preserves_invariants() -> None:
    inertia = PrincipalInertia(1.0, 2.0, 3.0)
    invariants = Invariants(1.8, 9.0)
    parameters = elliptic_parameters(inertia, invariants)
    initial = analytic_omega(0.0, parameters)
    final = analytic_omega(parameters.period, parameters)
    assert max(abs(a - b) for a, b in zip(initial, final)) < 1e-11
    observed = invariants_from_state(inertia, analytic_omega(0.371 * parameters.period, parameters))
    assert abs(observed.energy - invariants.energy) < 1e-12
    assert abs(observed.angular_momentum_squared - invariants.angular_momentum_squared) < 1e-11


def test_exact_axis1_solution_agrees_with_independent_rk4() -> None:
    inertia = PrincipalInertia(1.0, 2.0, 3.0)
    invariants = Invariants(3.6, 9.0)
    parameters = elliptic_parameters(inertia, invariants)
    times = [parameters.period * index / 24.0 for index in range(25)]
    exact = [analytic_omega(time, parameters) for time in times]
    numerical = integrate_rk4(inertia, exact[0], times)
    assert max(abs(a - b) for x, y in zip(exact, numerical) for a, b in zip(x, y)) < 2e-8


def test_separatrix_has_intermediate_axis_sign_change() -> None:
    inertia = PrincipalInertia(1.0, 2.0, 3.0)
    left = separatrix_omega(-10.0, inertia, 3.0)
    center = separatrix_omega(0.0, inertia, 3.0)
    right = separatrix_omega(10.0, inertia, 3.0)
    assert left[1] < 0.0 < right[1]
    assert center[1] == 0.0
    assert center[0] > 0.0 and center[2] > 0.0


def test_orientation_reconstruction_stays_on_so3() -> None:
    inertia = PrincipalInertia(1.0, 2.0, 3.0)
    parameters = elliptic_parameters(inertia, Invariants(1.8, 9.0))
    omega = lambda time: analytic_omega(time, parameters)
    quaternions = integrate_orientation_quaternion(omega, [0.0, 0.5, 1.0])
    for q in quaternions:
        assert abs(sum(value * value for value in q) - 1.0) < 1e-12
        matrix = quaternion_to_matrix(q)
        determinant = (
            matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
            - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
            + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
        )
        assert abs(determinant - 1.0) < 1e-12


def test_validation_rejects_degenerate_or_nonphysical_inputs() -> None:
    try:
        PrincipalInertia(1.0, 1.0, 2.0)
    except ValueError as exc:
        assert "I1 < I2 < I3" in str(exc)
    else:
        raise AssertionError("degenerate inertia must be rejected in the triaxial kernel")


def test_oakbench_passes_without_experimental_certification() -> None:
    report = run_oak_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_ANALYTIC_COMPUTATIONAL_CORE"
    assert report.certified_physical_experiment is False
    assert all(isfinite(result.metric) for result in report.results)
