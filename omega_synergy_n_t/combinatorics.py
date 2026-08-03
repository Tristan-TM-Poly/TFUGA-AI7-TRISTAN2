"""Subset-lattice utilities with deterministic ordering."""
from __future__ import annotations
from itertools import combinations
from math import comb
from typing import Iterable, Iterator
from .models import canonical_components


def subsets(values: Iterable[str], *, include_empty: bool=True, max_order: int|None=None) -> Iterator[tuple[str,...]]:
    items=canonical_components(values)
    start=0 if include_empty else 1
    stop=len(items) if max_order is None else min(len(items),max_order)
    for size in range(start,stop+1):
        yield from combinations(items,size)


def proper_subsets(values: Iterable[str], *, include_empty: bool=True) -> Iterator[tuple[str,...]]:
    items=canonical_components(values)
    stop=max(0,len(items)-1)
    yield from subsets(items,include_empty=include_empty,max_order=stop)


def subset_key(values: Iterable[str]) -> frozenset[str]: return frozenset(canonical_components(values))


def possible_count(component_count: int, order: int) -> int:
    if order<0 or order>component_count: return 0
    return comb(component_count,order)


def lattice_missing(universe: Iterable[str], observed: Iterable[frozenset[str]]) -> list[tuple[str,...]]:
    keys=set(observed)
    return [item for item in subsets(universe) if frozenset(item) not in keys]


def masks(component_count: int) -> range:
    if component_count<0: raise ValueError("component_count must be non-negative")
    return range(1<<component_count)


def mask_to_subset(components: Iterable[str], mask: int) -> tuple[str,...]:
    items=canonical_components(components)
    if mask<0 or mask>=(1<<len(items)): raise ValueError("mask outside component universe")
    return tuple(item for index,item in enumerate(items) if mask&(1<<index))
