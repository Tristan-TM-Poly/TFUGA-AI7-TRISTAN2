"""R0.5 constellation, coverage and distributed allocation baselines."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import asin, cos, pi, sin, sqrt
from typing import Any, Iterable, Mapping, Sequence


Vector3 = tuple[float, float, float]


def _dot(a: Vector3, b: Vector3) -> float:
    return sum(a[i] * b[i] for i in range(3))


def _norm(a: Vector3) -> float:
    return sqrt(_dot(a, a))


def _subtract(a: Vector3, b: Vector3) -> Vector3:
    return tuple(a[i] - b[i] for i in range(3))  # type: ignore[return-value]


@dataclass(frozen=True)
class WalkerSatellite:
    satellite_id: str
    plane_index: int
    slot_index: int
    radius_m: float
    inclination_rad: float
    raan_rad: float
    phase_rad: float
    mean_motion_rad_s: float
    capacity_units: float = 1.0

    def position(self, epoch_s: float) -> Vector3:
        u = (self.phase_rad + self.mean_motion_rad_s * epoch_s) % (2.0 * pi)
        co, so = cos(self.raan_rad), sin(self.raan_rad)
        ci, si = cos(self.inclination_rad), sin(self.inclination_rad)
        cu, su = cos(u), sin(u)
        return (
            self.radius_m * (co * cu - so * su * ci),
            self.radius_m * (so * cu + co * su * ci),
            self.radius_m * (su * si),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GroundTarget:
    target_id: str
    latitude_rad: float
    longitude_rad: float
    minimum_elevation_rad: float = 0.0
    priority: float = 1.0

    def validate(self) -> None:
        if not self.target_id:
            raise ValueError("target id cannot be empty")
        if not -0.5 * pi <= self.latitude_rad <= 0.5 * pi:
            raise ValueError("invalid target latitude")
        if not -pi <= self.longitude_rad <= pi:
            raise ValueError("invalid target longitude")
        if not 0.0 <= self.minimum_elevation_rad < 0.5 * pi:
            raise ValueError("invalid minimum elevation")
        if self.priority <= 0.0:
            raise ValueError("target priority must be positive")


@dataclass(frozen=True)
class ObservationTask:
    task_id: str
    target_id: str
    epoch_s: float
    demand_units: float
    priority: float = 1.0

    def validate(self) -> None:
        if not self.task_id or not self.target_id:
            raise ValueError("task and target ids cannot be empty")
        if self.epoch_s < 0.0 or self.demand_units <= 0.0 or self.priority <= 0.0:
            raise ValueError("invalid task timing, demand or priority")


@dataclass(frozen=True)
class TaskAssignment:
    task_id: str
    satellite_id: str | None
    score: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def walker_delta_constellation(
    *,
    total_satellites: int,
    planes: int,
    phasing: int,
    body_radius_m: float,
    altitude_m: float,
    inclination_rad: float,
    mu_m3_s2: float,
    capacity_units: float = 1.0,
) -> tuple[WalkerSatellite, ...]:
    if total_satellites <= 0 or planes <= 0 or total_satellites % planes != 0:
        raise ValueError("total satellites must be positive and divisible by planes")
    if body_radius_m <= 0.0 or altitude_m <= 0.0 or mu_m3_s2 <= 0.0:
        raise ValueError("body, altitude and mu must be positive")
    slots = total_satellites // planes
    radius = body_radius_m + altitude_m
    mean_motion = sqrt(mu_m3_s2 / radius**3)
    satellites: list[WalkerSatellite] = []
    for plane in range(planes):
        raan = 2.0 * pi * plane / planes
        for slot in range(slots):
            phase = 2.0 * pi * slot / slots + 2.0 * pi * phasing * plane / total_satellites
            satellites.append(
                WalkerSatellite(
                    satellite_id=f"sat-p{plane:02d}-s{slot:02d}",
                    plane_index=plane,
                    slot_index=slot,
                    radius_m=radius,
                    inclination_rad=inclination_rad,
                    raan_rad=raan,
                    phase_rad=phase % (2.0 * pi),
                    mean_motion_rad_s=mean_motion,
                    capacity_units=capacity_units,
                )
            )
    return tuple(satellites)


def target_position_inertial(
    target: GroundTarget,
    epoch_s: float,
    body_radius_m: float,
    body_rotation_rad_s: float,
) -> Vector3:
    target.validate()
    longitude = target.longitude_rad + body_rotation_rad_s * epoch_s
    cl = cos(target.latitude_rad)
    return (
        body_radius_m * cl * cos(longitude),
        body_radius_m * cl * sin(longitude),
        body_radius_m * sin(target.latitude_rad),
    )


def elevation_angle_rad(
    satellite_position_m: Vector3,
    target_position_m: Vector3,
) -> float:
    line = _subtract(satellite_position_m, target_position_m)
    sine_elevation = _dot(line, target_position_m) / (_norm(line) * _norm(target_position_m))
    return asin(max(-1.0, min(1.0, sine_elevation)))


def visible_satellites(
    constellation: Sequence[WalkerSatellite],
    target: GroundTarget,
    epoch_s: float,
    body_radius_m: float,
    body_rotation_rad_s: float,
) -> tuple[tuple[WalkerSatellite, float], ...]:
    target_position = target_position_inertial(target, epoch_s, body_radius_m, body_rotation_rad_s)
    visible = [
        (satellite, elevation_angle_rad(satellite.position(epoch_s), target_position))
        for satellite in constellation
    ]
    return tuple(
        sorted(
            (item for item in visible if item[1] >= target.minimum_elevation_rad),
            key=lambda item: (-item[1], item[0].satellite_id),
        )
    )


def sample_coverage(
    constellation: Sequence[WalkerSatellite],
    targets: Sequence[GroundTarget],
    *,
    duration_s: float,
    step_s: float,
    body_radius_m: float,
    body_rotation_rad_s: float,
) -> dict[str, Any]:
    if not constellation or not targets:
        raise ValueError("coverage requires satellites and targets")
    if duration_s <= 0.0 or step_s <= 0.0:
        raise ValueError("coverage duration and step must be positive")
    for target in targets:
        target.validate()
    epochs: list[float] = []
    t = 0.0
    while t < duration_s - 1e-12:
        epochs.append(t)
        t += step_s
    epochs.append(duration_s)

    target_reports: dict[str, Any] = {}
    weighted_visible = 0.0
    weighted_total = 0.0
    for target in targets:
        visibility = [
            bool(
                visible_satellites(
                    constellation,
                    target,
                    epoch,
                    body_radius_m,
                    body_rotation_rad_s,
                )
            )
            for epoch in epochs
        ]
        visible_count = sum(visibility)
        weighted_visible += target.priority * visible_count
        weighted_total += target.priority * len(epochs)
        longest_gap_samples = 0
        current_gap = 0
        for is_visible in visibility:
            if is_visible:
                longest_gap_samples = max(longest_gap_samples, current_gap)
                current_gap = 0
            else:
                current_gap += 1
        longest_gap_samples = max(longest_gap_samples, current_gap)
        target_reports[target.target_id] = {
            "visible_fraction": visible_count / len(epochs),
            "visible_samples": visible_count,
            "total_samples": len(epochs),
            "maximum_sampled_gap_s": longest_gap_samples * step_s,
        }
    return {
        "duration_s": duration_s,
        "step_s": step_s,
        "sample_count": len(epochs),
        "weighted_coverage_fraction": weighted_visible / weighted_total,
        "targets": target_reports,
        "operational_coverage_claimed": False,
    }


def segment_clear_of_body(
    position_a_m: Vector3,
    position_b_m: Vector3,
    body_radius_m: float,
    clearance_m: float = 0.0,
) -> bool:
    segment = _subtract(position_b_m, position_a_m)
    denominator = _dot(segment, segment)
    if denominator == 0.0:
        return _norm(position_a_m) > body_radius_m + clearance_m
    t = max(0.0, min(1.0, -_dot(position_a_m, segment) / denominator))
    closest = tuple(position_a_m[i] + t * segment[i] for i in range(3))
    return _norm(closest) > body_radius_m + clearance_m


def intersatellite_graph(
    constellation: Sequence[WalkerSatellite],
    *,
    epoch_s: float,
    maximum_range_m: float,
    body_radius_m: float,
    clearance_m: float = 0.0,
) -> dict[str, tuple[str, ...]]:
    if maximum_range_m <= 0.0:
        raise ValueError("maximum intersatellite range must be positive")
    positions = {satellite.satellite_id: satellite.position(epoch_s) for satellite in constellation}
    adjacency = {satellite.satellite_id: set() for satellite in constellation}
    for index, left in enumerate(constellation):
        for right in constellation[index + 1 :]:
            distance = _norm(_subtract(positions[left.satellite_id], positions[right.satellite_id]))
            if (
                distance <= maximum_range_m
                and segment_clear_of_body(
                    positions[left.satellite_id],
                    positions[right.satellite_id],
                    body_radius_m,
                    clearance_m,
                )
            ):
                adjacency[left.satellite_id].add(right.satellite_id)
                adjacency[right.satellite_id].add(left.satellite_id)
    return {node: tuple(sorted(neighbors)) for node, neighbors in sorted(adjacency.items())}


def connected_components(adjacency: Mapping[str, Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    remaining = set(adjacency)
    components: list[tuple[str, ...]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        visited: set[str] = set()
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            stack.extend(neighbor for neighbor in adjacency[node] if neighbor not in visited)
        remaining.difference_update(visited)
        components.append(tuple(sorted(visited)))
    return tuple(sorted(components, key=lambda component: (-len(component), component)))


def allocate_tasks(
    constellation: Sequence[WalkerSatellite],
    targets: Mapping[str, GroundTarget],
    tasks: Sequence[ObservationTask],
    *,
    body_radius_m: float,
    body_rotation_rad_s: float,
    unavailable_satellites: Iterable[str] = (),
) -> tuple[TaskAssignment, ...]:
    unavailable = set(unavailable_satellites)
    remaining_capacity = {
        satellite.satellite_id: satellite.capacity_units
        for satellite in constellation
        if satellite.satellite_id not in unavailable
    }
    assignments: list[TaskAssignment] = []
    ordered_tasks = sorted(tasks, key=lambda task: (-task.priority, task.epoch_s, task.task_id))
    for task in ordered_tasks:
        task.validate()
        if task.target_id not in targets:
            raise ValueError(f"unknown task target: {task.target_id}")
        candidates = visible_satellites(
            [satellite for satellite in constellation if satellite.satellite_id in remaining_capacity],
            targets[task.target_id],
            task.epoch_s,
            body_radius_m,
            body_rotation_rad_s,
        )
        feasible = [
            (satellite, elevation)
            for satellite, elevation in candidates
            if remaining_capacity[satellite.satellite_id] >= task.demand_units
        ]
        if not feasible:
            assignments.append(TaskAssignment(task.task_id, None, 0.0, "no-visible-capable-satellite"))
            continue
        satellite, elevation = max(
            feasible,
            key=lambda item: (
                item[1] + 1e-6 * remaining_capacity[item[0].satellite_id],
                item[0].satellite_id,
            ),
        )
        remaining_capacity[satellite.satellite_id] -= task.demand_units
        assignments.append(TaskAssignment(task.task_id, satellite.satellite_id, elevation, "assigned"))
    return tuple(sorted(assignments, key=lambda assignment: assignment.task_id))


def migrate_functions(
    function_demands: Mapping[str, float],
    node_capacities: Mapping[str, float],
    *,
    failed_nodes: Iterable[str] = (),
) -> dict[str, Any]:
    failed = set(failed_nodes)
    remaining = {node: capacity for node, capacity in node_capacities.items() if node not in failed}
    assignment: dict[str, str] = {}
    unassigned: list[str] = []
    for function_id, demand in sorted(function_demands.items(), key=lambda item: (-item[1], item[0])):
        if demand <= 0.0:
            raise ValueError("function demand must be positive")
        candidates = [(capacity, node) for node, capacity in remaining.items() if capacity >= demand]
        if not candidates:
            unassigned.append(function_id)
            continue
        _, selected = max(candidates)
        assignment[function_id] = selected
        remaining[selected] -= demand
    return {
        "assignment": dict(sorted(assignment.items())),
        "unassigned": sorted(unassigned),
        "remaining_capacity": dict(sorted(remaining.items())),
        "graceful": not unassigned,
    }


def replenishment_plan(
    constellation: Sequence[WalkerSatellite],
    failed_satellites: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    failed = set(failed_satellites)
    return tuple(
        {
            "satellite_id": satellite.satellite_id,
            "plane_index": satellite.plane_index,
            "slot_index": satellite.slot_index,
            "target_raan_rad": satellite.raan_rad,
            "target_phase_rad": satellite.phase_rad,
            "replacement_required": True,
        }
        for satellite in constellation
        if satellite.satellite_id in failed
    )
