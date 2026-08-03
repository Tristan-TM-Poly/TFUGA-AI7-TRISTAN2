"""Two-level factorial designs, contrasts, and explicit alias diagnostics."""
from __future__ import annotations
from itertools import combinations
from math import prod
from .combinatorics import masks, mask_to_subset, subsets
from .models import ExperimentDesign, ExperimentRun, canonical_components, stable_id


def full_factorial_design(components: tuple[str,...], *, replicates: int=1) -> ExperimentDesign:
    items=canonical_components(components)
    if not items: raise ValueError("at least one component is required")
    if len(items)>16: raise ValueError("full factorial design capped at order 16")
    if replicates<1: raise ValueError("replicates must be positive")
    runs=[]
    for replicate in range(1,replicates+1):
        for mask in masks(len(items)):
            active=mask_to_subset(items,mask)
            inactive=tuple(x for x in items if x not in active)
            runs.append(ExperimentRun(stable_id("RUN",items,mask,replicate),active,inactive,replicate))
    identifiable=tuple(subsets(items,include_empty=False))
    return ExperimentDesign(stable_id("DESIGN","full",items,replicates),items,"full_factorial",tuple(runs),identifiable,(),
        ("Stable context across configurations.","No interference outside declared components."),
        ("Stop on critical safety or integrity failure.","Stop when a simpler baseline dominates."))


def fractional_half_design(components: tuple[str,...], *, parity: int=0) -> ExperimentDesign:
    items=canonical_components(components)
    if len(items)<3: raise ValueError("half fraction requires at least three components")
    if parity not in (0,1): raise ValueError("parity must be 0 or 1")
    runs=[]
    for mask in masks(len(items)):
        if mask.bit_count()%2!=parity: continue
        active=mask_to_subset(items,mask)
        runs.append(ExperimentRun(stable_id("RUN","half",items,mask),active,tuple(x for x in items if x not in active)))
    groups=alias_groups(items,[r.active for r in runs],max_order=min(4,len(items)))
    aliased_terms={t for group in groups for t in group if len(group)>1}
    identifiable=tuple(t for t in subsets(items,include_empty=False,max_order=min(4,len(items))) if "*".join(t) not in aliased_terms)
    flat_groups=tuple(tuple(group) for group in groups if len(group)>1)
    return ExperimentDesign(stable_id("DESIGN","half",items,parity),items,"fractional_half",tuple(runs),identifiable,flat_groups,
        ("Higher-order interactions are sparse.","Alias groups are reviewed before interpretation."),
        ("Stop when aliasing prevents the target decision.","Promote to full factorial for disputed terms."))


def mobius_contrast(outcomes: dict[frozenset[str],float], target: tuple[str,...]) -> float:
    target=canonical_components(target)
    total=0.0
    for subset in subsets(target):
        key=frozenset(subset)
        if key not in outcomes: raise ValueError(f"missing run {subset}")
        total+=((-1)**(len(target)-len(subset)))*float(outcomes[key])
    return total


def orthogonal_effect(outcomes: dict[frozenset[str],float], universe: tuple[str,...], term: tuple[str,...]) -> float:
    universe=canonical_components(universe); term=canonical_components(term)
    expected={frozenset(s) for s in subsets(universe)}
    if set(outcomes)!=expected: raise ValueError("orthogonal effect requires a complete factorial")
    contrast=0.0
    for active,value in outcomes.items():
        signs=[1 if item in active else -1 for item in term]
        contrast+=prod(signs)*value
    return contrast/(2**(len(universe)-1))


def _column(term: tuple[str,...], active_runs: list[tuple[str,...]]) -> tuple[int,...]:
    return tuple(prod(1 if x in set(active) else -1 for x in term) for active in active_runs)


def alias_groups(components: tuple[str,...], active_runs: list[tuple[str,...]], *, max_order: int=4) -> list[list[str]]:
    terms=list(subsets(components,include_empty=False,max_order=max_order))
    groups: list[list[str]]=[]; used=set()
    columns={term:_column(term,active_runs) for term in terms}
    for term in terms:
        if term in used: continue
        column=columns[term]; neg=tuple(-x for x in column)
        group=[]
        for other in terms:
            if other in used: continue
            if columns[other] in (column,neg):
                group.append("*".join(other)); used.add(other)
        groups.append(group)
    return groups
