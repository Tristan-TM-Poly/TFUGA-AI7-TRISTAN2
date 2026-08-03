"""Generate Ω-MILLENNIUM-T∞ R0.2 source package."""
from __future__ import annotations
from omega_millennium_r02_gen_common import write

CORE=r'''"""Typed R0.2 research kernel. Software fixtures only; no theorem solution."""
from __future__ import annotations
from dataclasses import dataclass,asdict,replace
from enum import Enum
from pathlib import Path
from collections import defaultdict,deque
import hashlib,json

ROOT=Path(__file__).resolve().parents[2]
def load(name): return json.loads((ROOT/"data"/"omega_millennium_r02"/name).read_text())
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()

class QuantifierKind(str,Enum): FORALL="forall"; EXISTS="exists"; UNIQUE="exists_unique"
@dataclass(frozen=True)
class Symbol:
    name:str; type_name:str; domain:str
@dataclass(frozen=True)
class Quantifier:
    kind:QuantifierKind; symbol:str; scope_index:int
@dataclass(frozen=True)
class TypedStatement:
    statement_id:str; natural_language:str; formal_text:str
    symbols:tuple[Symbol,...]; quantifiers:tuple[Quantifier,...]
    coefficient_field:str; ambient_domain:str
    def validate(self):
        errors=[]; names=[s.name for s in self.symbols]
        if not self.statement_id or not self.natural_language or not self.formal_text: errors.append("blank statement field")
        if len(names)!=len(set(names)): errors.append("duplicate symbols")
        if set(q.symbol for q in self.quantifiers)-set(names): errors.append("unknown quantified symbol")
        if len({q.scope_index for q in self.quantifiers})!=len(self.quantifiers): errors.append("duplicate quantifier scope")
        if not self.coefficient_field or not self.ambient_domain: errors.append("missing domain contract")
        return tuple(errors)

class ClaimStatus(str,Enum):
    PARSED="parsed"; TYPE_CHECKED="type_checked"; SKELETON="skeleton"; KERNEL_CHECKED="kernel_checked"; REFUTED="refuted"
@dataclass(frozen=True)
class ClaimIR:
    claim_id:str; problem_id:str; statement:TypedStatement
    assumptions:tuple[str,...]=(); dependencies:tuple[str,...]=()
    evidence:tuple[str,...]=(); status:ClaimStatus=ClaimStatus.PARSED
    solution_claimed:bool=False
    def validate(self):
        errors=list(self.statement.validate())
        if self.claim_id in self.dependencies: errors.append("self dependency")
        if len(self.dependencies)!=len(set(self.dependencies)): errors.append("duplicate dependencies")
        if self.solution_claimed and self.status!=ClaimStatus.KERNEL_CHECKED: errors.append("solution claim below kernel checked")
        return tuple(errors)
    @property
    def digest(self): return digest(asdict(self))

class AssumptionState(str,Enum): DECLARED="declared"; INHERITED="inherited"; DISCHARGED="discharged"; HIDDEN="hidden"
@dataclass(frozen=True)
class Assumption:
    assumption_id:str; statement:str; state:AssumptionState=AssumptionState.DECLARED; parents:tuple[str,...]=()
class AssumptionLedger:
    def __init__(self): self.items={}
    def add(self,a):
        if a.assumption_id in self.items: raise ValueError("duplicate assumption")
        if set(a.parents)-self.items.keys(): raise ValueError("unknown parent")
        self.items[a.assumption_id]=a
    def closure(self,ids):
        seen=set(); stack=list(ids)
        while stack:
            aid=stack.pop()
            if aid not in self.items: raise ValueError("unknown assumption")
            if aid not in seen: seen.add(aid); stack.extend(self.items[aid].parents)
        return frozenset(seen)
    def discharge(self,aid):
        self.items[aid]=replace(self.items[aid],state=AssumptionState.DISCHARGED)

@dataclass(frozen=True)
class HyperEdge:
    edge_id:str; premises:tuple[str,...]; conclusion:str; level:int=1; semantic:str="implies"
class HyperProofGraph:
    def __init__(self,problem_id): self.problem_id=problem_id; self.claims={}; self.edges={}
    def add_claim(self,c):
        if c.problem_id!=self.problem_id or c.validate(): raise ValueError("invalid claim")
        if c.claim_id in self.claims: raise ValueError("duplicate claim")
        self.claims[c.claim_id]=c
    def add_edge(self,e):
        if not e.premises or e.conclusion in e.premises: raise ValueError("invalid edge")
        if set(e.premises+(e.conclusion,))-self.claims.keys(): raise ValueError("unknown claim")
        self.edges[e.edge_id]=e
    def closure(self,seeds,minimum_level=1):
        reached=set(seeds); changed=True
        while changed:
            changed=False
            for e in self.edges.values():
                if e.semantic!="refutes" and e.level>=minimum_level and e.conclusion not in reached and all(p in reached for p in e.premises):
                    reached.add(e.conclusion); changed=True
        return frozenset(reached)
    def frontier(self,target,seeds,minimum_level=1):
        reached=self.closure(seeds,minimum_level)
        options=[tuple(sorted(set(e.premises)-reached)) for e in self.edges.values() if e.conclusion==target and e.level>=minimum_level]
        return tuple(sorted((x for x in options if x),key=lambda x:(len(x),x)))
    def cycles(self):
        adj=defaultdict(set)
        for e in self.edges.values():
            for p in e.premises: adj[p].add(e.conclusion)
        indeg={c:0 for c in self.claims}
        for src in adj:
            for dst in adj[src]: indeg[dst]+=1
        q=deque(sorted(k for k,v in indeg.items() if v==0))
        while q:
            n=q.popleft()
            for d in adj[n]:
                indeg[d]-=1
                if indeg[d]==0:q.append(d)
        return tuple(sorted(k for k,v in indeg.items() if v>0))

EXPECTED={"strategies":448,"lemma_families":64,"falsifiers":32,"formal_targets":16,"assumption_patterns":128,"proof_mutations":128,"barriers":224,"transfer_bridges":64,"research_cells_seed":4096}
FILES={"strategies":"strategies.json","lemma_families":"lemma_families.json","falsifiers":"falsifiers.json","formal_targets":"formal_targets.json","assumption_patterns":"assumption_patterns.json","proof_mutations":"proof_mutations.json","barriers":"barriers.json","transfer_bridges":"transfer_bridges.json","research_cells_seed":"research_cells_seed.json"}
def atlas():
    errors=[]; catalogs={}
    for name,file in FILES.items():
        payload=load(file); catalogs[name]=payload
        if payload["count"]!=EXPECTED[name] or len(payload["items"])!=EXPECTED[name]: errors.append(name)
    return {"valid":not errors,"errors":errors,"counts":EXPECTED,"logical_frontier_cells":14680064,"permanent_total_cap":None,"digest":digest(catalogs)}
def problem_specs():
    paths=sorted((ROOT/"specs"/"omega_millennium_r02").glob("*.json"))
    items=[json.loads(p.read_text()) for p in paths]
    errors=[x["problem_id"] for x in items if x["formal_contract"]["solution_claimed"] is not False]
    return {"count":len(items),"open":sum(x["status"]=="open" for x in items),"valid":not errors,"errors":errors,"digest":digest(items)}
def poincare_benchmark():
    p=load("poincare_reconstruction_fixture.json"); ids={x["claim_id"] for x in p["claims"]}; errors=[]
    for e in p["edges"]:
        if set(e["premises"]+[e["conclusion"]])-ids: errors.append(e["edge_id"])
    reached=set(p["seed_claims"]); changed=True
    while changed:
        changed=False
        for e in p["edges"]:
            if e["oak_level"]>=3 and e["conclusion"] not in reached and all(x in reached for x in e["premises"]):
                reached.add(e["conclusion"]); changed=True
    return {"valid":not errors,"claims":len(ids),"edges":len(p["edges"]),"target_reached":p["target_claim"] in reached,"accepted_proof_reconstructed":False,"solution_claimed":False,"digest":digest(p)}
def strategy_value(x):
    d=x["dimensions"]; return (d["fertility"]+d["testability"]+d["formalizability"]+d["dependency_unlock"])/(0.5+d["false_progress_risk"])
def campaign(budget=1024):
    if budget<0: raise ValueError("negative budget")
    items=load("strategies.json")["items"]; ranked=sorted(items,key=lambda x:(-strategy_value(x),x["strategy_id"]))
    values=[strategy_value(x) for x in ranked]; total=sum(values); raw=[budget*v/total for v in values]
    units=[int(x) for x in raw]
    for i in sorted(range(len(raw)),key=lambda i:(-(raw[i]-units[i]),ranked[i]["strategy_id"]))[:budget-sum(units)]: units[i]+=1
    allocations=[{"strategy_id":x["strategy_id"],"units":u} for x,u in zip(ranked,units) if u]
    out={"schema":"omega-millennium-campaign/2","finite_budget_units":budget,"allocated_units":sum(units),"allocations":allocations,"logical_frontier_cells":14680064,"permanent_total_cap":None,"solution_claimed":False,"scientific_validation_claimed":False}
    out["digest"]=digest(out); return out
def benchmark():
    out={"schema":"omega-millennium-r02-benchmark/2","catalogs":atlas(),"problem_specs":problem_specs(),"poincare":poincare_benchmark(),"logical_frontier_cells":14680064,"status":"CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2","solution_claimed":False,"formal_proof_claimed":False,"scientific_validation_claimed":False,"permanent_total_cap":None}
    out["digest"]=digest(out); return out
def formal_skeleton(claim,target):
    marker={"lean4":"sorry","coq":"Admitted","isabelle_hol":"sorry"}.get(target,"PLACEHOLDER")
    return {"claim_id":claim.claim_id,"target":target,"text":f"{target}:{claim.claim_id}:{marker}","placeholders":[marker],"proof_complete":False,"source_digest":claim.digest}
'''

CLI=r'''"""CLI for Ω-MILLENNIUM-T∞ R0.2."""
import argparse,json
from pathlib import Path
from .core import atlas,benchmark,campaign,poincare_benchmark,problem_specs
def main(argv=None):
    p=argparse.ArgumentParser(prog="omega-millennium-r02"); s=p.add_subparsers(dest="cmd",required=True)
    for n in ("atlas","benchmark","specs","poincare-bench"):
        q=s.add_parser(n); q.add_argument("--output")
    q=s.add_parser("campaign"); q.add_argument("--budget",type=int,default=1024); q.add_argument("--output")
    a=p.parse_args(argv)
    result={"atlas":atlas,"benchmark":benchmark,"specs":problem_specs,"poincare-bench":poincare_benchmark}.get(a.cmd,lambda:campaign(a.budget))()
    text=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if a.output: Path(a.output).write_text(text)
    else: print(text,end="")
    return 0
if __name__=="__main__": raise SystemExit(main())
'''

INIT=r'''"""Ω-MILLENNIUM-T∞ R0.2 software research kernel."""
from .core import *
from .core import atlas,benchmark,campaign,poincare_benchmark,problem_specs,formal_skeleton
__version__="0.2.0"
'''

def generate():
    write("omega_millennium_t/r02/core.py",CORE)
    write("omega_millennium_t/r02/cli.py",CLI)
    write("omega_millennium_t/r02/__init__.py",INIT)
