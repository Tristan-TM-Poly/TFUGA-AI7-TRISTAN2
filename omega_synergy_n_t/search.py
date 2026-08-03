"""Bounded search methods with an explicit reserve for pure high-order emergence."""
from __future__ import annotations
from hashlib import sha256
from itertools import combinations
from .models import SearchCandidate, canonical_components


def _det_noise(items: tuple[str,...]) -> float:
    return int(sha256("\x1f".join(items).encode()).hexdigest()[:8],16)/0xffffffff


def heuristic_candidate(items, signatures: dict[str,dict], *, exploration: bool=False) -> SearchCandidate:
    items=canonical_components(items)
    outputs=set(); inputs=set(); domains=set(); evidence=0.0; risk=0.0; cost=0.0
    for item in items:
        sig=signatures.get(item,{})
        outputs.update(sig.get("outputs",[])); inputs.update(sig.get("inputs",[])); domains.update(sig.get("domains",[]))
        evidence+=float(sig.get("evidence",0.0)); risk+=float(sig.get("risk",0.0)); cost+=float(sig.get("cost",1.0))
    matched=len(outputs&inputs); closure=matched/(len(inputs) or 1)
    compatibility=1.0 if matched else (0.25 if len(items)>2 and exploration else 0.0)
    eig=(len(domains)+matched)/(len(items)+2)
    score=0.35*closure+0.25*compatibility+0.2*(evidence/len(items))+0.2*eig-0.1*(risk/len(items))-0.05*(cost/len(items))
    rationale=(f"matched_types={matched}",f"domains={len(domains)}",f"exploration={exploration}")
    return SearchCandidate(items,len(items),score,closure,compatibility,eig,cost,risk,exploration,rationale)


def exhaustive_search(components, signatures, *, min_order=2, max_order=4) -> list[SearchCandidate]:
    items=canonical_components(components); output=[]
    for order in range(min_order,min(max_order,len(items))+1):
        output.extend(heuristic_candidate(c,signatures) for c in combinations(items,order))
    return sorted(output,key=lambda x:(-x.heuristic_score,x.components))


def beam_search(components, signatures, *, max_order=6, beam_width=64, exploration_rate=0.15) -> dict[int,list[SearchCandidate]]:
    items=canonical_components(components)
    if not 0<=exploration_rate<=1: raise ValueError("exploration_rate must be in [0,1]")
    pairs=[heuristic_candidate(c,signatures,exploration=_det_noise(c)<exploration_rate) for c in combinations(items,2)]
    beam=sorted(pairs,key=lambda x:(-(x.heuristic_score+(0.15 if x.exploration else 0)),x.components))[:beam_width]
    result={2:beam}
    for order in range(3,min(max_order,len(items))+1):
        seen={}; expanded=[]
        for candidate in beam:
            for item in items:
                if item in candidate.components: continue
                coalition=canonical_components((*candidate.components,item))
                if coalition in seen: continue
                exploration=_det_noise(coalition)<exploration_rate
                proposal=heuristic_candidate(coalition,signatures,exploration=exploration)
                seen[coalition]=proposal; expanded.append(proposal)
        beam=sorted(expanded,key=lambda x:(-(x.heuristic_score+(0.15 if x.exploration else 0)),x.components))[:beam_width]
        result[order]=beam
    return result


def branch_and_bound(components, signatures, *, max_order=6, threshold=0.0, max_results=100) -> list[SearchCandidate]:
    items=canonical_components(components); output=[]
    def visit(prefix: tuple[str,...], start: int) -> None:
        if len(output)>=max_results: return
        if len(prefix)>=2:
            candidate=heuristic_candidate(prefix,signatures)
            optimistic=candidate.heuristic_score+0.2*(max_order-len(prefix))
            if optimistic<threshold: return
            if candidate.heuristic_score>=threshold: output.append(candidate)
        if len(prefix)>=max_order: return
        for index in range(start,len(items)):
            visit((*prefix,items[index]),index+1)
    visit((),0)
    return sorted(output,key=lambda x:(-x.heuristic_score,x.components))[:max_results]
