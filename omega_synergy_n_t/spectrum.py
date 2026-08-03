"""Order spectrum and higher-order portfolio metrics."""
from __future__ import annotations
from collections import defaultdict
from math import log
from .models import InteractionEstimate, OrderBand, OrderSpectrum
from .combinatorics import possible_count


def order_spectrum(estimates: list[InteractionEstimate], *, component_count: int|None=None, threshold: float=0.0) -> OrderSpectrum:
    grouped=defaultdict(list)
    for item in estimates: grouped[item.order].append(item)
    if component_count is None:
        component_count=len({x for item in estimates for x in item.components})
    bands=[]; energies={}
    for order in sorted(grouped):
        items=grouped[order]
        positive=[x for x in items if x.proper_interaction>threshold]
        negative=[x for x in items if x.proper_interaction<-threshold]
        pos_energy=sum(max(0.0,x.proper_interaction) for x in items)
        neg_energy=sum(max(0.0,-x.proper_interaction) for x in items)
        cost=sum(x.integration_cost for x in items)
        efficiency=sum(max(0.0,x.net_synergy) for x in items)/(cost+1e-12)
        purity=sum(x.purity for x in items)/len(items)
        possible=possible_count(component_count,order)
        bands.append(OrderBand(order,len(items),possible,len(positive),len(negative),pos_energy,neg_energy,
                               len(positive)/(possible or 1),efficiency,purity))
        energies[order]=pos_energy
    total=sum(energies.values())
    normalized={k:(v/total if total else 0.0) for k,v in energies.items()}
    entropy=-sum(p*log(p) for p in normalized.values() if p>0)
    dominant=max(normalized,key=normalized.get) if total else None
    return OrderSpectrum(tuple(bands),normalized,entropy,dominant)


def genuine_interaction_rate(estimates: list[InteractionEstimate], order: int, threshold: float=0.0) -> float:
    items=[x for x in estimates if x.order==order]
    return sum(x.interval_low>threshold for x in items)/(len(items) or 1)


def n_order_yield(estimates: list[InteractionEstimate], order: int, experiment_cost: float) -> float:
    if experiment_cost<=0: raise ValueError("experiment_cost must be positive")
    return sum(max(0.0,x.net_synergy) for x in estimates if x.order==order)/experiment_cost


def higher_order_debt_ratio(estimates: list[InteractionEstimate], order: int) -> float:
    items=[x for x in estimates if x.order==order]
    return sum(x.debt for x in items)/(sum(max(0.0,x.proper_interaction) for x in items)+1e-12)
