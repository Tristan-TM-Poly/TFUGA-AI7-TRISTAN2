"""Deterministic OAKBench for Ω-RIGID-BODY-T R0.2."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import pi, sqrt

from .analytic import exact_omega, exact_parameters_from_state
from .atlas import atlas_manifest, default_atlas_config
from .geometry import oriented_solid_angle_closed_polygon, phase_closure_report
from .integrators import integrate_midpoint_torque_free, simulate_adaptive
from .linalg import max_abs, norm
from .model import PrincipalMoments, principal_axis_stability


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    passed: bool
    metric: float
    threshold: float
    details: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OAKReport:
    status: str
    passed: bool
    results: tuple[BenchmarkResult, ...]
    certified_analytic_identities: bool
    certified_computational_fixtures: bool
    certified_physics: bool
    experimental_validation: bool
    new_law_of_physics_claimed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "passed": self.passed,
            "results": [result.to_dict() for result in self.results],
            "certified_analytic_identities": self.certified_analytic_identities,
            "certified_computational_fixtures": self.certified_computational_fixtures,
            "certified_physics": self.certified_physics,
            "experimental_validation": self.experimental_validation,
            "new_law_of_physics_claimed": self.new_law_of_physics_claimed,
        }


def _result(identifier: str, metric: float, threshold: float, details: str) -> BenchmarkResult:
    return BenchmarkResult(identifier, metric <= threshold, metric, threshold, details)


def run_oak_benchmarks() -> OAKReport:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    results: list[BenchmarkResult] = []

    phase_cases = (
        (0.2, 0.3, 1.0),
        (-0.2, -0.3, 1.0),
        (1.0, 0.25, 0.15),
        (-1.0, 0.25, -0.15),
    )
    phase_error = 0.0
    for state in phase_cases:
        parameters = exact_parameters_from_state(model, state, phase_grid=1024)
        recovered = exact_omega(0.0, parameters)
        phase_error = max(phase_error, max_abs(recovered[i] - state[i] for i in range(3)))
    results.append(_result("arbitrary-phase-sign-recovery", phase_error, 2e-11, "four sign sectors across both regimes"))

    midpoint = integrate_midpoint_torque_free(model, (0.2, 0.3, 1.0), t_end=100.0, steps=20_000)
    midpoint_error = max(midpoint.max_energy_residual, midpoint.max_momentum_squared_residual)
    results.append(_result("implicit-midpoint-quadratic-invariants", midpoint_error, 2e-9, "100 time units"))

    triangle = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    solid_angle_error = abs(abs(oriented_solid_angle_closed_polygon(triangle)) - pi / 2.0)
    results.append(_result("spherical-triangle-solid-angle", solid_angle_error, 2e-14, "octant triangle area π/2"))

    phase_parameters = exact_parameters_from_state(model, (0.2, 0.3, 1.0), phase_grid=1024)
    phase = phase_closure_report(model, phase_parameters, samples=2048, rtol=2e-12, atol=2e-14)
    results.append(_result("montgomery-vs-quaternion-monodromy", phase.phase_residual, 2e-7, "one exact polhode period"))
    results.append(_result("monodromy-axis-alignment", phase.monodromy_axis_error, 2e-7, "relative orientation axis parallel to inertial L"))

    constant_torque = lambda time, omega, q: (0.003, -0.002, 0.004)
    forced = simulate_adaptive(
        model,
        (0.4, -0.2, 0.8),
        t_end=12.0,
        samples=240,
        torque=constant_torque,
        damping=0.01,
        rtol=2e-11,
        atol=2e-13,
    )
    results.append(
        _result(
            "forced-energy-work-balance",
            abs(forced.balance.energy_balance_residual),
            2e-9,
            "external torque plus viscous damping",
        )
    )
    results.append(
        _result(
            "forced-angular-impulse-balance",
            norm(forced.balance.angular_impulse_balance_residual),
            3e-9,
            "inertial angular impulse ledger",
        )
    )

    stable1 = principal_axis_stability(model, 1, 2.0)
    unstable2 = principal_axis_stability(model, 2, 2.0)
    stable3 = principal_axis_stability(model, 3, 2.0)
    expected = (
        2.0 * sqrt((2.0 - 1.0) * (3.0 - 1.0) / (2.0 * 3.0)),
        2.0 * sqrt((2.0 - 1.0) * (3.0 - 2.0) / (1.0 * 3.0)),
        2.0 * sqrt((3.0 - 1.0) * (3.0 - 2.0) / (1.0 * 2.0)),
    )
    stability_error = max(abs(stable1.rate - expected[0]), abs(unstable2.rate - expected[1]), abs(stable3.rate - expected[2]))
    stability_flag_error = 0.0 if stable1.stable and not unstable2.stable and stable3.stable else 1.0
    results.append(_result("principal-axis-linear-stability", max(stability_error, stability_flag_error), 2e-15, "stable-unstable-stable theorem"))

    config = default_atlas_config(inertia_count=3, energy_count=8)
    first = atlas_manifest(config)
    second = atlas_manifest(config)
    atlas_error = 0.0 if first["sha256"] == second["sha256"] and first["materialized_cells"] == second["materialized_cells"] else 1.0
    results.append(_result("deterministic-parameter-atlas", atlas_error, 0.0, f"sha256={first['sha256']}"))

    passed = all(result.passed for result in results)
    return OAKReport(
        status="CERTIFIED_ANALYTIC_COMPUTATIONAL_CORE_R0_2" if passed else "FAILED_OAK_R0_2",
        passed=passed,
        results=tuple(results),
        certified_analytic_identities=passed,
        certified_computational_fixtures=passed,
        certified_physics=False,
        experimental_validation=False,
        new_law_of_physics_claimed=False,
    )
