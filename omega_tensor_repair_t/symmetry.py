"""Finite symmetry actions and iterative branching towers."""

from __future__ import annotations

from typing import Iterable, Sequence

from .linalg import Matrix, add, scale, shape, zeros
from .models import BranchNode, SymmetryTower

Permutation = tuple[int, ...]


def validate_permutation(permutation: Sequence[int]) -> Permutation:
    result = tuple(int(index) for index in permutation)
    if sorted(result) != list(range(len(result))):
        raise ValueError("invalid permutation")
    return result


def permute_square(matrix: Matrix, permutation: Sequence[int]) -> Matrix:
    rows, cols = shape(matrix)
    perm = validate_permutation(permutation)
    if rows != cols or rows != len(perm):
        raise ValueError("permutation action requires a matching square matrix")
    return tuple(tuple(matrix[perm[row]][perm[col]] for col in range(cols)) for row in range(rows))


def group_average(matrix: Matrix, permutations: Iterable[Sequence[int]]) -> Matrix:
    actions = tuple(validate_permutation(permutation) for permutation in permutations)
    if not actions:
        raise ValueError("group average requires at least one action")
    result = zeros(*shape(matrix))
    for action in actions:
        result = add(result, permute_square(matrix, action))
    return scale(result, 1.0 / len(actions))


def default_rank2_tower_2d() -> SymmetryTower:
    return SymmetryTower(
        name="rank2-2d-transpose-trace tower",
        nodes=(
            BranchNode("full", 4, "complete", None, ("symmetric", "antisymmetric")),
            BranchNode("symmetric", 3, "transpose-even", "full", ("symmetric_traceless", "trace")),
            BranchNode("antisymmetric", 1, "transpose-odd", "full"),
            BranchNode("symmetric_traceless", 2, "transpose-even and trace-free", "symmetric"),
            BranchNode("trace", 1, "O(2)-scalar", "symmetric"),
        ),
    )


def validate_tower(tower: SymmetryTower) -> dict[str, object]:
    ids = {node.node_id for node in tower.nodes}
    errors: list[str] = []
    for node in tower.nodes:
        if node.parent_id is not None and node.parent_id not in ids:
            errors.append(f"missing parent {node.parent_id!r} for {node.node_id!r}")
        for child_id in node.children_ids:
            if child_id not in ids:
                errors.append(f"missing child {child_id!r} for {node.node_id!r}")
        if node.children_ids and node.exact_partition:
            child_dimension = sum(tower.node(child_id).dimension for child_id in node.children_ids)
            if child_dimension != node.dimension:
                errors.append(
                    f"dimension mismatch at {node.node_id!r}: {node.dimension} != {child_dimension}"
                )
    return {
        "valid": not errors,
        "errors": errors,
        "node_count": len(tower.nodes),
        "root_count": len(tower.roots()),
    }
