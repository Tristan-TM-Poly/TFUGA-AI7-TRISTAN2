"""R0.3 tests for active benchmarking and inverse resource design."""

from __future__ import annotations

import pytest

from omega_compute_physics_t.active import (
    discriminating_experiment,
    geometric_design_space,
    rank_experiments,
    select_next_experiments,
)
from omega_compute_physics_t.atlas import ResourceSample, fit_resource_model
from omega_compute_physics_t.budget import (
    ResourceConstraint,
    compile_budget,
    pareto_front,
    quality_per_cost,
)


def _fit(values, target: str, degree: int = 2):
    samples = [
        ResourceSample(
            variables={"n": float(n)},
            resources={target: float(value)},
            metadata={"campaign": "r03-test"},
        )
        for n, value in values
    ]
    return fit_resource_model(
        samples,
        target,
        max_total_degree=degree,
        include_logs=False,
        include_xlogx=False,
    )


def test_geometric_design_space_is_bounded() -> None:
    points = geometric_design_space({"a": (1.0, 100.0), "b": (2.0, 200.0)}, levels=3)
    assert len(points) == 9
    assert points[0]["a"] > 0
    with pytest.raises(ValueError):
        geometric_design_space(
            {"a": (1.0, 10.0), "b": (1.0, 10.0), "c": (1.0, 10.0)},
            levels=20,
            max_points=1000,
        )


def test_discriminating_experiment_moves_to_model_disagreement() -> None:
    linear = _fit([(n, n) for n in range(1, 31)], "wall_time_s")
    curved = _fit(
        [(n, n + 0.02 * n * n) for n in range(1, 31)],
        "wall_time_s",
    )
    candidates = [{"n": float(n)} for n in range(2, 31)]
    selected = discriminating_experiment(linear, curved, candidates)
    assert selected.point["n"] >= 25.0
    assert selected.disagreement > 0.0


def test_active_batch_uses_novelty_and_diversity() -> None:
    model = _fit([(n, n) for n in range(1, 21)], "wall_time_s")
    existing = [
        ResourceSample(
            variables={"n": float(n)},
            resources={"wall_time_s": float(n)},
        )
        for n in (1, 2, 4, 8)
    ]
    candidates = [{"n": float(n)} for n in (1, 2, 4, 8, 16, 32, 64)]
    ranked = rank_experiments(
        (model,),
        candidates,
        existing_samples=existing,
        disagreement_weight=0.0,
        novelty_weight=1.0,
        cost_power=0.0,
    )
    assert ranked[0].point["n"] in {32.0, 64.0}
    chosen = select_next_experiments(
        (model,),
        candidates,
        existing_samples=existing,
        count=2,
        min_log_distance=0.5,
        disagreement_weight=0.0,
        novelty_weight=1.0,
        cost_power=0.0,
    )
    assert len(chosen) == 2
    assert chosen[0].point != chosen[1].point


def test_budget_compiler_selects_best_robust_feasible_quality() -> None:
    wall = _fit([(n, n) for n in range(1, 11)], "wall_time_s", degree=1)
    memory = _fit([(n, 2 * n) for n in range(1, 11)], "memory_mb", degree=1)
    quality = _fit([(n, n) for n in range(1, 11)], "quality", degree=1)
    candidates = [{"n": float(n)} for n in range(1, 11)]

    report = compile_budget(
        {
            "wall_time_s": wall,
            "memory_mb": memory,
            "quality": quality,
        },
        candidates,
        constraints=(
            ResourceConstraint("wall_time_s", upper=6.0),
            ResourceConstraint("memory_mb", upper=10.0),
        ),
        uncertainty_radii={"memory_mb": 1.5},
        objective_target="quality",
        objective_direction="maximize",
    )
    assert report.best is not None
    assert abs(report.best.point["n"] - 4.0) < 1e-6
    assert report.best.feasible


def test_pareto_front_removes_dominated_large_n_region() -> None:
    wall = _fit([(n, n) for n in range(1, 10)], "wall_time_s", degree=1)
    quality = _fit(
        [(n, -((n - 5) ** 2)) for n in range(1, 10)],
        "quality",
        degree=2,
    )
    candidates = [{"n": float(n)} for n in range(1, 10)]
    front = pareto_front(
        {"wall_time_s": wall, "quality": quality},
        candidates,
        objectives={"wall_time_s": "minimize", "quality": "maximize"},
    )
    values = {round(item.point["n"]) for item in front}
    assert values == {1, 2, 3, 4, 5}


def test_quality_per_cost_is_explicit_scalarization() -> None:
    assert quality_per_cost(
        10.0,
        {"time": 2.0, "energy": 3.0},
        weights={"time": 2.0, "energy": 1.0},
    ) == 10.0 / 7.0
