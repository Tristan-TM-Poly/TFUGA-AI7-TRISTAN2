from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
import pytest
from omega_synergy_t.r02.adapters import adapt_records
from omega_synergy_t.r02.contracts import AuthorityLevel,EvidenceState,GateStatus,IREdge,IRNode,ObjectKind,RelationKind,SynergyConstellation,TransformationIR,canonical_json,digest,stable_id
from omega_synergy_t.r02.gates import evaluate_constellation
from omega_synergy_t.r02.graph import TransformationGraph,canonical_type,discover_bridges,materialize_bridge,type_similarity
from omega_synergy_t.r02.kernel import SynergyOSKernel,demo_inputs
from omega_synergy_t.r02.manifest import verify_bundle,write_bundle
from omega_synergy_t.r02.portfolio import PortfolioPolicy,select_portfolio
from omega_synergy_t.r02.proof import EvidenceContext,EvidenceEnvelope,assess_claim_coverage,assess_promotion,classify_evidence
from omega_synergy_t.r02.seed import top_constellations

def node(name,outputs=(),inputs=(),evidence=(),uncertainty=.2,risk=.1):return IRNode.build(ObjectKind.CREATION,name,source_identity=name,input_types=list(inputs),output_types=list(outputs),evidence_refs=list(evidence),uncertainty=uncertainty,risk=risk,provenance=[f"source:{name}"])
def constellation(name="Passing",**overrides):
    values=dict(id=stable_id("CONST",name),name=name,systems=["A","B"],objective="Close and measure.",transformations=["A -> adapter -> B"],required_interfaces=["adapter:A->B"],metrics=["closure_gain"],baselines=["A alone","simplest manual adapter"],falsifiers=["no gain"],rollback=["remove adapter"],risks=["integration"],domains=["infrastructure"],closure_gain=.9,evidence_strength=.8,reuse=.8,product_value=.6,information_value=.8,reversibility=.9,integration_cost=.3,risk_score=.2,uncertainty=.2,evidence_refs=["E1"],metadata={"provenance":["A","B"],"isolated_sandbox":True,"human_gate_explicit":True});values.update(overrides);return SynergyConstellation(**values)
def decision(item,status=GateStatus.ELIGIBLE_FOR_HUMAN_REVIEW):
    from omega_synergy_t.r02.contracts import GateDecision
    return GateDecision(item.id,status,[],[],item.evidence_refs,[])
def test_01_canonical_json_order():assert canonical_json({"b":2,"a":1})==canonical_json({"a":1,"b":2})
def test_02_digest_order():assert digest({"b":2,"a":1})==digest({"a":1,"b":2})
def test_03_source_date_epoch(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH","1785785117");from omega_synergy_t.r02.contracts import utc_now;assert utc_now()=="2026-08-03T19:25:17+00:00"
def test_04_stable_id():assert stable_id("X",1)==stable_id("X",1)!=stable_id("Y",1)
def test_05_node_bounds():
    with pytest.raises(ValueError):node("bad",uncertainty=1.1)
def test_06_duplicate_node():
    ir=TransformationIR();n=node("A");ir.add_node(n)
    with pytest.raises(ValueError):ir.add_node(n)
def test_07_dangling_edge():
    ir=TransformationIR();n=node("A");ir.add_node(n)
    with pytest.raises(ValueError):ir.add_edge(IREdge.build(n.id,"missing",RelationKind.PRODUCES))
def test_08_digest_ignores_generated_at():
    a,b=TransformationIR(generated_at="2026-01-01T00:00:00+00:00"),TransformationIR(generated_at="2026-02-01T00:00:00+00:00");a.add_node(node("A"));b.add_node(node("A"));assert a.content_digest==b.content_digest
def test_09_alias():assert canonical_type("proof_artifact")=="evidence"
def test_10_similarity():assert type_similarity("repository_snapshot","repotwin")==1.0
def test_11_no_name_only_bridge():
    ir=TransformationIR();ir.add_node(node("Evidence",outputs=["x"]));ir.add_node(node("Evidence consumer",inputs=["y"]));assert not discover_bridges(ir,threshold=.8)
def test_12_exact_bridge():
    ir=TransformationIR();ir.add_node(node("A",outputs=["evidence_bundle"],evidence=["E"]));ir.add_node(node("B",inputs=["evidence_bundle"]));assert discover_bridges(ir)[0].exact_matches==1
def test_13_alias_bridge():
    ir=TransformationIR();ir.add_node(node("A",outputs=["proof_artifact"],evidence=["E"]));ir.add_node(node("B",inputs=["evidence"]));assert discover_bridges(ir)[0].alias_matches==1
def test_14_materialize_bridge():
    ir=TransformationIR();a=node("A",outputs=["claim_candidate"],evidence=["E"]);b=node("B",inputs=["claim"]);ir.add_node(a);ir.add_node(b);bridge=discover_bridges(ir)[0];interface,e1,e2=materialize_bridge(ir,bridge);assert interface.metadata["review_only"] and e1.declared_losses==e2.declared_losses
def test_15_cycle():
    ir=TransformationIR();a,b=node("A"),node("B");ir.add_node(a);ir.add_node(b);ir.add_edge(IREdge.build(a.id,b.id,RelationKind.DEPENDS_ON));ir.add_edge(IREdge.build(b.id,a.id,RelationKind.DEPENDS_ON));assert TransformationGraph(ir).dependency_cycles()
def test_16_impact():
    ir=TransformationIR();a,b=node("A"),node("B");ir.add_node(a);ir.add_node(b);ir.add_edge(IREdge.build(a.id,b.id,RelationKind.PRODUCES));assert b.id in TransformationGraph(ir).impact_closure([a.id])
def test_17_gate_missing_interface():assert evaluate_constellation(constellation(required_interfaces=[]),available_evidence=["E1"]).status==GateStatus.BLOCKED
def test_18_gate_missing_baseline():assert "simplest_baseline" in evaluate_constellation(constellation(baselines=["A alone"]),available_evidence=["E1"]).missing_gates
def test_19_gate_missing_falsifier():assert evaluate_constellation(constellation(falsifiers=[]),available_evidence=["E1"]).status==GateStatus.BLOCKED
def test_20_gate_human_review():
    result=evaluate_constellation(constellation(),available_evidence=["E1"]);assert result.status==GateStatus.ELIGIBLE_FOR_HUMAN_REVIEW and not result.automatic_merge_allowed
def test_21_recursive_governor():
    item=constellation(metadata={"provenance":["x"],"isolated_sandbox":True,"human_gate_explicit":True,"recursive_generation":True});assert evaluate_constellation(item,available_evidence=["E1"],governors=[]).status==GateStatus.BLOCKED
def test_22_portfolio_blocks():
    good,bad=constellation("good"),constellation("bad");selected=select_portfolio([good,bad],[decision(good),decision(bad,GateStatus.BLOCKED)],policy=PortfolioPolicy(budget=10,max_items=2));assert bad.id not in selected.selected_ids
def test_23_portfolio_budget():
    item=constellation();selected=select_portfolio([item],[decision(item)],policy=PortfolioPolicy(budget=.01,max_items=1));assert not selected.selected_ids
def test_24_portfolio_diversity():
    a=constellation("a",domains=["science"]);b=constellation("b",domains=["product"]);selected=select_portfolio([a,b],[decision(a),decision(b)],policy=PortfolioPolicy(budget=10,max_items=2));assert set(selected.diversity_domains)=={"science","product"}
def test_25_intent_adapter():
    ir=TransformationIR();adapt_records("intent",[{"id":"I","name":"I","work_units":[{"name":"W"}]}],ir);assert any(n.kind==ObjectKind.WORK_UNIT for n in ir.nodes)
def test_26_creation_adapter():
    ir=TransformationIR();adapt_records("creation",[{"id":"C","name":"C","capabilities":[{"name":"cap"}],"needs":[{"name":"need"}]}],ir);kinds={n.kind for n in ir.nodes};assert ObjectKind.CAPABILITY in kinds and ObjectKind.NEED in kinds
def test_27_unknown_adapter():
    with pytest.raises(ValueError):adapt_records("unknown",[],TransformationIR())
def test_28_evidence_stale():
    e=EvidenceEnvelope.build("C","test",{},environment_digest="A");assert classify_evidence(e,EvidenceContext(environment_digest="B"))==EvidenceState.STALE
def test_29_evidence_expired():
    e=EvidenceEnvelope.build("C","test",{},observed_at="2026-01-01T00:00:00+00:00",expires_at="2026-01-02T00:00:00+00:00",environment_digest="A");assert classify_evidence(e,EvidenceContext(now="2026-02-01T00:00:00+00:00",environment_digest="B"))==EvidenceState.EXPIRED
def test_30_evidence_revoked():
    e=EvidenceEnvelope.build("C","test",{});e.revoked=True;assert classify_evidence(e,EvidenceContext())==EvidenceState.REVOKED
def test_31_coverage_blocks():
    c=assess_claim_coverage("C",positive_tests=1,negative_tests=0,required_tests=1,passed_required_tests=1);assert c.blocked_reasons
def test_32_coverage_complete():
    c=assess_claim_coverage("C",positive_tests=2,negative_tests=2,required_tests=2,passed_required_tests=2,oracle_quality=1,falsifier_present=True,provenance_complete=True,environment_recorded=True,limitations_declared=True,required_evidence_kinds=["test"],present_evidence_kinds=["test"]);assert c.score==1 and not c.blocked_reasons
def test_33_promotion_current():
    c=assess_claim_coverage("C",positive_tests=1,negative_tests=1,required_tests=1,passed_required_tests=1,oracle_quality=1,falsifier_present=True,provenance_complete=True,environment_recorded=True,limitations_declared=True);assert assess_promotion("C",[EvidenceEnvelope.build("C","test",{})],c).eligible_for_human_review
def test_34_promotion_no_merge():
    c=assess_claim_coverage("C",positive_tests=1,negative_tests=1,required_tests=1,passed_required_tests=1,oracle_quality=1,falsifier_present=True,provenance_complete=True,environment_recorded=True,limitations_declared=True);p=assess_promotion("C",[EvidenceEnvelope.build("C","test",{})],c);assert not p.automatic_merge_allowed and not p.automatic_publication_allowed
def test_35_seed_six():assert len(top_constellations())==6 and len({i.id for i in top_constellations()})==6
def test_36_kernel_demo():
    result=SynergyOSKernel().compile(demo_inputs(),available_evidence=["PR-338","PR-347"]);assert result.bundle.authority==AuthorityLevel.A3_REVIEW_CANDIDATE and result.graph_metrics["nodes"]>0
def test_37_kernel_deterministic(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH","1785785117");a=SynergyOSKernel().compile(demo_inputs());b=SynergyOSKernel().compile(demo_inputs());assert a.bundle.ir.content_digest==b.bundle.ir.content_digest
def test_38_bundle_verify(tmp_path):
    result=SynergyOSKernel().compile(demo_inputs());write_bundle(result,tmp_path);assert verify_bundle(tmp_path)["valid"]
def test_39_cli_demo_audit(tmp_path):
    out=tmp_path/"bundle";env={**os.environ,"SOURCE_DATE_EPOCH":"1785785117"};root=Path(__file__).resolve().parents[1];p=subprocess.run([sys.executable,"-m","omega_synergy_t.r02","demo","--output-dir",str(out)],cwd=root,env=env,text=True,capture_output=True);assert p.returncode==0,p.stderr;q=subprocess.run([sys.executable,"-m","omega_synergy_t.r02","audit","--bundle-dir",str(out)],cwd=root,env=env,text=True,capture_output=True);assert q.returncode==0 and json.loads(q.stdout)["valid"]
