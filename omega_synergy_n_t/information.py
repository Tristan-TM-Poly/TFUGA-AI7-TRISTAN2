"""Discrete information measures for unique, redundant, and joint effects.

Interaction information is signed and is not a full partial-information decomposition.
The implementation therefore reports its convention explicitly.
"""
from __future__ import annotations
from collections import Counter
from math import log2
from typing import Iterable, Hashable


def entropy(values: Iterable[Hashable]) -> float:
    values=list(values)
    if not values: return 0.0
    counts=Counter(values); n=len(values)
    return -sum((c/n)*log2(c/n) for c in counts.values())


def joint(*columns: Iterable[Hashable]) -> list[tuple[Hashable,...]]:
    material=[list(c) for c in columns]
    if not material: return []
    sizes={len(c) for c in material}
    if len(sizes)!=1: raise ValueError("columns must have equal length")
    return list(zip(*material))


def mutual_information(x: Iterable[Hashable], y: Iterable[Hashable]) -> float:
    x=list(x); y=list(y)
    if len(x)!=len(y): raise ValueError("columns must have equal length")
    return entropy(x)+entropy(y)-entropy(joint(x,y))


def conditional_mutual_information(x, y, z) -> float:
    x=list(x); y=list(y); z=list(z)
    if len({len(x),len(y),len(z)})!=1: raise ValueError("columns must have equal length")
    return entropy(joint(x,z))+entropy(joint(y,z))-entropy(z)-entropy(joint(x,y,z))


def interaction_information(x, y, z) -> float:
    """McGill signed interaction information I(X;Y)-I(X;Y|Z).

    Negative values often indicate synergy under this convention; positive values
    often indicate redundancy. This sign is convention-dependent and not causal.
    """
    return mutual_information(x,y)-conditional_mutual_information(x,y,z)


def xor_fixture(repeats: int=16):
    if repeats<1: raise ValueError("repeats must be positive")
    x=[]; y=[]; target=[]
    for _ in range(repeats):
        for a,b in ((0,0),(0,1),(1,0),(1,1)):
            x.append(a); y.append(b); target.append(a^b)
    return x,y,target


def information_report(x,y,target) -> dict:
    x=list(x); y=list(y); target=list(target)
    return {
        "definition":"McGill interaction information; negative suggests joint-only synergy under this convention",
        "i_x_target":mutual_information(x,target),
        "i_y_target":mutual_information(y,target),
        "i_xy_target":mutual_information(joint(x,y),target),
        "interaction_information":interaction_information(x,y,target),
        "causal_claimed":False,
        "pid_claimed":False,
    }
