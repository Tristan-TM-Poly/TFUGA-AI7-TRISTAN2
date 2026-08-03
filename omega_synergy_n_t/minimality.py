"""Ablation, necessity, and minimal-core discovery."""
from __future__ import annotations
from itertools import combinations
from .models import canonical_components


def necessity(values: dict[frozenset[str],float], coalition) -> dict[str,float]:
    coalition=canonical_components(coalition); full=frozenset(coalition)
    if full not in values: raise ValueError("full coalition value missing")
    return {c:values[full]-values[frozenset(set(coalition)-{c})] for c in coalition}


def minimal_cores(values: dict[frozenset[str],float], coalition, threshold: float) -> list[tuple[str,...]]:
    items=canonical_components(coalition)
    feasible=[]
    for size in range(1,len(items)+1):
        for subset in combinations(items,size):
            if values.get(frozenset(subset),float("-inf"))>=threshold:
                if not any(set(core).issubset(subset) for core in feasible): feasible.append(subset)
        if feasible: break
    return feasible


def redundant_components(values: dict[frozenset[str],float], coalition, tolerance: float=1e-9) -> list[str]:
    scores=necessity(values,coalition)
    return sorted(c for c,v in scores.items() if abs(v)<=tolerance)


def harmful_components(values: dict[frozenset[str],float], coalition, tolerance: float=1e-9) -> list[str]:
    scores=necessity(values,coalition)
    return sorted(c for c,v in scores.items() if v<-tolerance)
