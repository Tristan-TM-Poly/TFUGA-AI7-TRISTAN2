"""Ω-SPACE-HG-T∞ R0.5 constellation and mycelial operations laboratory."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import radians
from typing import Any, Callable

from .constellation import (
    GroundTarget,
    ObservationTask,
    allocate_tasks,
    connected_components,
    intersatellite_graph,
    migrate_functions,
    replenishment_plan,
    sample_coverage,
    walker_delta_constellation,
)


EARTH_RADIUS_M = 6_378_137.0
EARTH_MU_M3_S2 = 3.986004418e14
EARTH_ROTATION_RAD_S = 7.2921150e-5


@dataclass(frozen=True)
class R05Check:
    name: str
    passed: bool
    observed: Any
    criterion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_constellation(total_satellites: int = 24):
    planes = 6 if total_satellites % 6 == 0 else 4
    return walker_delta_constellation(
        total_satellites=total_satellites,
        planes=planes,
        phasing=1,
        body_radius_m=EARTH_RADIUS_M,
        altitude_m=550_000.0,
        inclination_rad=radians(53.0),
        mu_m3_s2=EARTH_MU_M3_S2,
        capacity_units=4.0,
    )


def canonical_targets() -> tuple[GroundTarget, ...]:
    return (
        GroundTarget("montreal", radians(45.5019), radians(-73.5674), radians(10.0), 1.2),
        GroundTarget("equator-atlantic", radians(0.0), radians(-30.0), radians(10.0), 1.0),
        GroundTarget("north-pacific", radians(40.0), radians(170.0), radians(10.0), 0.9),
        GroundTarget("south-indian", radians(-30.0), radians(80.0), radians(10.0), 0.9),
    )


def simulate_r05_constellation(
    *,
    duration_hours: float = 24.0,
    step_s: float = 120.0,
    failed_satellites: tuple[str, ...] = (),
) -> dict[str, Any]:
    constellation = canonical_constellation()
    active = tuple(
        satellite
        for satellite in constellation
        if satellite.satellite_id not in set(failed_satellites)
    )
    targets = canonical_targets()
    coverage = sample_coverage(
        active,
        targets,
        duration_s=duration_hours * 3600.0,
        step_s=step_s,
        body_radius_m=EARTH_RADIUS_M,
        body_rotation_rad_s=EARTH_ROTATION_RAD_S,
    )
    graph = intersatellite_graph(
        active,
        epoch_s=0.0,
        maximum_range_m=5_500_000.0,
        body_radius_m=EARTH_RADIUS_M,
        clearance_m=10_000.0,
    )
    components = connected_components(graph)
    tasks = tuple(
        ObservationTask(
            task_id=f"task-{index:03d}",
            target_id=target.target_id,
            epoch_s=1800.0 * index,
            demand_units=1.0,
            priority=target.priority,
        )
        for index, target in enumerate(targets * 3)
    )
    assignments = allocate_tasks(
        active,
        {target.target_id: target for target in targets},
        tasks,
        body_radius_m=EARTH_RADIUS_M,
        body_rotation_rad_s=EARTH_ROTATION_RAD_S,
    )
    assigned = sum(assignment.satellite_id is not None for assignment in assignments)
    functions = {
        "orbit-determination": 1.5,
        "time-service": 1.0,
        "routing": 1.0,
        "science-planning": 2.0,
        "anomaly-triage": 1.5,
    }
    capacities = {satellite.satellite_id: 3.0 for satellite in constellation[:8]}
    migration = migrate_functions(functions, capacities, failed_nodes=failed_satellites)
    return {
        "release": "R0.5",
        "nominal_satellite_count": len(constellation),
        "active_satellite_count": len(active),
        "failed_satellites": list(failed_satellites),
        "coverage": coverage,
        "network": {
            "node_count": len(graph),
            "edge_count": sum(len(neighbors) for neighbors in graph.values()) // 2,
            "component_count": len(components),
            "largest_component_size": len(components[0]) if components else 0,
            "components": [list(component) for component in components],
        },
        "tasks": {
            "requested": len(tasks),
            "assigned": assigned,
            "assignment_fraction": assigned / len(tasks),
            "assignments": [assignment.to_dict() for assignment in assignments],
        },
        "function_migration": migration,
        "replenishment": list(replenishment_plan(constellation, failed_satellites)),
        "operational_coverage_claimed": False,
        "collision_safety_claimed": False,
        "autonomous_servicing_claimed": False,
        "flight_qualified_claimed": False,
    }


def _capture(name: str, criterion: str, function: Callable[[], tuple[bool, Any]]) -> R05Check:
    try:
        passed, observed = function()
        return R05Check(name, bool(passed), observed, criterion)
    except Exception as error:
        return R05Check(name, False, f"{type(error).__name__}: {error}", criterion)


def run_r05_oak_benchmarks() -> dict[str, Any]:
    def walker_check() -> tuple[bool, Any]:
        constellation = canonical_constellation()
        ids = {satellite.satellite_id for satellite in constellation}
        planes = {satellite.plane_index for satellite in constellation}
        return len(constellation) == 24 and len(ids) == 24 and len(planes) == 6, {
            "satellites": len(constellation),
            "unique_ids": len(ids),
            "planes": len(planes),
        }

    def coverage_monotonicity_check() -> tuple[bool, Any]:
        targets = canonical_targets()
        sparse = canonical_constellation(12)
        dense = canonical_constellation(24)
        sparse_report = sample_coverage(
            sparse,
            targets,
            duration_s=6 * 3600.0,
            step_s=180.0,
            body_radius_m=EARTH_RADIUS_M,
            body_rotation_rad_s=EARTH_ROTATION_RAD_S,
        )
        dense_report = sample_coverage(
            dense,
            targets,
            duration_s=6 * 3600.0,
            step_s=180.0,
            body_radius_m=EARTH_RADIUS_M,
            body_rotation_rad_s=EARTH_ROTATION_RAD_S,
        )
        observed = {
            "sparse": sparse_report["weighted_coverage_fraction"],
            "dense": dense_report["weighted_coverage_fraction"],
        }
        return observed["dense"] >= observed["sparse"], observed

    def network_check() -> tuple[bool, Any]:
        report = simulate_r05_constellation(duration_hours=6.0, step_s=180.0)
        network = report["network"]
        return network["largest_component_size"] >= 0.75 * network["node_count"], network

    def graceful_degradation_check() -> tuple[bool, Any]:
        nominal = simulate_r05_constellation(duration_hours=6.0, step_s=180.0)
        failed_ids = tuple(satellite.satellite_id for satellite in canonical_constellation()[:3])
        degraded = simulate_r05_constellation(
            duration_hours=6.0,
            step_s=180.0,
            failed_satellites=failed_ids,
        )
        observed = {
            "nominal_coverage": nominal["coverage"]["weighted_coverage_fraction"],
            "degraded_coverage": degraded["coverage"]["weighted_coverage_fraction"],
            "degraded_active": degraded["active_satellite_count"],
            "replacements": len(degraded["replenishment"]),
        }
        return (
            observed["degraded_coverage"] > 0.0
            and observed["degraded_active"] == 21
            and observed["replacements"] == 3
        ), observed

    def deterministic_replay_check() -> tuple[bool, Any]:
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
        keys = ("coverage", "network", "tasks", "function_migration", "replenishment")
        return all(first[key] == second[key] for key in keys), {
            "coverage": first["coverage"]["weighted_coverage_fraction"],
            "assigned": first["tasks"]["assigned"],
            "components": first["network"]["component_count"],
        }

    def migration_check() -> tuple[bool, Any]:
        report = migrate_functions(
            {"a": 2.0, "b": 2.0, "c": 1.0},
            {"node-1": 3.0, "node-2": 3.0},
            failed_nodes=("node-1",),
        )
        return report["graceful"] is False and len(report["unassigned"]) == 1, report

    def boundary_check() -> tuple[bool, Any]:
        boundaries = {
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
            "flight_qualified_claimed": False,
            "operational_coverage_claimed": False,
            "collision_safety_claimed": False,
            "autonomous_servicing_claimed": False,
        }
        return not any(boundaries.values()), boundaries

    checks = (
        _capture("walker_structure", "24 unique satellites occupy six planes", walker_check),
        _capture(
            "sampled_coverage_monotonicity",
            "24-satellite sampled coverage is no worse than 12-satellite coverage",
            coverage_monotonicity_check,
        ),
        _capture(
            "intersatellite_connectivity",
            "largest canonical component contains at least 75% of nodes",
            network_check,
        ),
        _capture(
            "graceful_coverage_degradation",
            "three failures retain nonzero coverage and generate three replacements",
            graceful_degradation_check,
        ),
        _capture(
            "constellation_deterministic_replay",
            "coverage network tasks migration and replenishment replay exactly",
            deterministic_replay_check,
        ),
        _capture(
            "function_capacity_gate",
            "insufficient surviving capacity leaves functions explicitly unassigned",
            migration_check,
        ),
        _capture(
            "r05_claim_boundaries",
            "no proof validation flight coverage collision or servicing claim",
            boundary_check,
        ),
    )
    return {
        "suite": "OMEGA-SPACE-HG-T-R0.5-OAKBench",
        "passed": all(check.passed for check in checks),
        "checks": [check.to_dict() for check in checks],
        "theorem_claimed": False,
        "scientific_validation_claimed": False,
        "flight_qualified_claimed": False,
        "operational_coverage_claimed": False,
        "collision_safety_claimed": False,
        "autonomous_servicing_claimed": False,
        "limitations": [
            "circular analytical Walker geometry without perturbation or orbit-estimation uncertainty",
            "sampled spherical-Earth coverage can miss short visibility transitions",
            "intersatellite links use range and body-clearance geometry only",
            "task allocation is a deterministic greedy baseline without slew power data or schedule coupling",
            "function migration uses scalar capacity and omits software compatibility timing and security",
            "replenishment records failed slots but does not design launch transfer or collision-safe insertion",
        ],
    }
