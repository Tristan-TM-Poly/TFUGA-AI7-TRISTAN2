"""Identity dependency graph with cycle and closure audits."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable
from .models import IdentitySchema


@dataclass(frozen=True)
class DependencyAudit:
    nodes: int
    edges: int
    missing_parents: tuple[str, ...]
    cycle: tuple[str, ...]
    valid: bool
    theorem_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class IdentityDependencyGraph:
    def __init__(self, schemas: Iterable[IdentitySchema]) -> None:
        self.schemas = {schema.schema_id: schema for schema in schemas}
        self.parents = {
            schema.schema_id: tuple(schema.parent_ids) for schema in self.schemas.values()
        }

    def audit(self) -> DependencyAudit:
        missing = sorted({
            parent for parents in self.parents.values() for parent in parents
            if parent not in self.schemas
        })
        cycle = self._find_cycle()
        return DependencyAudit(
            nodes=len(self.schemas),
            edges=sum(len(x) for x in self.parents.values()),
            missing_parents=tuple(missing),
            cycle=cycle,
            valid=not missing and not cycle,
        )

    def _find_cycle(self) -> tuple[str, ...]:
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(node: str) -> tuple[str, ...]:
            if node in visiting:
                start = stack.index(node)
                return tuple(stack[start:] + [node])
            if node in visited:
                return ()
            visiting.add(node)
            stack.append(node)
            for parent in self.parents.get(node, ()):
                found = visit(parent)
                if found:
                    return found
            stack.pop()
            visiting.remove(node)
            visited.add(node)
            return ()

        for node in sorted(self.schemas):
            found = visit(node)
            if found:
                return found
        return ()

    def topological_order(self) -> tuple[str, ...]:
        audit = self.audit()
        if not audit.valid:
            raise ValueError(f"invalid dependency graph: {audit.to_dict()}")
        visited: set[str] = set()
        result: list[str] = []

        def visit(node: str) -> None:
            if node in visited:
                return
            for parent in self.parents[node]:
                visit(parent)
            visited.add(node)
            result.append(node)

        for node in sorted(self.schemas):
            visit(node)
        return tuple(result)

    def ancestors(self, schema_id: str) -> tuple[str, ...]:
        if schema_id not in self.schemas:
            raise KeyError(schema_id)
        result: set[str] = set()
        frontier = list(self.parents[schema_id])
        while frontier:
            current = frontier.pop()
            if current not in result:
                result.add(current)
                frontier.extend(self.parents[current])
        return tuple(sorted(result))
