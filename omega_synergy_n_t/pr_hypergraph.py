"""PR hypergraph planning and higher-order epistasis."""
from __future__ import annotations
from dataclasses import dataclass,field
from .mobius import direct_interaction
from .models import Serializable,canonical_components,stable_id

@dataclass(frozen=True,slots=True)
class PRMutation(Serializable):
    id: str
    paths: tuple[str,...]
    capabilities: tuple[str,...]=()
    needs: tuple[str,...]=()
    dependencies: tuple[str,...]=()
    conflicts: tuple[str,...]=()
    tests: tuple[str,...]=()
    rollback: tuple[str,...]=()

@dataclass(frozen=True,slots=True)
class PRConstellation(Serializable):
    id: str
    pr_ids: tuple[str,...]
    order: int
    dependency_edges: tuple[tuple[str,str],...]
    conflict_pairs: tuple[tuple[str,str],...]
    required_subset_orders: tuple[int,...]
    authority: str="review_only_plan"
    automatic_merge_allowed: bool=False


def compile_constellation(prs: list[PRMutation]) -> PRConstellation:
    ids=canonical_components(p.id for p in prs); known=set(ids); deps=[]; conflicts=set()
    for pr in prs:
        for dep in pr.dependencies:
            if dep in known: deps.append((dep,pr.id))
        for conflict in pr.conflicts:
            if conflict in known: conflicts.add(tuple(sorted((pr.id,conflict))))
    return PRConstellation(stable_id("PRC",ids),ids,len(ids),tuple(sorted(set(deps))),tuple(sorted(conflicts)),tuple(range(1,len(ids)+1)))


def topological_waves(constellation: PRConstellation) -> list[tuple[str,...]]:
    remaining=set(constellation.pr_ids); edges=set(constellation.dependency_edges); waves=[]
    while remaining:
        ready=tuple(sorted(x for x in remaining if not any(dst==x and src in remaining for src,dst in edges)))
        if not ready: raise ValueError("dependency cycle in PR constellation")
        waves.append(ready); remaining.difference_update(ready)
    return waves


def hyper_epistasis(values: dict[frozenset[str],float],pr_ids) -> float:
    return direct_interaction(values,canonical_components(pr_ids))
