"""Local linearization atlases with measured validity domains."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Callable, Iterable, Sequence

import numpy as np
import numpy.typing as npt

from omega_vla_t.differential import jacobian


Array = npt.NDArray[np.float64]
VectorFunction = Callable[[Array], npt.ArrayLike]


@dataclass(frozen=True)
class LinearizationCell:
    cell_id: str
    center: tuple[float, ...]
    value: tuple[float, ...]
    jacobian: tuple[tuple[float, ...], ...]
    radius: float
    sample_count: int
    maximum_absolute_residual: float
    maximum_relative_residual: float
    mean_relative_residual: float
    validity_tolerance: float
    valid: bool
    spectral_radius: float | None
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AtlasTransition:
    source: str
    target: str
    center_distance: float
    overlap_margin: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LinearizationAtlas:
    cells: tuple[LinearizationCell, ...]
    transitions: tuple[AtlasTransition, ...]
    input_dimension: int
    output_dimension: int
    coverage_claimed: bool = False
    theorem_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "cells": [cell.to_dict() for cell in self.cells],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "input_dimension": self.input_dimension,
            "output_dimension": self.output_dimension,
            "coverage_claimed": self.coverage_claimed,
            "theorem_claimed": self.theorem_claimed,
        }

    def nearest_cell(self, point: npt.ArrayLike) -> LinearizationCell:
        value = np.asarray(point, dtype=float).reshape(-1)
        if value.shape != (self.input_dimension,):
            raise ValueError("point dimension does not match atlas")
        return min(
            self.cells,
            key=lambda cell: float(
                np.linalg.norm(value - np.asarray(cell.center, dtype=float))
            ),
        )

    def predict(self, point: npt.ArrayLike) -> tuple[Array, LinearizationCell, bool]:
        value = np.asarray(point, dtype=float).reshape(-1)
        cell = self.nearest_cell(value)
        center = np.asarray(cell.center)
        base = np.asarray(cell.value)
        derivative = np.asarray(cell.jacobian)
        predicted = base + derivative @ (value - center)
        inside_declared_radius = float(np.linalg.norm(value - center)) <= cell.radius
        return predicted, cell, inside_declared_radius and cell.valid


def _directions(dimension: int, random_count: int, seed: int) -> list[Array]:
    directions: list[Array] = []
    identity = np.eye(dimension)
    for axis in identity:
        directions.extend((axis.copy(), -axis.copy()))
    generator = np.random.default_rng(seed)
    for _ in range(random_count):
        direction = generator.normal(size=dimension)
        norm = float(np.linalg.norm(direction))
        if norm <= np.finfo(float).eps:
            continue
        directions.append(direction / norm)
    return directions


def build_linearization_cell(
    function: VectorFunction,
    center: npt.ArrayLike,
    *,
    radius: float,
    validity_tolerance: float = 0.05,
    random_directions: int = 16,
    seed: int = 0,
    derivative_step: float = 1e-6,
) -> LinearizationCell:
    point = np.asarray(center, dtype=float).reshape(-1)
    if point.size == 0 or not np.all(np.isfinite(point)):
        raise ValueError("center must be a non-empty finite vector")
    if radius <= 0.0 or validity_tolerance < 0.0:
        raise ValueError("radius must be positive and tolerance nonnegative")
    base = np.asarray(function(point), dtype=float).reshape(-1)
    if base.size == 0 or not np.all(np.isfinite(base)):
        raise ValueError("function must return a non-empty finite vector")
    derivative = jacobian(function, point, step=derivative_step)

    absolute_errors: list[float] = []
    relative_errors: list[float] = []
    local_seed = int.from_bytes(
        sha256(
            (repr(tuple(float(x) for x in point)) + f":{seed}").encode("utf-8")
        ).digest()[:8],
        "big",
    )
    directions = _directions(point.size, random_directions, local_seed)
    for direction in directions:
        perturbation = radius * direction
        observed = np.asarray(function(point + perturbation), dtype=float).reshape(-1)
        if observed.shape != base.shape or not np.all(np.isfinite(observed)):
            raise ValueError("function output changed dimension or became non-finite")
        predicted = base + derivative @ perturbation
        residual = observed - predicted
        absolute = float(np.linalg.norm(residual))
        scale = max(float(np.linalg.norm(observed)), np.finfo(float).eps)
        absolute_errors.append(absolute)
        relative_errors.append(absolute / scale)

    maximum_absolute = max(absolute_errors, default=0.0)
    maximum_relative = max(relative_errors, default=0.0)
    mean_relative = float(np.mean(relative_errors)) if relative_errors else 0.0
    spectral_radius: float | None = None
    if derivative.shape[0] == derivative.shape[1]:
        spectral_radius = float(np.max(np.abs(np.linalg.eigvals(derivative)), initial=0.0))

    identity_payload = (
        tuple(float(value) for value in point),
        float(radius),
        float(validity_tolerance),
        int(seed),
    )
    cell_id = "lin-cell-" + sha256(repr(identity_payload).encode()).hexdigest()[:20]
    return LinearizationCell(
        cell_id=cell_id,
        center=tuple(float(value) for value in point),
        value=tuple(float(value) for value in base),
        jacobian=tuple(
            tuple(float(value) for value in row) for row in derivative
        ),
        radius=float(radius),
        sample_count=len(directions),
        maximum_absolute_residual=maximum_absolute,
        maximum_relative_residual=maximum_relative,
        mean_relative_residual=mean_relative,
        validity_tolerance=float(validity_tolerance),
        valid=maximum_relative <= validity_tolerance,
        spectral_radius=spectral_radius,
    )


def build_linearization_atlas(
    function: VectorFunction,
    centers: Iterable[npt.ArrayLike],
    *,
    radii: float | Sequence[float],
    validity_tolerance: float = 0.05,
    random_directions: int = 16,
    seed: int = 0,
) -> LinearizationAtlas:
    center_list = [np.asarray(center, dtype=float).reshape(-1) for center in centers]
    if not center_list:
        raise ValueError("at least one center is required")
    input_dimension = center_list[0].size
    if any(center.shape != (input_dimension,) for center in center_list):
        raise ValueError("all centers must share one input dimension")
    if np.isscalar(radii):
        radius_list = [float(radii)] * len(center_list)
    else:
        radius_list = [float(value) for value in radii]
    if len(radius_list) != len(center_list):
        raise ValueError("one radius is required per center")

    cells = tuple(
        build_linearization_cell(
            function,
            center,
            radius=radius,
            validity_tolerance=validity_tolerance,
            random_directions=random_directions,
            seed=seed + index,
        )
        for index, (center, radius) in enumerate(zip(center_list, radius_list))
    )
    output_dimension = len(cells[0].value)
    if any(len(cell.value) != output_dimension for cell in cells):
        raise ValueError("function output dimension changed across atlas centers")

    transitions: list[AtlasTransition] = []
    for source_index, source in enumerate(cells):
        source_center = np.asarray(source.center)
        for target_index in range(source_index + 1, len(cells)):
            target = cells[target_index]
            distance = float(
                np.linalg.norm(source_center - np.asarray(target.center))
            )
            margin = source.radius + target.radius - distance
            if margin >= 0.0:
                transitions.extend(
                    (
                        AtlasTransition(
                            source=source.cell_id,
                            target=target.cell_id,
                            center_distance=distance,
                            overlap_margin=margin,
                        ),
                        AtlasTransition(
                            source=target.cell_id,
                            target=source.cell_id,
                            center_distance=distance,
                            overlap_margin=margin,
                        ),
                    )
                )
    return LinearizationAtlas(
        cells=cells,
        transitions=tuple(transitions),
        input_dimension=input_dimension,
        output_dimension=output_dimension,
        coverage_claimed=False,
        theorem_claimed=False,
    )
