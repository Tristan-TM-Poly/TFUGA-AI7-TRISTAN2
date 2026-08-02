from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp, pi
from typing import Any

from .analytics import couette_profile, l2_error, poiseuille_mean_velocity, poiseuille_profile
from .conservation import ConservationBudget
from .solvers import solve_diffusion_1d


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    passed: bool
    metrics: dict[str, float]
    thresholds: dict[str, float]
    status: str
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["limitations"] = list(self.limitations)
        return payload


@dataclass(frozen=True)
class OAKBenchmarkReport:
    status: str
    results: tuple[BenchmarkResult, ...]
    scientific_claim: str
    certified_physics: bool = False

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "certified_physics": self.certified_physics,
            "scientific_claim": self.scientific_claim,
            "results": [item.to_dict() for item in self.results],
        }


def _couette_benchmark() -> BenchmarkResult:
    samples = [couette_profile(i / 10, gap=1.0, upper_velocity=2.0) for i in range(11)]
    reference = [2.0 * i / 10 for i in range(11)]
    error = max(abs(a - b) for a, b in zip(samples, reference, strict=True))
    return BenchmarkResult(
        benchmark_id="couette-linear-profile",
        passed=error <= 1e-14,
        metrics={"max_abs_error": error},
        thresholds={"max_abs_error": 1e-14},
        status="analytic_identity",
    )


def _poiseuille_benchmark() -> BenchmarkResult:
    gap = 1.0
    mu = 2.0
    dpdx = -12.0
    points = 4001
    dx = gap / (points - 1)
    values = [poiseuille_profile(i * dx, gap=gap, pressure_gradient=dpdx, dynamic_viscosity=mu) for i in range(points)]
    numerical_mean = dx * (0.5 * values[0] + sum(values[1:-1]) + 0.5 * values[-1]) / gap
    exact_mean = poiseuille_mean_velocity(gap=gap, pressure_gradient=dpdx, dynamic_viscosity=mu)
    relative_error = abs(numerical_mean - exact_mean) / abs(exact_mean)
    return BenchmarkResult(
        benchmark_id="poiseuille-mean-flow",
        passed=relative_error <= 1e-6,
        metrics={"relative_error": relative_error, "numerical_mean": numerical_mean, "exact_mean": exact_mean},
        thresholds={"relative_error": 1e-6},
        status="analytic_quadrature_check",
    )


def _diffusion_benchmark() -> BenchmarkResult:
    diffusivity = 0.1
    final_time = 0.05
    coarse = solve_diffusion_1d(points=41, final_time=final_time, diffusivity=diffusivity)
    fine = solve_diffusion_1d(points=81, final_time=final_time, diffusivity=diffusivity)

    def exact(result: Any) -> list[float]:
        damping = exp(-(pi * pi) * diffusivity * final_time)
        return [__import__("math").sin(pi * position) * damping for position in result.x]

    coarse_error = l2_error(coarse.values, exact(coarse))
    fine_error = l2_error(fine.values, exact(fine))
    convergence_ratio = coarse_error / max(fine_error, 1e-300)
    budget = ConservationBudget(
        initial=fine.initial_mass,
        final=fine.final_mass,
        integrated_boundary_flux=fine.initial_mass - fine.final_mass,
    )
    passed = fine_error < coarse_error and convergence_ratio > 3.0 and abs(budget.residual) < 1e-12
    return BenchmarkResult(
        benchmark_id="diffusion-sine-convergence",
        passed=passed,
        metrics={
            "coarse_l2_error": coarse_error,
            "fine_l2_error": fine_error,
            "convergence_ratio": convergence_ratio,
            "diffusion_cfl": fine.cfl_diffusion,
            "budget_residual": budget.residual,
        },
        thresholds={
            "convergence_ratio_min": 3.0,
            "budget_abs_residual_max": 1e-12,
        },
        status="numerical_convergence_check",
        limitations=(
            "One-dimensional linear diffusion only.",
            "Passing does not certify Navier-Stokes, turbulence or experimental physics.",
        ),
    )


def run_core_benchmarks() -> OAKBenchmarkReport:
    results = (_couette_benchmark(), _poiseuille_benchmark(), _diffusion_benchmark())
    passed = all(item.passed for item in results)
    return OAKBenchmarkReport(
        status="CERTIFIED_COMPUTATIONAL_CORE" if passed else "FAILED_OAK_GATE",
        results=results,
        scientific_claim=(
            "The compact analytic and one-dimensional numerical kernels reproduce their declared baselines within stated tolerances."
            if passed
            else "At least one declared baseline was not reproduced within tolerance."
        ),
        certified_physics=False,
    )
