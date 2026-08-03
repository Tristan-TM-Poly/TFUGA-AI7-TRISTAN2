"""Generate R0.2 tests, schemas, docs, example and pyproject registration."""
from omega_millennium_r02_gen_common import ROOT,PROBLEMS,write

TESTS=r'''import json
from pathlib import Path
import pytest
from omega_millennium_t.r02.core import *

def stmt():
    return TypedStatement("s","Every x equals itself","forall x, x=x",(Symbol("x","Nat","N"),),(Quantifier(QuantifierKind.FORALL,"x",0),),"Z","discrete")

def claim(cid="c",problem="poincare"):
    return ClaimIR(cid,problem,stmt(),("a",),(),(),ClaimStatus.TYPE_CHECKED,False)

def test_statement_and_claim():
    assert stmt().validate()==()
    assert claim().validate()==()
    assert claim().digest==claim().digest

def test_bad_quantifier_and_solution_flag():
    bad=TypedStatement("s","x","x",(Symbol("x","Nat","N"),),(Quantifier(QuantifierKind.FORALL,"z",0),),"Z","d")
    assert bad.validate()
    assert ClaimIR("c","p",stmt(),status=ClaimStatus.TYPE_CHECKED,solution_claimed=True).validate()

def test_assumption_ledger():
    l=AssumptionLedger(); l.add(Assumption("a","compact"))
    l.add(Assumption("b","smooth",AssumptionState.INHERITED,("a",)))
    assert l.closure(("b",))==frozenset({"a","b"})
    l.discharge("a"); assert l.items["a"].state==AssumptionState.DISCHARGED

def test_hypergraph_closure_and_frontier():
    g=HyperProofGraph("poincare")
    for c in ("a","b","c","d"): g.add_claim(claim(c))
    g.add_edge(HyperEdge("e1",("a","b"),"c",3))
    g.add_edge(HyperEdge("e2",("c",),"d",3))
    assert g.closure(("a",),3)==frozenset({"a"})
    assert g.closure(("a","b"),3)==frozenset({"a","b","c","d"})
    assert g.frontier("c",("a",),3)==(("b",),)

def test_cycle_detector():
    g=HyperProofGraph("poincare")
    for c in ("a","b"): g.add_claim(claim(c))
    g.add_edge(HyperEdge("e1",("a",),"b",2)); g.add_edge(HyperEdge("e2",("b",),"a",2))
    assert g.cycles()==("a","b")

def test_catalog_atlas_and_specs():
    a=atlas(); s=problem_specs()
    assert a["valid"] is True and a["logical_frontier_cells"]==14_680_064
    assert a["counts"]["strategies"]==448 and a["counts"]["barriers"]==224 and a["counts"]["research_cells_seed"]==4096
    assert s["count"]==7 and s["open"]==6 and s["valid"] is True

@pytest.mark.parametrize("budget",[0,1,7,127,1024,10001])
def test_campaign_exact(budget):
    c=campaign(budget)
    assert c["allocated_units"]==budget
    assert c["permanent_total_cap"] is None
    assert c["solution_claimed"] is False

def test_poincare_positive_control():
    p=poincare_benchmark()
    assert p["valid"] is True and p["claims"]==48 and p["edges"]==72
    assert p["accepted_proof_reconstructed"] is False
    assert p["solution_claimed"] is False

def test_benchmark_deterministic_and_bounded():
    a=benchmark(); b=benchmark()
    assert a==b
    assert a["status"]=="CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2"
    assert a["solution_claimed"] is False
    assert a["formal_proof_claimed"] is False
    assert a["scientific_validation_claimed"] is False

@pytest.mark.parametrize("target",["lean4","coq","isabelle_hol","smtlib","human_latex"])
def test_formal_skeleton_incomplete(target):
    f=formal_skeleton(claim(),target)
    assert f["placeholders"] and f["proof_complete"] is False

def test_cli(tmp_path):
    from omega_millennium_t.r02.cli import main
    p=tmp_path/"b.json"
    assert main(["benchmark","--output",str(p)])==0
    assert json.loads(p.read_text())["status"]=="CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2"
'''

SCHEMA_SPEC={
"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object",
"required":["schema","problem_id","status","statement","formal_contract"],
"properties":{"schema":{"const":"omega-millennium-problem-spec/2"},"problem_id":{"type":"string"},
"status":{"enum":["open","solved_benchmark"]},"statement":{"type":"string"},
"formal_contract":{"type":"object","required":["solution_claimed"],"properties":{"solution_claimed":{"const":False}}}}}
SCHEMA_BENCH={
"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object",
"required":["status","logical_frontier_cells","solution_claimed","formal_proof_claimed","scientific_validation_claimed"],
"properties":{"status":{"const":"CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2"},
"logical_frontier_cells":{"const":14680064},"solution_claimed":{"const":False},
"formal_proof_claimed":{"const":False},"scientific_validation_claimed":{"const":False}}}
SCHEMA_CAMPAIGN={
"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object",
"required":["finite_budget_units","allocated_units","permanent_total_cap","solution_claimed"],
"properties":{"finite_budget_units":{"type":"integer","minimum":0},"allocated_units":{"type":"integer","minimum":0},
"permanent_total_cap":{"type":"null"},"solution_claimed":{"const":False}}}

ARCH='''# Ω-MILLENNIUM-T∞ R0.2

R0.2 is a software research architecture, not a solution to an open
Millennium Prize problem.

## Delivered

- seven canonical problem specifications;
- 448 research strategies;
- 64 lemma families;
- 32 falsifier families;
- 16 formal targets;
- 128 assumption patterns;
- 128 proof mutations;
- 224 barriers;
- 64 transfer bridges;
- quantified Claim-IR;
- assumption ledger;
- multi-premise proof hypergraph;
- 48-claim/72-edge Poincaré positive-control fixture;
- a 14,680,064-cell logical frontier;
- deterministic campaigns with no permanent total cap.

## Permanent OAK boundaries

```text
solution_claimed: false
formal_proof_claimed: false
scientific_validation_claimed: false
accepted_proof_reconstructed: false
finite_computation_is_not_proof: true
```

The line count is not a proof metric. Each catalog entry is a typed research
address, barrier, falsifier or formal target. Every actual run remains finite.
'''

def generate():
    write("tests/test_omega_millennium_r02.py",TESTS)
    write("schemas/omega_millennium_problem_spec_v2.schema.json",SCHEMA_SPEC)
    write("schemas/omega_millennium_benchmark_v2.schema.json",SCHEMA_BENCH)
    write("schemas/omega_millennium_campaign_v2.schema.json",SCHEMA_CAMPAIGN)
    write("docs/omega_millennium_t/r02/R02_ARCHITECTURE.md",ARCH)
    for pid,(title,status,statement,domains,outcomes,objects) in PROBLEMS.items():
        write(f"docs/omega_millennium_t/r02/problems/{pid}.md",f"# {title}\n\nStatus: `{status}`\n\n{statement}\n\nNo solution is claimed.\n")
    write("examples/omega_millennium_r02_demo.py",'from omega_millennium_t.r02.core import benchmark,campaign\nimport json\nprint(json.dumps({"benchmark":benchmark(),"campaign":campaign(4096)},sort_keys=True,indent=2))\n')
    py=ROOT/"pyproject.toml"
    text=py.read_text(encoding="utf-8")
    line='omega-millennium-r02 = "omega_millennium_t.r02.cli:main"\n'
    if line not in text:
        text=text.replace('\n[tool.pytest.ini_options]',f'\n{line}\n[tool.pytest.ini_options]')
        py.write_text(text,encoding="utf-8")
