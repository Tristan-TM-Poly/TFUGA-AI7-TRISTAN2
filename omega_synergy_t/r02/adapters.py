"""Loss-declaring adapters into the Ω-TRANSFORMATION-IR."""
from __future__ import annotations

from dataclasses import dataclass, field, is_dataclass, asdict
from typing import Any, Iterable, Mapping, Sequence

from .contracts import AuthorityLevel, EpistemicStatus, IREdge, IRNode, ObjectKind, RelationKind, TransformationIR, digest, stable_id


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping): return dict(value)
    if is_dataclass(value): return asdict(value)
    if hasattr(value, "to_dict"):
        result = value.to_dict()
        if isinstance(result, Mapping): return dict(result)
    if hasattr(value, "__dict__"): return dict(value.__dict__)
    raise TypeError(f"unsupported adapter input: {type(value).__name__}")


def _value(record: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in record and record[name] is not None: return record[name]
    return default


def _strings(value: Any) -> list[str]:
    if value is None: return []
    if isinstance(value, str): return [value] if value.strip() else []
    if isinstance(value, Mapping): return [str(key) for key in value]
    if isinstance(value, Iterable): return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _risk(record: Mapping[str, Any]) -> float:
    raw = _value(record, "risk", "risk_score", "aggregate_risk", default=0.0)
    if isinstance(raw, Mapping): raw = max([float(item) for item in raw.values()] or [0.0])
    try: return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError): return 0.0


def _uncertainty(record: Mapping[str, Any]) -> float:
    raw = _value(record, "uncertainty", "uncertainties", default=1.0)
    if isinstance(raw, Mapping):
        values = [float(item) for item in raw.values()] or [1.0]
        raw = sum(values) / len(values)
    try: return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError): return 1.0


def _status(value: Any, default: EpistemicStatus) -> EpistemicStatus:
    return {"idea": EpistemicStatus.HYPOTHESIS, "structured": EpistemicStatus.FORMALIZED, "formalized": EpistemicStatus.FORMALIZED, "implemented": EpistemicStatus.IMPLEMENTED, "executable": EpistemicStatus.IMPLEMENTED, "tested": EpistemicStatus.TESTED, "benchmarked": EpistemicStatus.MEASURED, "measured": EpistemicStatus.MEASURED, "replicated": EpistemicStatus.REPLICATED, "canonical": EpistemicStatus.CANONICAL, "refuted": EpistemicStatus.REFUTED, "superseded": EpistemicStatus.SUPERSEDED}.get(str(value or "").lower(), default)


@dataclass(slots=True)
class AdaptationReceipt:
    adapter: str
    source_digest: str
    source_identity: str
    produced_node_ids: list[str]
    produced_edge_ids: list[str]
    warnings: list[str] = field(default_factory=list)
    declared_losses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"adapter": self.adapter, "source_digest": self.source_digest, "source_identity": self.source_identity, "produced_node_ids": sorted(set(self.produced_node_ids)), "produced_edge_ids": sorted(set(self.produced_edge_ids)), "warnings": sorted(set(self.warnings)), "declared_losses": sorted(set(self.declared_losses))}


def _receipt(adapter: str, record: Mapping[str, Any], identity: str) -> AdaptationReceipt:
    return AdaptationReceipt(adapter, digest(record), identity, [], [])


def _safe_add_node(ir: TransformationIR, node: IRNode, receipt: AdaptationReceipt) -> None:
    existing = next((item for item in ir.nodes if item.id == node.id), None)
    if existing is None: ir.add_node(node)
    elif existing.to_dict() != node.to_dict(): receipt.warnings.append(f"node_collision:{node.id}")
    receipt.produced_node_ids.append(node.id)


def _safe_add_edge(ir: TransformationIR, edge: IREdge, receipt: AdaptationReceipt) -> None:
    try: ir.add_edge(edge)
    except ValueError as exc:
        receipt.warnings.append(str(exc)); return
    receipt.produced_edge_ids.append(edge.id)


def adapt_intent(record_like: Any, ir: TransformationIR) -> AdaptationReceipt:
    record = _mapping(record_like); identity = str(_value(record, "id", "intent_id", "name", default=digest(record)[:16])); receipt = _receipt("intent", record, identity)
    intent = IRNode.build(ObjectKind.INTENT, str(_value(record, "name", "title", "objective", default=f"Intent {identity}")), source_identity=identity, version=str(_value(record, "version", "schema_version", default="0")), status=_status(_value(record, "status"), EpistemicStatus.FORMALIZED), authority=AuthorityLevel.A1_DRAFT, input_types=_strings(_value(record, "input_types", "inputs")), output_types=_strings(_value(record, "output_types", "outputs", "deliverables")), claims=_strings(_value(record, "claims")), provenance=_strings(_value(record, "provenance", "sources")), uncertainty=_uncertainty(record), risk=_risk(record), metadata={"requirements": _value(record, "requirements", default=[]), "completion_contract": _value(record, "completion_contract", default={}), "source_type": str(_value(record, "source_type", default="intent_contract"))})
    _safe_add_node(ir, intent, receipt)
    work_units = _value(record, "work_units", "tasks", "steps", default=[])
    for index, raw in enumerate(work_units or []):
        unit = _mapping(raw) if not isinstance(raw, str) else {"name": raw}; unit_identity = str(_value(unit, "id", "name", default=f"{identity}:{index}"))
        node = IRNode.build(ObjectKind.WORK_UNIT, str(_value(unit, "name", "title", "objective", default=f"Work unit {index+1}")), source_identity=(identity, unit_identity), status=_status(_value(unit, "status"), EpistemicStatus.FORMALIZED), authority=AuthorityLevel.A1_DRAFT, input_types=_strings(_value(unit, "input_types", "inputs")), output_types=_strings(_value(unit, "output_types", "outputs", "artifacts")), capabilities=_strings(_value(unit, "capabilities")), needs=_strings(_value(unit, "needs", "dependencies")), claims=_strings(_value(unit, "claims")), provenance=[intent.id, *_strings(_value(unit, "provenance"))], uncertainty=_uncertainty(unit), risk=_risk(unit), metadata={"acceptance_criteria": _value(unit, "acceptance_criteria", default=[])})
        _safe_add_node(ir, node, receipt); _safe_add_edge(ir, IREdge.build(intent.id, node.id, RelationKind.PRODUCES, confidence=1.0), receipt)
    for index, raw in enumerate(_value(record, "generators", "generator_specifications", default=[]) or []):
        generator = _mapping(raw) if not isinstance(raw, str) else {"name": raw}
        node = IRNode.build(ObjectKind.GENERATOR, str(_value(generator, "name", "id", default=f"Generator {index+1}")), source_identity=(identity,index,generator), status=EpistemicStatus.FORMALIZED, authority=AuthorityLevel.A1_DRAFT, input_types=_strings(_value(generator,"input_types","inputs")), output_types=_strings(_value(generator,"output_types","outputs")), capabilities=_strings(_value(generator,"capabilities")), provenance=[intent.id], uncertainty=_uncertainty(generator), risk=_risk(generator), metadata={"bounded": bool(_value(generator,"bounded",default=True))})
        _safe_add_node(ir,node,receipt); _safe_add_edge(ir,IREdge.build(intent.id,node.id,RelationKind.PRODUCES,confidence=0.9),receipt)
    if not work_units: receipt.warnings.append("intent_has_no_work_units")
    if not intent.output_types: receipt.declared_losses.append("intent_outputs_not_typed")
    return receipt


def adapt_creation(record_like: Any, ir: TransformationIR) -> AdaptationReceipt:
    record=_mapping(record_like); identity=str(_value(record,"id","name",default=digest(record)[:16])); receipt=_receipt("creation_dna",record,identity)
    capabilities_raw=list(_value(record,"capabilities",default=[]) or []); needs_raw=list(_value(record,"needs",default=[]) or []); evidence_raw=list(_value(record,"evidence",default=[]) or [])
    creation=IRNode.build(ObjectKind.CREATION,str(_value(record,"name",default=f"Creation {identity}")),source_identity=identity,version=str(_value(record,"version",default="0")),status=_status(_value(record,"maturity","status"),EpistemicStatus.FORMALIZED),authority=AuthorityLevel.A2_LOCAL_EXECUTION if capabilities_raw else AuthorityLevel.A1_DRAFT,capabilities=[str(_value(_mapping(i),"id","name",default=i)) for i in capabilities_raw],needs=[str(_value(_mapping(i),"id","name",default=i)) for i in needs_raw],evidence_refs=[str(_value(_mapping(i),"hash","id","source",default="")) for i in evidence_raw],provenance=_strings(_value(record,"paths","provenance")),uncertainty=_uncertainty(record),risk=_risk(record),metadata={"repository":_value(record,"repository",default=""),"domains":_strings(_value(record,"domains")),"permissions":_value(record,"permissions",default={}),"expansion_options":_value(record,"expansion_options",default=[])})
    _safe_add_node(ir,creation,receipt)
    for index,raw in enumerate(capabilities_raw):
        item=_mapping(raw) if not isinstance(raw,str) else {"name":raw}; cap_identity=str(_value(item,"id","name",default=f"{identity}:cap:{index}"))
        capability=IRNode.build(ObjectKind.CAPABILITY,str(_value(item,"name",default=cap_identity)),source_identity=(identity,cap_identity),status=EpistemicStatus.IMPLEMENTED,authority=AuthorityLevel.A2_LOCAL_EXECUTION,input_types=_strings(_value(item,"input_types","inputs")),output_types=_strings(_value(item,"output_types","outputs")),capabilities=[cap_identity],provenance=[creation.id,*_strings(_value(item,"provenance"))],uncertainty=1.0-max(0.0,min(1.0,float(_value(item,"confidence",default=0.0)))),risk=_risk(item),metadata={"domains":_strings(_value(item,"domains")),"invariants":_strings(_value(item,"invariants")),"declared_losses":_strings(_value(item,"losses","declared_losses"))})
        _safe_add_node(ir,capability,receipt); _safe_add_edge(ir,IREdge.build(creation.id,capability.id,RelationKind.EXPOSES,confidence=1.0),receipt)
    for index,raw in enumerate(needs_raw):
        item=_mapping(raw) if not isinstance(raw,str) else {"name":raw}; need_identity=str(_value(item,"id","name",default=f"{identity}:need:{index}"))
        need=IRNode.build(ObjectKind.NEED,str(_value(item,"name",default=need_identity)),source_identity=(identity,need_identity),status=EpistemicStatus.HYPOTHESIS,authority=AuthorityLevel.A1_DRAFT,input_types=_strings(_value(item,"input_types","inputs")),output_types=_strings(_value(item,"desired_output_types","output_types","outputs")),needs=[need_identity],provenance=[creation.id,*_strings(_value(item,"provenance"))],uncertainty=max(0.0,min(1.0,1.0-float(_value(item,"priority",default=0.5))*0.4)),metadata={"domains":_strings(_value(item,"domains")),"acceptance_criteria":_value(item,"acceptance_criteria",default=[])})
        _safe_add_node(ir,need,receipt); _safe_add_edge(ir,IREdge.build(creation.id,need.id,RelationKind.EXPOSES,confidence=1.0),receipt)
    if not evidence_raw: receipt.warnings.append("creation_has_no_evidence")
    if not capabilities_raw and not needs_raw: receipt.declared_losses.append("creation_has_no_typed_capability_need_surface")
    return receipt


def adapt_experiment(record_like: Any, ir: TransformationIR) -> AdaptationReceipt:
    record=_mapping(record_like); identity=str(_value(record,"id","experiment_id",default=digest(record)[:16])); receipt=_receipt("experiment",record,identity); candidate_id=str(_value(record,"candidate_id","subject_id",default=""))
    node=IRNode.build(ObjectKind.EXPERIMENT,str(_value(record,"name","hypothesis",default=f"Experiment {identity}")),source_identity=identity,status=EpistemicStatus.FORMALIZED,authority=AuthorityLevel.A2_LOCAL_EXECUTION,input_types=["candidate_hypothesis","baseline","test_fixture"],output_types=["measurement","evidence_bundle","residual"],claims=_strings(_value(record,"hypothesis")),provenance=_strings(_value(record,"provenance")),uncertainty=_uncertainty(record),risk=_risk(record),metadata={"candidate_id":candidate_id,"baselines":_value(record,"baselines",default=[]),"ablations":_value(record,"ablations",default=[]),"controls":_value(record,"controls",default=[]),"metrics":_value(record,"metrics",default=[]),"success_criteria":_value(record,"success_criteria",default=[]),"failure_criteria":_value(record,"failure_criteria",default=[]),"stopping_rules":_value(record,"stopping_rules",default=[]),"rollback":_value(record,"rollback",default=[])})
    _safe_add_node(ir,node,receipt)
    if candidate_id and any(i.id==candidate_id for i in ir.nodes): _safe_add_edge(ir,IREdge.build(node.id,candidate_id,RelationKind.TESTS,confidence=1.0),receipt)
    elif candidate_id: receipt.warnings.append(f"experiment_subject_not_ingested:{candidate_id}")
    if not node.metadata["baselines"]: receipt.warnings.append("experiment_has_no_baseline")
    return receipt


def adapt_pr_gene(record_like: Any, ir: TransformationIR) -> AdaptationReceipt:
    record=_mapping(record_like); identity=str(_value(record,"id","pr_id","title",default=digest(record)[:16])); receipt=_receipt("pr_gene",record,identity); candidate_id=str(_value(record,"candidate_id",default=""))
    node=IRNode.build(ObjectKind.PR_GENE,str(_value(record,"title","name",default=f"PR Gene {identity}")),source_identity=identity,status=EpistemicStatus.FORMALIZED,authority=AuthorityLevel.A1_DRAFT,input_types=["reviewed_change_plan","test_contract"],output_types=["draft_pull_request","validation_receipt","rollback_plan"],capabilities=_strings(_value(record,"capabilities_added")),needs=_strings(_value(record,"needs_resolved")),provenance=_strings(_value(record,"paths")),uncertainty=_uncertainty(record),risk=_risk(record),metadata={"intention":_value(record,"intention",default=""),"candidate_id":candidate_id,"tests":_value(record,"tests",default=[]),"dependencies":_value(record,"dependencies",default=[]),"conflicts":_value(record,"conflicts",default=[]),"rollback":_value(record,"rollback",default=[]),"merge_authority":False})
    _safe_add_node(ir,node,receipt)
    if candidate_id and any(i.id==candidate_id for i in ir.nodes): _safe_add_edge(ir,IREdge.build(node.id,candidate_id,RelationKind.IMPLEMENTS,confidence=0.9),receipt)
    if not node.metadata["tests"]: receipt.warnings.append("pr_gene_has_no_tests")
    if not node.metadata["rollback"]: receipt.warnings.append("pr_gene_has_no_rollback")
    return receipt


def adapt_portfolio_record(record_like: Any, ir: TransformationIR) -> AdaptationReceipt:
    record=_mapping(record_like); identity=str(_value(record,"id","prototype_id","name",default=digest(record)[:16])); receipt=_receipt("portfolio_record",record,identity); maturity=str(_value(record,"maturity","level",default="P0")); status=EpistemicStatus.OBSERVED
    if maturity in {"P2","P3","P4","P5","P6","P7","P8"}: status=EpistemicStatus.IMPLEMENTED
    if maturity in {"P3","P4","P5","P6","P7","P8"}: status=EpistemicStatus.TESTED
    if maturity in {"P4","P5","P6","P7","P8"}: status=EpistemicStatus.MEASURED
    if maturity=="P8": status=EpistemicStatus.REPLICATED
    node=IRNode.build(ObjectKind.PORTFOLIO_DECISION,str(_value(record,"name","title",default=f"Portfolio record {identity}")),source_identity=identity,status=status,authority=AuthorityLevel.A3_REVIEW_CANDIDATE,evidence_refs=_strings(_value(record,"evidence_refs","evidence")),provenance=_strings(_value(record,"repository","paths","provenance")),uncertainty=_uncertainty(record),risk=_risk(record),metadata={"maturity":maturity,"dimensions":_value(record,"dimensions","scores",default={}),"signals":_value(record,"signals",default={}),"next_action":_value(record,"next_action",default="collect_missing_evidence"),"selected":bool(_value(record,"selected",default=False))})
    _safe_add_node(ir,node,receipt)
    if maturity in {"P0","P1","P2","P3","P4"} and not node.evidence_refs: receipt.warnings.append("portfolio_record_lacks_external_evidence")
    return receipt


def adapt_promotion_proof(record_like: Any, ir: TransformationIR) -> AdaptationReceipt:
    record=_mapping(record_like); identity=str(_value(record,"id","proof_id",default=digest(record)[:16])); receipt=_receipt("promotion_proof",record,identity); subject_id=str(_value(record,"claim_id","subject_id","candidate_id",default="")); eligible=bool(_value(record,"eligible","eligible_for_human_review",default=False))
    node=IRNode.build(ObjectKind.PROMOTION_PROOF,str(_value(record,"name",default=f"Promotion proof {identity}")),source_identity=identity,status=EpistemicStatus.TESTED if eligible else EpistemicStatus.FORMALIZED,authority=AuthorityLevel.A3_REVIEW_CANDIDATE,input_types=["claim","current_evidence","coverage_assessment"],output_types=["human_review_candidate" if eligible else "blocked_promotion"],evidence_refs=_strings(_value(record,"evidence_bundle_ids","evidence_refs")),provenance=_strings(_value(record,"provenance")),uncertainty=_uncertainty(record),risk=_risk(record),metadata={"subject_id":subject_id,"eligible_for_human_review":eligible,"blocked_reasons":_value(record,"blocked_reasons",default=[]),"automatic_merge_allowed":False,"human_review_required":True})
    _safe_add_node(ir,node,receipt)
    if subject_id and any(i.id==subject_id for i in ir.nodes): _safe_add_edge(ir,IREdge.build(node.id,subject_id,RelationKind.PROMOTES,confidence=1.0),receipt)
    elif subject_id: receipt.warnings.append(f"promotion_subject_not_ingested:{subject_id}")
    if not node.evidence_refs: receipt.warnings.append("promotion_proof_has_no_named_evidence")
    return receipt


ADAPTERS={"intent":adapt_intent,"intent_contract":adapt_intent,"creation":adapt_creation,"creation_dna":adapt_creation,"experiment":adapt_experiment,"experiment_plan":adapt_experiment,"pr_gene":adapt_pr_gene,"portfolio":adapt_portfolio_record,"portfolio_record":adapt_portfolio_record,"promotion_proof":adapt_promotion_proof}


def adapt_records(kind: str, records: Sequence[Any], ir: TransformationIR) -> list[AdaptationReceipt]:
    normalized=kind.strip().lower()
    if normalized not in ADAPTERS: raise ValueError(f"unsupported adapter kind: {kind}")
    return [ADAPTERS[normalized](record,ir) for record in records]


def adaptation_digest(receipts: Sequence[AdaptationReceipt]) -> str:
    return stable_id("ADAPT",[receipt.to_dict() for receipt in receipts],length=32)
