from __future__ import annotations

import hashlib
import json
from itertools import combinations
from typing import Any, Iterable

from .cvcd import canonicalize_atom


def _tokens(values: Iterable[str]) -> set[str]:
    out=set()
    for value in values:
        atom=canonicalize_atom(str(value))
        out.update(token for token in atom.replace("/", " ").replace(":", " ").split() if len(token) >= 3)
    return out


def skill_genome(spec: dict[str, Any]) -> dict[str, Any]:
    genome={
        "name": spec.get("name","unknown"),
        "activation_tokens": sorted(_tokens(spec.get("use_when",[]) + spec.get("do_not_use_when",[]))),
        "workflow_atoms": sorted({canonicalize_atom(str(x)) for x in spec.get("workflow",[])}),
        "invariant_atoms": sorted({canonicalize_atom(str(x)) for x in spec.get("invariants",[])}),
        "output_tokens": sorted(_tokens(spec.get("outputs",[]))),
        "eval_classes": sorted({str(c.get("class")) for c in spec.get("eval_cases",[]) if isinstance(c,dict)}),
    }
    canonical=json.dumps(genome,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    genome["fingerprint"]=hashlib.sha256(canonical.encode()).hexdigest()
    return genome


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa,sb=set(a),set(b)
    if not sa and not sb: return 1.0
    if not sa or not sb: return 0.0
    return len(sa & sb)/len(sa | sb)


def genome_similarity(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    ga=skill_genome(a); gb=skill_genome(b)
    axes={
        "activation":_jaccard(ga["activation_tokens"],gb["activation_tokens"]),
        "workflow":_jaccard(ga["workflow_atoms"],gb["workflow_atoms"]),
        "invariants":_jaccard(ga["invariant_atoms"],gb["invariant_atoms"]),
        "outputs":_jaccard(ga["output_tokens"],gb["output_tokens"]),
        "eval_classes":_jaccard(ga["eval_classes"],gb["eval_classes"]),
    }
    weights={"activation":0.20,"workflow":0.35,"invariants":0.25,"outputs":0.10,"eval_classes":0.10}
    score=sum(axes[k]*weights[k] for k in axes)
    return {"score":round(score,6), **{k:round(v,6) for k,v in axes.items()}}


def dedup_report(specs: Iterable[dict[str, Any]], threshold: float = 0.82) -> dict[str, Any]:
    specs=list(specs)
    pairs=[]
    for a,b in combinations(specs,2):
        sim=genome_similarity(a,b)
        if sim["score"] >= threshold:
            pairs.append({"a":a.get("name"),"b":b.get("name"),"similarity":sim})
    pairs.sort(key=lambda x:(-x["similarity"]["score"],str(x["a"]),str(x["b"])))
    return {
        "skill_count":len(specs),
        "threshold":threshold,
        "candidate_duplicate_pairs":pairs,
        "note":"Lexical/structural SkillGenome similarity is a dedup review signal, not proof of semantic equivalence.",
    }
