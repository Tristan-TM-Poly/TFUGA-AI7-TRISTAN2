"""OAKBench checks for the dependency-free Euler-top kernel."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite

from .elliptic import complete_elliptic_k, jacobi_sncndn, near_separatrix_period_asymptotic
from .euler_top import (
    Invariants,
    PrincipalInertia,
    analytic_omega,
    elliptic_parameters,
    integrate_orientation_quaternion,
    integrate_rk4,
    invariant_residuals,
    quaternion_to_matrix,
)


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    passed: bool
    metric: float
    tolerance: float
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OAKReport:
    status: str
    passed: bool
    results: tuple[BenchmarkResult, ...]
    certified_analytic_identities: bool
    certified_numerical_crosscheck: bool
    certified_physical_experiment: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "passed": self.passed,
            "results": [result.to_dict() for result in self.results],
            "certified_analytic_identities": self.certified_analytic_identities,
            "certified_numerical_crosscheck": self.certified_numerical_crosscheck,
            "certified_physical_experiment": self.certified_physical_experiment,
        }


def run_oak_benchmarks() -> OAKReport:
    results = (
        _jacobi_identity_benchmark(),
        _axis3_solution_benchmark(),
        _axis1_solution_benchmark(),
        _near_separatrix_benchmark(),
        _orientation_benchmark(),
    )
    passed = all(result.passed for result in results)
    return OAKReport(
        status="CERTIFIED_ANALYTIC_COMPUTATIONAL_CORE" if passed else "FAILED_ANALYTIC_COMPUTATIONAL_CORE",
        passed=passed,
        results=results,
        certified_analytic_identities=passed,
        certified_numerical_crosscheck=passed,
    )


def _jacobi_identity_benchmark() -> BenchmarkResult:
    maximum = 0.0
    for m in (0.0, 0.1, 0.5, 0.9, 0.999999):
        for u in (-5.0, -1.3, 0.0, 0.1, 1.0, 2.0, 5.0):
            sn, cn, dn = jacobi_sncndn(u, m)
            maximum = max(maximum, abs(sn * sn + cn * cn - 1.0))
            maximum = max(maximum, abs(dn * dn + m * sn * sn - 1.0))
    tolerance = 5e-13
    return BenchmarkResult(
        benchmark_id="jacobi-identities",
        passed=maximum <= tolerance,
        metric=maximum,
        tolerance=tolerance,
        note="AGM Jacobi functions satisfy both real algebraic identities.",
    )


def _axis3_solution_benchmark() -> BenchmarkResult:
    return _analytic_numeric_benchmark(
        benchmark_id="stable-axis-3-analytic-vs-rk4",
        inertia=PrincipalInertia(1.0, 2.0, 3.0),
        invariants=Invariants(energy=1.8, angular_momentum_squared=9.0),
    )


def _axis1_solution_benchmark() -> BenchmarkResult:
    return _analytic_numeric_benchmark(
        benchmark_id="stable-axis-1-analytic-vs-rk4",
        inertia=PrincipalInertia(1.0, 2.0, 3.0),
        invariants=Invariants(energy=3.6, angular_momentum_squared=9.0),
    )


def _analytic_numeric_benchmark(
    *,
    benchmark_id: str,
    inertia: PrincipalInertia,
    invariants: Invariants,
) -> BenchmarkResult:
    parameters = elliptic_parameters(inertia, invariants)
    times = [parameters.period * index / 32.0 for index in range(33)]
    exact = [analytic_omega(time, parameters) for time in times]
    numerical = integrate_rk4(inertia, exact[0], times)
    maximum = 0.0
    for expected, observed in zip(exact, numerical):
        maximum = max(maximum, max(abs(a - b) for a, b in zip(expected, observed)))
        energy_residual, momentum_residual = invariant_residuals(inertia, expected, invariants)
        maximum = max(maximum, abs(energy_residual), abs(momentum_residual))
    tolerance = 2e-8
    return BenchmarkResult(
        benchmark_id=benchmark_id,
        passed=maximum <= tolerance,
        metric=maximum,
        tolerance=tolerance,
        note="Exact Jacobi branch agrees with an independent small-step RK4 integration.",
    )


def _near_separatrix_benchmark() -> BenchmarkResult:
    m = 1.0 - 1e-10
    exact = complete_elliptic_k(m)
    asymptotic = near_separatrix_period_asymptotic(m)
    relative = abs(exact - asymptotic) / exact
    tolerance = 2e-10
    return BenchmarkResult(
        benchmark_id="separatrix-period-log-divergence",
        passed=relative <= tolerance,
        metric=relative,
        tolerance=tolerance,
        note="K(m) approaches the logarithmic divergence as m tends to one.",
    )


def _orientation_benchmark() -> BenchmarkResult:
    inertia = PrincipalInertia(1.0, 2.0, 3.0)
    invariants = Invariants(energy=1.8, angular_momentum_squared=9.0)
    parameters = elliptic_parameters(inertia, invariants)
    times = [parameters.period * index / 16.0 for index in range(17)]
    omega = lambda time: analytic_omega(time, parameters)
    quaternions = integrate_orientation_quaternion(omega, times)
    maximum = 0.0
    for q in quaternions:
        maximum = max(maximum, abs(sum(value * value for value in q) - 1.0))
        matrix = quaternion_to_matrix(q)
        for row_index in range(3):
            for column_index in range(3):
                dot = sum(matrix[k][row_index] * matrix[k][column_index] for k in range(3))
                target = 1.0 if row_index == column_index else 0.0
                maximum = max(maximum, abs(dot - target))
    tolerance = 5e-12
    return BenchmarkResult(
        benchmark_id="orientation-unit-quaternion-orthogonality",
        passed=isfinite(maximum) and maximum <= tolerance,
        metric=maximum,
        tolerance=tolerance,
        note="Quaternion reconstruction preserves unit norm and SO(3) orthogonality.",
    )
