"""Exact zeta/Möbius transforms on the Boolean subset lattice."""
from __future__ import annotations
from collections.abc import Mapping
from math import sqrt
from .combinatorics import proper_subsets, subsets, lattice_missing
from .models import Certification, InteractionEstimate, SubsetMeasurement, canonical_components


def normalize_values(values: Mapping[object,float]) -> dict[frozenset[str],float]:
    result={}
    for key,value in values.items():
        if isinstance(key,frozenset): k=key
        elif isinstance(key,(set,list,tuple)): k=frozenset(str(x) for x in key)
        elif key in ("",None,"empty","∅"): k=frozenset()
        else: k=frozenset([str(key)])
        result[k]=float(value)
    return result


def validate_complete_lattice(values: Mapping[object,float], universe: tuple[str,...]|None=None) -> tuple[str,...]:
    normalized=normalize_values(values)
    if universe is None:
        universe=canonical_components(x for key in normalized for x in key)
    missing=lattice_missing(universe,normalized)
    if missing:
        preview=", ".join("{"+",".join(x)+"}" for x in missing[:8])
        raise ValueError(f"incomplete subset lattice: {len(missing)} missing ({preview})")
    return canonical_components(universe)


def mobius_decompose(values: Mapping[object,float], *, require_complete: bool=True) -> dict[frozenset[str],float]:
    normalized=normalize_values(values)
    universe=canonical_components(x for key in normalized for x in key)
    if require_complete: validate_complete_lattice(normalized,universe)
    interactions: dict[frozenset[str],float]={}
    for subset in subsets(universe):
        key=frozenset(subset)
        if key not in normalized: continue
        lower=sum(interactions[frozenset(t)] for t in proper_subsets(subset) if frozenset(t) in interactions)
        interactions[key]=normalized[key]-lower
    return interactions


def direct_interaction(values: Mapping[object,float], target: tuple[str,...]) -> float:
    normalized=normalize_values(values)
    result=0.0
    target=canonical_components(target)
    for subset in subsets(target):
        key=frozenset(subset)
        if key not in normalized: raise ValueError(f"missing subset {subset}")
        result+=((-1.0)**(len(target)-len(subset)))*normalized[key]
    return result


def zeta_reconstruct(interactions: Mapping[object,float]) -> dict[frozenset[str],float]:
    normalized=normalize_values(interactions)
    universe=canonical_components(x for key in normalized for x in key)
    output={}
    for subset in subsets(universe):
        output[frozenset(subset)]=sum(normalized.get(frozenset(t),0.0) for t in subsets(subset))
    return output


def interaction_standard_error(errors: Mapping[object,float], target: tuple[str,...]) -> float:
    normalized=normalize_values(errors)
    variances=[]
    for subset in subsets(target):
        key=frozenset(subset)
        if key not in normalized: raise ValueError(f"missing standard error for subset {subset}")
        variances.append(normalized[key]**2)
    return sqrt(sum(variances))


def decompose_measurements(records: list[SubsetMeasurement], *, z: float=1.96) -> list[InteractionEstimate]:
    if not records: return []
    context_ids={r.context_id for r in records}
    if len(context_ids)!=1: raise ValueError("measurements from multiple contexts must be decomposed separately")
    by_key={r.key:r for r in records}
    universe=canonical_components(x for r in records for x in r.components)
    validate_complete_lattice({k:r.value for k,r in by_key.items()},universe)
    values={k:r.value for k,r in by_key.items()}
    interactions=mobius_decompose(values)
    results=[]
    baseline=values[frozenset()]
    for subset in subsets(universe,include_empty=False):
        key=frozenset(subset); rec=by_key[key]
        proper=interactions[key]
        se=interaction_standard_error({k:r.standard_error for k,r in by_key.items()},subset)
        gross=rec.value-baseline
        lower=gross-proper
        net=proper-rec.integration_cost-rec.debt-rec.residual_risk
        purity=abs(proper)/(abs(rec.value)+1e-12)
        necessity={c:rec.value-by_key[key-{c}].value for c in subset}
        cert=Certification.N5_PROPER if proper-z*se>0 else Certification.N4_GROSS
        limitations=("Independent-error propagation assumed.","Measured interaction is not automatically causal.")
        results.append(InteractionEstimate(
            components=subset,order=len(subset),gross_value=gross,proper_interaction=proper,
            lower_order_value=lower,integration_cost=rec.integration_cost,debt=rec.debt,
            residual_risk=rec.residual_risk,net_synergy=net,standard_error=se,
            interval_low=proper-z*se,interval_high=proper+z*se,purity=purity,
            necessity=necessity,context_id=rec.context_id,certification=cert,limitations=limitations))
    return results
