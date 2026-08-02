"""Machine-readable atlases plus lazy regime lattice."""
from pathlib import Path
from itertools import product
import json
DATA=Path(__file__).with_name("data")
def _load(name): return json.loads((DATA/name).read_text(encoding="utf-8"))
def regimes():
    out=[]
    for shard in sorted(DATA.glob("regimes_*.json")): out.extend(json.loads(shard.read_text(encoding="utf-8")))
    if not out: out=_load("regimes.json")
    base=[x for x in out if "__" not in x["id"]]; present={x["id"] for x in out}
    for item in base:
        for modifier in ("collisionless","collisional","magnetized"):
            candidate={**item,"id":f"{item['id']}__{modifier}","name":f"{item['name']} — {modifier}","modifier":modifier,"status":"generated_specialization_requires_parameter_validation"}
            if candidate["id"] not in present: out.append(candidate)
    return out
def instabilities(): return _load("instabilities.json")
def models(): return _load("models.json")
def diagnostics(): return _load("diagnostics.json")
def benchmarks(): return _load("benchmarks.json")
def search_atlas(query):
    q=query.casefold(); out=[]
    for source,items in (("regime",regimes()),("instability",instabilities()),("model",models()),("diagnostic",diagnostics()),("benchmark",benchmarks())):
        for x in items:
            if q in json.dumps(x,ensure_ascii=False).casefold(): out.append({"source":source,**x})
    return out
REGIME_AXES={"coupling":("weak","moderate","strong"),"collisionality":("collisionless","transitional","collisional"),"magnetization":("unmagnetized","partially_magnetized","magnetized"),"statistics":("classical","degenerate"),"relativity":("nonrelativistic","relativistic")}
def regime_lattice_manifest():
    n=1
    for v in REGIME_AXES.values(): n*=len(v)
    return {"base_regimes":len(regimes()),"cells_per_regime":n,"total_cells":len(regimes())*n,"permanent_cap":False,"axes":REGIME_AXES}
def iter_regime_lattice():
    names=tuple(REGIME_AXES)
    for regime in regimes():
        for values in product(*(REGIME_AXES[n] for n in names)):
            yield {"cell_id":regime["id"]+"__"+"__".join(values),"parent_regime":regime["id"],"family":regime["family"],"domain":regime["domain"],**dict(zip(names,values)),"minimum_checks":["collectivity","scale_separation","conservation","convergence","uncertainty"],"epistemic_status":"generated_regime_cell_not_certified"}
def iter_benchmark_model_matrix():
    for b in benchmarks():
        for m in models(): yield {"benchmark_id":b["id"],"model_id":m["id"],"required_metrics":b["required_metrics"],"decision":"candidate_mapping_requires_implementation","oak":["reference","convergence","negative_control"]}
def iter_model_transition_graph():
    for s in models():
        for t in models():
            if s["id"]!=t["id"]: yield {"from":s["id"],"to":t["id"],"transition":"projection_or_lift","required_proof":["shared observables","asymptotic overlap","residual estimate","unit consistency"],"status":"candidate"}
