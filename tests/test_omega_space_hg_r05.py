from __future__ import annotations

from math import radians

import pytest

from omega_space_hg_t.constellation import (
    ObservationTask,
    allocate_tasks,
    connected_components,
    intersatellite_graph,
    migrate_functions,
    replenishment_plan,
    sample_coverage,
    segment_clear_of_body,
    walker_delta_constellation,
)
from omega_space_hg_t.r05 import (
    EARTH_MU_M3_S2,
    EARTH_RADIUS_M,
    EARTH_ROTATION_RAD_S,
    canonical_constellation,
    canonical_targets,
    run_r05_oak_benchmarks,
    simulate_r05_constellation,
)


def test_walker_delta_has_unique_ids_planes_and_slots() -> None:
    constellation = canonical_constellation()
    assert len(constellation) == 24
    assert len({satellite.satellite_id for satellite in constellation}) == 24
    assert len({satellite.plane_index for satellite in constellation}) == 6
    assert all(satellite.radius_m > EARTH_RADIUS_M for satellite in constellation)


def test_walker_requires_divisibility() -> None:
    with pytest.raises(ValueError):
        walker_delta_constellation(
            total_satellites=10,
            planes=3,
            phasing=1,
            body_radius_m=EARTH_RADIUS_M,
            altitude_m=500_000.0,
            inclination_rad=radians(45.0),
            mu_m3_s2=EARTH_MU_M3_S2,
        )


def test_dense_constellation_sampled_coverage_is_not_worse() -> None:
    targets = canonical_targets()
    sparse = canonical_constellation(12)
    dense = canonical_constellation(24)
    kwargs = dict(
        targets=targets,
        duration_s=6 * 3600.0,
        step_s=180.0,
        body_radius_m=EARTH_RADIUS_M,
        body_rotation_rad_s=EARTH_ROTATION_RAD_S,
    )
    sparse_report = sample_coverage(sparse, **kwargs)
    dense_report = sample_coverage(dense, **kwargs)
    assert dense_report["weighted_coverage_fraction"] >= sparse_report["weighted_coverage_fraction"]


def test_segment_visibility_blocks_earth_occultation() -> None:
    radius = EARTH_RADIUS_M + 550_000.0
    assert segment_clear_of_body(
        (radius, 0.0, 0.0),
        (0.0, radius, 0.0),
        EARTH_RADIUS_M,
    ) is False
    assert segment_clear_of_body(
        (radius, 0.0, 0.0),
        (radius, 1000.0, 0.0),
        EARTH_RADIUS_M,
    ) is True


def test_intersatellite_graph_is_symmetric() -> None:
    constellation = canonical_constellation(12)
    graph = intersatellite_graph(
        constellation,
        epoch_s=0.0,
        maximum_range_m=6_000_000.0,
        body_radius_m=EARTH_RADIUS_M,
    )
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            assert node in graph[neighbor]
    assert sum(len(neighbors) for neighbors in graph.values()) % 2 == 0


def test_connected_components_partition_nodes() -> None:
    adjacency = {
        "a": ("b",),
        "b": ("a",),
        "c": (),
        "d": ("e",),
        "e": ("d",),
    }
    components = connected_components(adjacency)
    assert {node for component in components for node in component} == set(adjacency)
    assert sorted(len(component) for component in components) == [1, 2, 2]


def test_task_allocation_respects_visibility_capacity_and_failures() -> None:
    constellation = canonical_constellation()
    target = canonical_targets()[0]
    tasks = (
        ObservationTask("task-a", target.target_id, 0.0, 1.0, 2.0),
        ObservationTask("task-b", target.target_id, 0.0, 4.0, 1.0),
    )
    assignments = allocate_tasks(
        constellation,
        {target.target_id: target},
        tasks,
        body_radius_m=EARTH_RADIUS_M,
        body_rotation_rad_s=EARTH_ROTATION_RAD_S,
    )
    assert [assignment.task_id for assignment in assignments] == ["task-a", "task-b"]
    assert all(
        assignment.reason in ("assigned", "no-visible-capable-satellite")
        for assignment in assignments
    )


def test_function_migration_exposes_insufficient_capacity() -> None:
    report = migrate_functions(
        {"a": 2.0, "b": 2.0, "c": 1.0},
        {"node-1": 3.0, "node-2": 3.0},
        failed_nodes=("node-1",),
    )
    assert report["graceful"] is False
    assert len(report["unassigned"]) == 1
    assert set(report["assignment"]) in ({"a", "c"}, {"b", "c"})


def test_replenishment_matches_failed_slots() -> None:
    constellation = canonical_constellation()
    failed = (constellation[0].satellite_id, constellation[7].satellite_id)
    plan = replenishment_plan(constellation, failed)
    assert len(plan) == 2
    assert {item["satellite_id"] for item in plan} == set(failed)


def test_degraded_constellation_retains_nonzero_sampled_coverage() -> None:
    failed = tuple(satellite.satellite_id for satellite in canonical_constellation()[:3])
    report = simulate_r05_constellation(
        duration_hours=6.0,
        step_s=180.0,
        failed_satellites=failed,
    )
    assert report["active_satellite_count"] == 21
    assert report["coverage"]["weighted_coverage_fraction"] > 0.0
    assert len(report["replenishment"]) == 3
    assert report["collision_safety_claimed"] is False


def test_r05_simulation_replays_exactly() -> None:
    failed = ("sat-p00-s00", "sat-p01-s00")
    first = simulate_r05_constellation(
        duration_hours=3.0,
        step_s=180.0,
        failed_satellites=failed,
    )
    second = simulate_r05_constellation(
        duration_hours=3.0,
        step_s=180.0,
        failed_satellites=failed,
    )
    assert first["coverage"] == second["coverage"]
    assert first["network"] == second["network"]
    assert first["tasks"] == second["tasks"]


def test_r05_oakbench_passes_research_fixtures_only() -> None:
    report = run_r05_oak_benchmarks()
    assert report["passed"] is True
    assert len(report["checks"]) >= 7
    assert report["flight_qualified_claimed"] is False
    assert report["operational_coverage_claimed"] is False
    assert report["collision_safety_claimed"] is False
    assert report["autonomous_servicing_claimed"] is False
