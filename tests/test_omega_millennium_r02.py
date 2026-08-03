import json
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
