"""Deterministic synthetic fixtures. These are software tests, not observed corpus evidence."""
from __future__ import annotations
from .combinatorics import subsets
from .mobius import zeta_reconstruct
from .models import SubsetMeasurement


def _records(values,context="fixture",se=0.0):
    return [SubsetMeasurement(tuple(sorted(k)),v,se,context_id=context,provenance=("synthetic_fixture",)) for k,v in sorted(values.items(),key=lambda x:(len(x[0]),sorted(x[0])))]


def pure_triplet():
    interactions={frozenset():0.0,frozenset({"A"}):0.0,frozenset({"B"}):0.0,frozenset({"C"}):0.0,
                  frozenset({"A","B"}):0.0,frozenset({"A","C"}):0.0,frozenset({"B","C"}):0.0,frozenset({"A","B","C"}):1.0}
    return _records(zeta_reconstruct(interactions),"pure_triplet")


def reducible_triplet():
    interactions={frozenset():0.0,frozenset({"A"}):1.0,frozenset({"B"}):2.0,frozenset({"C"}):3.0,
                  frozenset({"A","B"}):0.5,frozenset({"A","C"}):0.25,frozenset({"B","C"}):0.75,frozenset({"A","B","C"}):0.0}
    return _records(zeta_reconstruct(interactions),"reducible_triplet")


def anti_order4():
    items=("A","B","C","D"); interactions={frozenset():0.0}
    for s in subsets(items,include_empty=False): interactions[frozenset(s)]=0.2 if len(s)==2 else 0.0
    interactions[frozenset(items)]=-2.0
    return _records(zeta_reconstruct(interactions),"anti_order4")


def synergy_os_order4():
    items=("Foundry","Intent","Portfolio","Proof")
    interactions={frozenset():0.1}
    for s in subsets(items,include_empty=False):
        interactions[frozenset(s)]={1:0.1,2:0.05,3:0.02,4:0.7}[len(s)]
    values=zeta_reconstruct(interactions)
    return [SubsetMeasurement(tuple(sorted(k)),v,0.01,integration_cost=0.01*len(k),debt=0.005*len(k),residual_risk=0.002*len(k),context_id="synergy_os_order4",provenance=("synthetic_fixture",)) for k,v in sorted(values.items(),key=lambda x:(len(x[0]),sorted(x[0])))]
