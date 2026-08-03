"""Ω-SYNERGY-OS-T∞ R0.2 orchestration kernel: planning and evidence routing, not authority."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
from .adapters import AdaptationReceipt, adapt_records
from .contracts import GateDecision, ResidualRecord, SynergyConstellation, SynergyOSBundle, TransformationIR, stable_id
from .gates import GatePolicy, evaluate_constellation
from .graph import BridgeCandidate, TransformationGraph, discover_bridges, materialize_bridge
from .portfolio import PortfolioPolicy, select_portfolio
from .seed import top_constellations

DEFAULT_M_MINUS=[("M2-001","Similarity is not complementarity; require typed closure.","WARNING"),("M2-002","A generated adapter must declare information loss.","ERROR"),("M2-003","A score cannot compensate for a missing baseline, falsifier, rollback or provenance.","ERROR"),("M2-004","Two agents sharing the same source are not independent evidence.","WARNING"),("M2-005","Evidence integrity is not scientific truth.","WARNING"),("M2-006","Recursive generation requires proof, portfolio and stop governors.","CRITICAL"),("M2-007","No heuristic grants merge, release, publication, financial, IP or security authority.","CRITICAL"),("M2-008","Volume and logical addressability are not execution or external value.","WARNING"),("M2-009","A claim candidate is not a corroborated claim.","ERROR"),("M2-010","A plan remains bounded by compute, storage, CI, review and rollback capacity.","WARNING")]

@dataclass(slots=True)
class KernelPolicy:
    bridge_threshold:float=.45;max_bridge_candidates:int=250;materialize_top_bridges:int=24;include_seed_constellations:bool=True;gate_policy:GatePolicy=field(default_factory=GatePolicy);portfolio_policy:PortfolioPolicy=field(default_factory=PortfolioPolicy);governors:tuple[str,...]=("portfolio_governor","proof_os","oak_stopgate");source_heads:dict[str,str]=field(default_factory=dict)
    def __post_init__(self):
        if not 0<=self.bridge_threshold<=1:raise ValueError("bridge_threshold must be between 0 and 1")
        if self.max_bridge_candidates<0 or self.materialize_top_bridges<0:raise ValueError("bridge limits cannot be negative")

@dataclass(slots=True)
class CompileResult:
    bundle:SynergyOSBundle;adaptation_receipts:list[AdaptationReceipt];bridge_candidates:list[BridgeCandidate];graph_metrics:dict[str,Any]
    def to_dict(self):return {"bundle":self.bundle.to_dict(),"adaptation_receipts":[i.to_dict() for i in self.adaptation_receipts],"bridge_candidates":[i.to_dict() for i in self.bridge_candidates],"graph_metrics":self.graph_metrics}

class SynergyOSKernel:
    def __init__(self,policy=None):self.policy=policy or KernelPolicy()
    def _ingest(self,inputs):
        ir=TransformationIR(source_heads=dict(self.policy.source_heads));receipts=[]
        for kind in sorted(inputs):receipts.extend(adapt_records(kind,list(inputs[kind]),ir))
        for code,message,severity in DEFAULT_M_MINUS:ir.add_residual(ResidualRecord.build(code,message,severity))
        for receipt in receipts:
            for warning in receipt.warnings:ir.add_residual(ResidualRecord.build("ADAPTER_WARNING",warning,"WARNING",receipt.produced_node_ids,metadata={"adapter":receipt.adapter,"source_digest":receipt.source_digest}))
            for loss in receipt.declared_losses:ir.add_residual(ResidualRecord.build("ADAPTER_LOSS",loss,"ERROR",receipt.produced_node_ids,metadata={"adapter":receipt.adapter,"source_digest":receipt.source_digest}))
        return ir,receipts
    def _materialize_bridges(self,ir):
        candidates=discover_bridges(ir,threshold=self.policy.bridge_threshold,max_results=self.policy.max_bridge_candidates)
        for bridge in candidates[:self.policy.materialize_top_bridges]:
            interface,incoming,outgoing=materialize_bridge(ir,bridge)
            try:ir.add_node(interface)
            except ValueError:continue
            ir.add_edge(incoming);ir.add_edge(outgoing)
            if bridge.warnings:ir.add_residual(ResidualRecord.build("BRIDGE_REVIEW_REQUIRED",";".join(bridge.warnings),"WARNING",[bridge.provider_id,bridge.consumer_id,interface.id],metadata={"bridge_id":bridge.id,"score":bridge.score}))
        return candidates
    def _derived_constellations(self,ir,bridges):
        nodes={node.id:node for node in ir.nodes};result=[]
        for bridge in bridges[:min(32,len(bridges))]:
            provider,consumer=nodes.get(bridge.provider_id),nodes.get(bridge.consumer_id)
            if provider is None or consumer is None:continue
            evidence=sorted(set(provider.evidence_refs+consumer.evidence_refs));risk=max(provider.risk,consumer.risk,.35 if bridge.declared_losses else .15);uncertainty=min(1.0,(provider.uncertainty+consumer.uncertainty+(1.0-bridge.score))/3)
            result.append(SynergyConstellation(id=stable_id("CONST",bridge.id),name=f"Bridge: {provider.name} → {consumer.name}",systems=[provider.name,consumer.name],objective=f"Close typed need from {consumer.name} using outputs from {provider.name}.",transformations=[f"{provider.id} -> {bridge.required_interface}",f"{bridge.required_interface} -> {consumer.id}"],required_interfaces=[bridge.required_interface],metrics=["closure_success","schema_validity","provenance_integrity","loss_rate"],baselines=["provider alone","consumer alone","simplest manual adapter"],falsifiers=["adapter fails schema or round-trip contract","composition does not satisfy consumer acceptance criteria","declared losses exceed allowed threshold"],rollback=["remove generated interface","invalidate dependent evidence","restore prior graph"],risks=bridge.warnings or ["unmeasured_integration_gain"],domains=sorted(set(provider.metadata.get("domains",[])+consumer.metadata.get("domains",[]))) or ["integration"],closure_gain=bridge.score,evidence_strength=min(1.0,.15*len(evidence)),reuse=min(1.0,.4+.1*len(bridge.mappings)),product_value=.25,information_value=.55,reversibility=.95,integration_cost=min(1.0,.2+.15*len(bridge.mappings)+.2*bridge.lossy_matches),risk_score=risk,uncertainty=uncertainty,stage="S3_INTERFACE_DEFINED",evidence_refs=evidence,metadata={"provenance":[provider.id,consumer.id,bridge.id],"bridge_id":bridge.id,"isolated_sandbox":True,"human_gate_explicit":True,"derived":True}))
        return result
    def compile(self,inputs,*,available_evidence=()):
        ir,receipts=self._ingest(inputs);bridges=self._materialize_bridges(ir);constellations=self._derived_constellations(ir,bridges)
        if self.policy.include_seed_constellations:constellations=[*top_constellations(),*constellations]
        unique={}
        for item in constellations:
            if item.id in unique:ir.add_residual(ResidualRecord.build("CONSTELLATION_COLLISION",f"duplicate constellation id {item.id}","ERROR",[item.id]));continue
            unique[item.id]=item
        constellations=[unique[key] for key in sorted(unique)];evidence=sorted(set(available_evidence)|{ref for item in constellations for ref in item.evidence_refs})
        decisions=[evaluate_constellation(item,policy=self.policy.gate_policy,available_evidence=evidence,known_interfaces=item.required_interfaces,governors=self.policy.governors) for item in constellations]
        portfolio=select_portfolio(constellations,decisions,policy=self.policy.portfolio_policy);graph=TransformationGraph(ir);cycles=graph.dependency_cycles()
        for cycle in cycles:ir.add_residual(ResidualRecord.build("DEPENDENCY_CYCLE"," -> ".join(cycle),"ERROR",cycle))
        errors=ir.validate()
        for error in errors:ir.add_residual(ResidualRecord.build("IR_VALIDATION",error,"ERROR"))
        bundle=SynergyOSBundle("2.0",ir,constellations,sorted(decisions,key=lambda i:i.constellation_id),portfolio,list(ir.residuals))
        metrics={"coverage":graph.coverage(),"interface_entropy":graph.interface_entropy(),"dependency_cycles":cycles,"ir_validation_errors":errors,"nodes":len(ir.nodes),"edges":len(ir.edges),"bridge_candidates":len(bridges),"materialized_bridges":min(len(bridges),self.policy.materialize_top_bridges),"constellations":len(constellations),"selected":len(portfolio.selected_ids),"blocked":len(portfolio.blocked_ids),"authority":"A3","automatic_merge_allowed":False}
        return CompileResult(bundle,receipts,bridges,metrics)

def demo_inputs():
    return {"intent":[{"id":"INTENT-SYNERGY-DEMO","name":"Turn a repository intention into a proof-carrying review plan","inputs":["intent"],"outputs":["review_plan"],"requirements":["typed transformations","evidence","rollback"],"work_units":[{"id":"WU-SCAN","name":"Build repository twin","inputs":["repository"],"outputs":["repository_snapshot"]},{"id":"WU-PROOF","name":"Compile evidence bundle","inputs":["experiment"],"outputs":["evidence_bundle"]}]}],"creation":[{"id":"CREATION-REPOTWIN","name":"RepoTwin","repository":"demo/repo","paths":["omega_intent_t/r03"],"domains":["infrastructure"],"capabilities":[{"id":"CAP-REPO-SNAPSHOT","name":"Repository inventory","input_types":["repository"],"output_types":["repository_snapshot"],"confidence":.8}],"needs":[{"id":"NEED-PROOF","name":"Proof routing","input_types":["repository_snapshot"],"desired_output_types":["evidence_bundle"],"priority":.9}],"evidence":[{"id":"PR-338","source":"PR-338","strength":.8}],"uncertainty":.25,"risk":.2},{"id":"CREATION-PROOF-OS","name":"Evidence OS","repository":"demo/repo","paths":["omega_ci_proof_autonomy_t"],"domains":["proof"],"capabilities":[{"id":"CAP-EVIDENCE-BUNDLE","name":"Evidence bundle compiler","input_types":["repository_snapshot"],"output_types":["evidence_bundle"],"confidence":.85}],"needs":[{"id":"NEED-REPOSITORY-SNAPSHOT","name":"Repository impact snapshot","input_types":["repository"],"desired_output_types":["repository_snapshot"],"priority":.8}],"evidence":[{"id":"PR-347","source":"PR-347","strength":.8}],"uncertainty":.2,"risk":.25}]}
