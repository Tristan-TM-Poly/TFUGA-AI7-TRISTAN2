"""Load and query machine-readable plasma atlases shipped with the package."""
from __future__ import annotations
from pathlib import Path
from itertools import product
import json
DATA=Path(__file__).with_name("data")

def _load(name:str): return json.loads((DATA/name).read_text(encoding="utf-8"))
def regimes():
    shards=sorted(DATA.glob("regimes_*.json"))
    out=[]
    for shard in shards:
        out.extend(json.loads(shard.read_text(encoding="utf-8")))
    if not out:
        out=_load("regimes.json")
    base=[x for x in out if "__" not in x["id"]]
    present={x["id"] for x in out}
    for item in base:
        for modifier in ("collisionless","collisional","magnetized"):
            candidate={
                **item,
                "id":f"{item['id']}__{modifier}",
                "name":f"{item['name']} — {modifier}",
                "modifier":modifier,
                "status":"generated_specialization_requires_parameter_validation",
            }
            if candidate["id"] not in present:
                out.append(candidate)
    return out
def instabilities(): return _load("instabilities.json")
def models(): return _load("models.json")
def diagnostics(): return _load("diagnostics.json")
def benchmarks(): return _load("benchmarks.json")

def search_atlas(query:str)->list[dict]:
    q=query.casefold(); out=[]
    for source,items in (("regime",regimes()),("instability",instabilities()),("model",models()),("diagnostic",diagnostics()),("benchmark",benchmarks())):
        for x in items:
            if q in json.dumps(x,ensure_ascii=False).casefold(): out.append({"source":source,**x})
    return out

REGIME_AXES={
    "coupling":("weak","moderate","strong"),
    "collisionality":("collisionless","transitional","collisional"),
    "magnetization":("unmagnetized","partially_magnetized","magnetized"),
    "statistics":("classical","degenerate"),
    "relativity":("nonrelativistic","relativistic"),
}

def regime_lattice_manifest()->dict:
    per_regime=1
    for values in REGIME_AXES.values(): per_regime*=len(values)
    return {"base_regimes":len(regimes()),"cells_per_regime":per_regime,"total_cells":len(regimes())*per_regime,"permanent_cap":False,"axes":REGIME_AXES}

def iter_regime_lattice():
    names=tuple(REGIME_AXES)
    for regime in regimes():
        for values in product(*(REGIME_AXES[n] for n in names)):
            params=dict(zip(names,values))
            yield {"cell_id":regime["id"]+"__"+"__".join(values),"parent_regime":regime["id"],"family":regime["family"],"domain":regime["domain"],**params,"minimum_checks":["collectivity","scale_separation","conservation","convergence","uncertainty"],"epistemic_status":"generated_regime_cell_not_certified"}

def iter_benchmark_model_matrix():
    for benchmark in benchmarks():
        for model in models():
            yield {"benchmark_id":benchmark["id"],"model_id":model["id"],"required_metrics":benchmark["required_metrics"],"decision":"candidate_mapping_requires_implementation","oak":["reference","convergence","negative_control"]}

def iter_model_transition_graph():
    for source in models():
        for target in models():
            if source["id"]!=target["id"]:
                yield {"from":source["id"],"to":target["id"],"transition":"projection_or_lift","required_proof":["shared observables","asymptotic overlap","residual estimate","unit consistency"],"status":"candidate"}
