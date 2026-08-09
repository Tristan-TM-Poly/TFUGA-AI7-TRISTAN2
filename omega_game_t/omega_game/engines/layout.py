from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


Coordinate = tuple[int, int]


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _coord(value: Any, context: str) -> Coordinate:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{context} must be a two-item coordinate")
    return (int(value[0]), int(value[1]))


@dataclass(frozen=True)
class LayoutAudit:
    accepted: bool
    flags: tuple[str, ...]
    connected_spawns: bool
    resources_reachable_by_both: bool
    spawn_distance: int | None
    left_mean_resource_distance: float | None
    right_mean_resource_distance: float | None
    resource_distance_asymmetry: float
    fairness_threshold: float
    layout_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArenaLayout:
    width: int
    height: int
    left_spawn: Coordinate
    right_spawn: Coordinate
    resources: tuple[Coordinate, ...] = ()
    obstacles: tuple[Coordinate, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ArenaLayout":
        allowed = {"width", "height", "left_spawn", "right_spawn", "resources", "obstacles"}
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise ValueError(f"unknown layout fields: {','.join(unknown)}")
        for required in ("width", "height", "left_spawn", "right_spawn"):
            if required not in data:
                raise ValueError(f"layout.{required} is required")
        resources_raw = data.get("resources", [])
        obstacles_raw = data.get("obstacles", [])
        if not isinstance(resources_raw, list) or not isinstance(obstacles_raw, list):
            raise ValueError("layout resources/obstacles must be lists")
        layout = cls(
            width=int(data["width"]),
            height=int(data["height"]),
            left_spawn=_coord(data["left_spawn"], "layout.left_spawn"),
            right_spawn=_coord(data["right_spawn"], "layout.right_spawn"),
            resources=tuple(sorted(_coord(value, "layout.resources[]") for value in resources_raw)),
            obstacles=tuple(sorted(_coord(value, "layout.obstacles[]") for value in obstacles_raw)),
        )
        layout.validate_structure()
        return layout

    def normalized_dict(self) -> dict[str, Any]:
        self.validate_structure()
        return {
            "width": self.width,
            "height": self.height,
            "left_spawn": list(self.left_spawn),
            "right_spawn": list(self.right_spawn),
            "resources": [list(value) for value in sorted(self.resources)],
            "obstacles": [list(value) for value in sorted(self.obstacles)],
        }

    @property
    def layout_hash(self) -> str:
        return _canonical_hash(self.normalized_dict())

    def validate_structure(self) -> None:
        if self.width < 2 or self.height < 2:
            raise ValueError("layout dimensions must be >= 2")
        if self.left_spawn == self.right_spawn:
            raise ValueError("layout spawns must be distinct")
        resources = tuple(self.resources)
        obstacles = tuple(self.obstacles)
        if len(set(resources)) != len(resources):
            raise ValueError("layout resources must be unique")
        if len(set(obstacles)) != len(obstacles):
            raise ValueError("layout obstacles must be unique")
        all_coords = (self.left_spawn, self.right_spawn) + resources + obstacles
        for x, y in all_coords:
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise ValueError(f"layout coordinate out of bounds: {(x, y)}")
        spawn_set = {self.left_spawn, self.right_spawn}
        if spawn_set & set(resources):
            raise ValueError("layout resources cannot overlap spawns")
        if spawn_set & set(obstacles):
            raise ValueError("layout obstacles cannot overlap spawns")
        if set(resources) & set(obstacles):
            raise ValueError("layout resources cannot overlap obstacles")

    def audit(self, *, fairness_threshold: float = 0.50) -> LayoutAudit:
        self.validate_structure()
        if not 0.0 <= fairness_threshold <= 1.0:
            raise ValueError("fairness_threshold must be in [0, 1]")
        left_distances = distance_map(self, self.left_spawn)
        right_distances = distance_map(self, self.right_spawn)
        spawn_distance = left_distances.get(self.right_spawn)
        connected = spawn_distance is not None
        reachable_both = all(resource in left_distances and resource in right_distances for resource in self.resources)

        left_mean: float | None = None
        right_mean: float | None = None
        asymmetry = 0.0
        if self.resources and reachable_both:
            left_mean = sum(left_distances[resource] for resource in self.resources) / len(self.resources)
            right_mean = sum(right_distances[resource] for resource in self.resources) / len(self.resources)
            denominator = max(1.0, left_mean, right_mean)
            asymmetry = abs(left_mean - right_mean) / denominator

        flags: list[str] = []
        if not connected:
            flags.append("spawn_disconnected")
        if not reachable_both:
            flags.append("resource_not_reachable_by_both")
        if asymmetry > fairness_threshold:
            flags.append("resource_distance_asymmetry")
        return LayoutAudit(
            accepted=not flags,
            flags=tuple(flags),
            connected_spawns=connected,
            resources_reachable_by_both=reachable_both,
            spawn_distance=spawn_distance,
            left_mean_resource_distance=None if left_mean is None else round(left_mean, 6),
            right_mean_resource_distance=None if right_mean is None else round(right_mean, 6),
            resource_distance_asymmetry=round(asymmetry, 6),
            fairness_threshold=float(fairness_threshold),
            layout_hash=self.layout_hash,
        )


def walkable_neighbors(
    layout: ArenaLayout,
    position: Coordinate,
    *,
    extra_blocked: Iterable[Coordinate] = (),
) -> tuple[Coordinate, ...]:
    blocked = set(layout.obstacles) | set(extra_blocked)
    x, y = position
    candidates = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
    return tuple(
        sorted(
            candidate
            for candidate in candidates
            if 0 <= candidate[0] < layout.width
            and 0 <= candidate[1] < layout.height
            and candidate not in blocked
        )
    )


def distance_map(
    layout: ArenaLayout,
    origin: Coordinate,
    *,
    extra_blocked: Iterable[Coordinate] = (),
) -> dict[Coordinate, int]:
    layout.validate_structure()
    blocked = set(layout.obstacles) | set(extra_blocked)
    if origin in blocked:
        return {}
    distances: dict[Coordinate, int] = {origin: 0}
    queue: deque[Coordinate] = deque([origin])
    while queue:
        current = queue.popleft()
        for neighbor in walkable_neighbors(layout, current, extra_blocked=blocked - set(layout.obstacles)):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return distances


def shortest_step_candidates(
    layout: ArenaLayout,
    position: Coordinate,
    target: Coordinate,
    *,
    extra_blocked: Iterable[Coordinate] = (),
) -> tuple[Coordinate, ...]:
    if position == target:
        return (position,)
    blocked = set(extra_blocked)
    target_distances = distance_map(layout, target, extra_blocked=blocked)
    candidates = walkable_neighbors(layout, position, extra_blocked=blocked)
    reachable = [(target_distances[candidate], candidate) for candidate in candidates if candidate in target_distances]
    if not reachable:
        return ()
    best = min(distance for distance, _ in reachable)
    return tuple(candidate for distance, candidate in reachable if distance == best)
