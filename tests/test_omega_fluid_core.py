import json
from math import exp, pi, sin
from pathlib import Path

from omega_fluid_t.analytics import couette_profile, l2_error, poiseuille_mean_velocity, poiseuille_profile
from omega_fluid_t.dimensionless import DimensionlessInput, compute_dimensionless
from omega_fluid_t.frontier import FrontierWriter, WriterPolicy, default_fluid_space
from omega_fluid_t.oak import run_core_benchmarks
from omega_fluid_t.solvers import solve_diffusion_1d


def test_dimensionless_water_like_case() -> None:
    result = compute_dimensionless(
        DimensionlessInput(
            density=1000.0,
            velocity=2.0,
            length=0.1,
            dynamic_viscosity=1e-3,
            sound_speed=1480.0,
            gravity=9.81,
            surface_tension=0.072,
            thermal_diffusivity=1.4e-7,
            mass_diffusivity=2e-9,
            frequency=20.0,
            mean_free_path=3e-10,
            relaxation_time=1e-3,
        )
    )
    assert abs(result.reynolds - 200000.0) < 1e-9
    assert result.mach is not None and 0 < result.mach < 0.01
    assert result.froude is not None and result.froude > 1.0
    assert result.weber is not None and result.weber > 1000.0
    assert result.prandtl is not None and result.prandtl > 1.0
    assert result.knudsen is not None and result.knudsen < 1e-6


def test_dimensionless_rejects_nonphysical_denominator() -> None:
    try:
        compute_dimensionless(
            DimensionlessInput(density=1.0, velocity=1.0, length=1.0, dynamic_viscosity=0.0)
        )
    except ValueError as exc:
        assert "dynamic_viscosity" in str(exc)
    else:
        raise AssertionError("zero viscosity must be rejected by this guarded input model")


def test_couette_profile_endpoints_and_midpoint() -> None:
    assert couette_profile(0.0, gap=2.0, lower_velocity=1.0, upper_velocity=5.0) == 1.0
    assert couette_profile(1.0, gap=2.0, lower_velocity=1.0, upper_velocity=5.0) == 3.0
    assert couette_profile(2.0, gap=2.0, lower_velocity=1.0, upper_velocity=5.0) == 5.0


def test_poiseuille_profile_is_symmetric_and_matches_mean() -> None:
    left = poiseuille_profile(0.25, gap=1.0, pressure_gradient=-12.0, dynamic_viscosity=2.0)
    right = poiseuille_profile(0.75, gap=1.0, pressure_gradient=-12.0, dynamic_viscosity=2.0)
    assert left == right
    assert poiseuille_profile(0.0, gap=1.0, pressure_gradient=-12.0, dynamic_viscosity=2.0) == 0.0
    assert poiseuille_mean_velocity(gap=1.0, pressure_gradient=-12.0, dynamic_viscosity=2.0) == 0.5


def _diffusion_error(points: int) -> float:
    diffusivity = 0.1
    final_time = 0.05
    result = solve_diffusion_1d(points=points, final_time=final_time, diffusivity=diffusivity)
    exact = [sin(pi * x) * exp(-(pi * pi) * diffusivity * final_time) for x in result.x]
    assert result.cfl_diffusion <= 0.5
    return l2_error(result.values, exact)


def test_diffusion_converges_second_order_in_space_time_coupled() -> None:
    coarse = _diffusion_error(41)
    fine = _diffusion_error(81)
    assert fine < coarse
    assert coarse / fine > 3.0


def test_zero_time_is_identity_with_enforced_boundaries() -> None:
    result = solve_diffusion_1d(points=11, final_time=0.0, diffusivity=0.1)
    assert result.steps == 0
    assert result.values[0] == 0.0
    assert result.values[-1] == 0.0


def test_core_oak_benchmarks_pass_without_physics_certification() -> None:
    report = run_core_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_CORE"
    assert report.certified_physics is False
    assert {result.benchmark_id for result in report.results} == {
        "couette-linear-profile",
        "poiseuille-mean-flow",
        "diffusion-sine-convergence",
    }


def test_epoch_space_is_deterministic_and_has_no_total_cap() -> None:
    space = default_fluid_space()
    assert space.local_cardinality > 10**12
    first = space.genome(0)
    repeated = space.genome(0)
    next_epoch = space.genome(space.local_cardinality)
    assert first.content_hash() == repeated.content_hash()
    assert next_epoch.epoch == 1
    assert next_epoch.local_index == 0
    assert next_epoch.genome_id != first.genome_id
    plan = space.plan(start=space.local_cardinality * 10**6, count=10_000)
    assert plan.virtual_cardinality == "countably_unbounded_by_epoch"
    assert plan.count == 10_000


def test_frontier_writer_materializes_and_resumes(tmp_path: Path) -> None:
    output = tmp_path / "frontier"
    writer = FrontierWriter(output, policy=WriterPolicy(target_shard_bytes=8_000, checkpoint_interval=17))
    first = writer.materialize(default_fluid_space(), start=0, count=125)
    assert first["accepted"] == 125
    assert first["duplicate_ids"] == 0
    assert first["remote_mutations"] == 0
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["next_index"] == 125
    lines = []
    for shard in sorted((output / "shards").glob("*.jsonl")):
        lines.extend(shard.read_text(encoding="utf-8").splitlines())
    assert len(lines) == 125
    records = [json.loads(line) for line in lines]
    assert len({record["genome_id"] for record in records}) == 125
    assert records[-1]["chain_digest"] == manifest["chain_digest"]


def test_frontier_plan_accepts_large_finite_window() -> None:
    plan = default_fluid_space().plan(start=10**18, count=10**7)
    assert plan.start == 10**18
    assert plan.count == 10**7
    assert plan.estimated_jsonl_bytes == 9_000_000_000
