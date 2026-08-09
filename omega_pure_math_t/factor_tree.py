"""Exact finite factorization-tree search relative to declared rules."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping


@dataclass(frozen=True)
class FactorTree:
    label: str
    children: tuple["FactorTree", ...] = ()

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def leaf_count(self) -> int:
        if self.is_leaf:
            return 1
        return sum(child.leaf_count() for child in self.children)

    def depth(self) -> int:
        if self.is_leaf:
            return 0
        return 1 + max(child.depth() for child in self.children)

    def signature(self) -> str:
        if self.is_leaf:
            return self.label
        return f"{self.label}(" + ",".join(child.signature() for child in self.children) + ")"


def minimum_factor_tree(
    target: str,
    *,
    bricks: set[str],
    rules: Mapping[str, tuple[tuple[str, ...], ...]],
) -> FactorTree | None:
    """Return a minimum-leaf factor tree in an exact finite acyclic search.

    Cyclic decomposition paths are rejected on the active recursion stack.
    """

    @lru_cache(maxsize=None)
    def solve(label: str, active: frozenset[str] = frozenset()) -> FactorTree | None:
        if label in bricks:
            return FactorTree(label)
        if label in active:
            return None
        best: FactorTree | None = None
        next_active = active | {label}
        for decomposition in rules.get(label, ()):
            children: list[FactorTree] = []
            feasible = True
            for child_label in decomposition:
                child = solve(child_label, next_active)
                if child is None:
                    feasible = False
                    break
                children.append(child)
            if not feasible:
                continue
            candidate = FactorTree(label, tuple(children))
            if best is None or (
                candidate.leaf_count(), candidate.depth(), candidate.signature()
            ) < (
                best.leaf_count(), best.depth(), best.signature()
            ):
                best = candidate
        return best

    return solve(target)


def factor_tree_distance(left: FactorTree, right: FactorTree) -> int:
    """Simple structural edit proxy via symmetric difference of subtree signatures."""

    def subtrees(tree: FactorTree) -> set[str]:
        result = {tree.signature()}
        for child in tree.children:
            result |= subtrees(child)
        return result

    return len(subtrees(left) ^ subtrees(right))
