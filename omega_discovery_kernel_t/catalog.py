"""Canonical Ω64 event taxonomy for Ω-DISCOVERY-KERNEL-T∞ R0.2.

The registry is deliberately explicit.  It turns event names into enforceable
contracts instead of allowing arbitrary strings to acquire epistemic meaning.
A registered event still records workflow evidence; it does not certify that a
scientific interpretation is true.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class EventTypeSpec:
    name: str
    family: str
    purpose: str
    required_parent_any: tuple[str, ...] = ()
    required_payload: tuple[str, ...] = ()
    requires_human_approval: bool = False
    reversible_default: bool = True
    scientific_gate: str = "workflow_record_only"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _spec(
    name: str,
    family: str,
    purpose: str,
    *,
    parents: Iterable[str] = (),
    payload: Iterable[str] = (),
    approval: bool = False,
    reversible: bool = True,
    gate: str = "workflow_record_only",
) -> EventTypeSpec:
    return EventTypeSpec(
        name=name,
        family=family,
        purpose=purpose,
        required_parent_any=tuple(parents),
        required_payload=tuple(payload),
        requires_human_approval=approval,
        reversible_default=reversible,
        scientific_gate=gate,
    )


# Eight families × eight event types = 64 canonical contracts.
EVENT_CATALOG: tuple[EventTypeSpec, ...] = (
    # 1. Ingestion and observation
    _spec(
        "ObservationEvent", "ingestion",
        "Record a source observation with provenance and domain context.",
        payload=("observation_kind",), gate="provenance_required_for_promotion",
    ),
    _spec(
        "ImportEvent", "ingestion",
        "Record ingestion of an external file, dataset, API response, or repository object.",
        payload=("source_locator", "content_hash"), gate="content_hash_required",
    ),
    _spec(
        "NormalizationEvent", "ingestion",
        "Record reversible normalization without replacing the raw observation.",
        parents=("ObservationEvent", "ImportEvent"), payload=("method",),
    ),
    _spec(
        "CalibrationEvent", "ingestion",
        "Record a calibration transform, reference, conditions, and uncertainty.",
        parents=("ObservationEvent", "ImportEvent"),
        payload=("reference_id", "validity_domain"), gate="calibration_traceability_required",
    ),
    _spec(
        "SegmentationEvent", "ingestion",
        "Partition an observation while preserving source coordinates.",
        parents=("ObservationEvent", "NormalizationEvent"), payload=("segments",),
    ),
    _spec(
        "FeatureExtractionEvent", "ingestion",
        "Extract candidate features without declaring them causal or diagnostic.",
        parents=("ObservationEvent", "NormalizationEvent", "SegmentationEvent"),
        payload=("feature_family",), gate="candidate_features_only",
    ),
    _spec(
        "ProvenanceEvent", "ingestion",
        "Attach exact source, locator, hash, license, and custody metadata.",
        parents=("ObservationEvent", "ImportEvent"), payload=("provenance_records",),
    ),
    _spec(
        "QualityGateEvent", "ingestion",
        "Accept, quarantine, or reject input quality under declared rules.",
        parents=("ObservationEvent", "ImportEvent", "CalibrationEvent"),
        payload=("decision", "criteria"), gate="quality_decision_not_truth",
    ),

    # 2. Epistemic objects
    _spec(
        "DefinitionEvent", "epistemic",
        "Introduce or revise a definition with scope and non-equivalences.",
        parents=("ObservationEvent", "ImportEvent"), payload=("term", "definition"),
    ),
    _spec(
        "ClaimEvent", "epistemic",
        "Record an atomic claim, assumptions, scope, polarity, and failure conditions.",
        parents=("ObservationEvent", "DefinitionEvent", "ImportEvent"),
        payload=("claim_id", "text", "failure_conditions"), gate="claim_is_not_proof",
    ),
    _spec(
        "AssumptionEvent", "epistemic",
        "Make a hidden or explicit assumption independently auditable.",
        parents=("ClaimEvent", "DefinitionEvent"), payload=("assumption",),
    ),
    _spec(
        "EquationEvent", "epistemic",
        "Bind a claim to an equation, symbols, units, and validity domain.",
        parents=("ClaimEvent", "DefinitionEvent"),
        payload=("expression", "variables", "validity_domain"), gate="dimensional_audit_required",
    ),
    _spec(
        "PredictionEvent", "epistemic",
        "Declare a preregistered prediction before the corresponding result.",
        parents=("ClaimEvent", "EquationEvent", "GeneratorCandidate"),
        payload=("predicted_observable", "acceptance_rule"), gate="prediction_before_result",
    ),
    _spec(
        "ContradictionEvent", "epistemic",
        "Record a candidate contradiction requiring scope and protocol comparison.",
        parents=("ClaimEvent", "ResultPacket", "ReplicationEvent"),
        payload=("claim_ids", "overlap_scope"), gate="candidate_not_logical_verdict",
    ),
    _spec(
        "ScopeRevisionEvent", "epistemic",
        "Narrow, expand, or separate the domain of a claim after evidence review.",
        parents=("ClaimEvent", "ContradictionEvent", "ResultPacket", "MMinusRule"),
        payload=("old_scope", "new_scope", "reason"),
    ),
    _spec(
        "RefutationEvent", "epistemic",
        "Record a scoped refutation supported by a failed discriminating test or proof.",
        parents=("ResultPacket", "ReplicationEvent", "ProofEvent"),
        payload=("refuted_claim_ids", "scope"), gate="scoped_refutation_only",
    ),

    # 3. Models and generators
    _spec(
        "GeneratorCandidate", "model",
        "Represent a continuous generator plus discrete and singular sectors.",
        parents=("ClaimEvent", "FeatureExtractionEvent", "EquationEvent"),
        payload=("continuous_generators", "discrete_events", "residual"),
        gate="candidate_generator_not_causal_law",
    ),
    _spec(
        "GeneratorFitEvent", "model",
        "Fit generator parameters under a declared objective and data split.",
        parents=("GeneratorCandidate", "ObservationEvent", "DatasetSplitEvent"),
        payload=("objective", "parameters", "training_split"),
    ),
    _spec(
        "ModelSelectionEvent", "model",
        "Compare candidate models with matched budgets and preregistered metrics.",
        parents=("GeneratorFitEvent", "BaselineComparison", "ResultPacket"),
        payload=("candidates", "criterion", "selected"), gate="selection_not_external_validation",
    ),
    _spec(
        "ReconstructionEvent", "model",
        "Reconstruct observed data and record residual structure.",
        parents=("GeneratorFitEvent", "GeneratorCandidate"),
        payload=("metric", "residual"), gate="reconstruction_not_prediction",
    ),
    _spec(
        "ForecastEvent", "model",
        "Produce an out-of-sample forecast with horizon and uncertainty.",
        parents=("GeneratorFitEvent", "PredictionEvent"),
        payload=("horizon", "forecast", "uncertainty"), gate="forecast_requires_held_out_result",
    ),
    _spec(
        "ResidualEvent", "model",
        "Represent structured unexplained error as a first-class object.",
        parents=("ReconstructionEvent", "ForecastEvent", "ResultPacket"),
        payload=("metric", "magnitude", "structure"),
    ),
    _spec(
        "SyndromeEvent", "model",
        "Classify deviation between expected and observed operators.",
        parents=("ResidualEvent", "GeneratorCandidate", "ResultPacket"),
        payload=("classification", "normalized_magnitude"), gate="diagnostic_not_discovery",
    ),
    _spec(
        "ModelRejectedEvent", "model",
        "Reject a model for a declared task, metric, and validity domain.",
        parents=("BaselineComparison", "ResultPacket", "ReplicationEvent"),
        payload=("model_id", "reason", "scope"), gate="task_scoped_rejection",
    ),

    # 4. Experiments and evidence production
    _spec(
        "ExperimentSpec", "experiment",
        "Specify a reversible, discriminating experiment with safety and rollback.",
        parents=("GeneratorCandidate", "PredictionEvent", "ContradictionEvent"),
        payload=("protocol", "success_criteria", "rollback"),
        gate="specification_not_authorization",
    ),
    _spec(
        "SimulationRun", "experiment",
        "Execute a deterministic or stochastic simulation under recorded configuration.",
        parents=("ExperimentSpec", "GeneratorCandidate"),
        payload=("configuration", "seed", "software_environment"),
    ),
    _spec(
        "MeasurementRun", "experiment",
        "Record a physical measurement with instrument, calibration, and uncertainty.",
        parents=("ExperimentSpec", "CalibrationEvent"),
        payload=("instrument_id", "calibration_id", "observations"),
        approval=True, gate="calibrated_measurement_required",
    ),
    _spec(
        "BaselineComparison", "experiment",
        "Compare candidate and baseline under matched data, tuning, and metrics.",
        parents=("SimulationRun", "MeasurementRun", "ResultPacket"),
        payload=("baseline_id", "candidate_metric", "baseline_metric"),
        gate="matched_budget_required",
    ),
    _spec(
        "AblationRun", "experiment",
        "Remove components to identify which mechanism produces an observed gain.",
        parents=("ExperimentSpec", "GeneratorCandidate", "ResultPacket"),
        payload=("removed_components", "metric"),
    ),
    _spec(
        "ReplicationEvent", "experiment",
        "Attempt independent or internal reproduction under an explicit relation to the original.",
        parents=("ResultPacket", "ExperimentClosedEvent"),
        payload=("replication_kind", "original_result_id", "outcome"),
        gate="independence_must_be_declared",
    ),
    _spec(
        "SensitivityRun", "experiment",
        "Sweep parameters, noise, seeds, or sampling density to measure robustness.",
        parents=("ExperimentSpec", "ResultPacket"),
        payload=("swept_variables", "robustness_metric"),
    ),
    _spec(
        "ExperimentClosedEvent", "experiment",
        "Close an experiment with immutable references to protocol, outputs, and deviations.",
        parents=("SimulationRun", "MeasurementRun", "ResultPacket"),
        payload=("closure_status", "artifact_hashes"),
    ),

    # 5. OAK governance
    _spec(
        "OAKTransition", "oak",
        "Record a justified status transition with evidence ancestry and residues.",
        parents=("ResultPacket", "RefutationEvent", "ScopeRevisionEvent", "ApprovalEvent"),
        payload=("from_status", "to_status", "cause"), gate="status_transition_not_truth",
    ),
    _spec(
        "PromotionEvent", "oak",
        "Request promotion after satisfying the target gate.",
        parents=("OAKTransition", "ReplicationEvent", "ProofEvent"),
        payload=("target_status", "gate_evidence"), approval=True,
        gate="human_review_required",
    ),
    _spec(
        "DemotionEvent", "oak",
        "Reduce status after contradiction, failed replication, drift, or invalid provenance.",
        parents=("OAKTransition", "RefutationEvent", "IncidentEvent", "ContradictionEvent"),
        payload=("old_status", "new_status", "reason"),
    ),
    _spec(
        "ApprovalEvent", "oak",
        "Record explicit authorization by an accountable human or policy gate.",
        parents=("ActionProposal", "ExperimentSpec", "PublicationEvent", "DeploymentEvent"),
        payload=("approved_object_id", "approver", "scope"), approval=True,
    ),
    _spec(
        "RejectionEvent", "oak",
        "Reject a proposal while preserving rationale and future reconsideration conditions.",
        parents=("ActionProposal", "PromotionEvent", "PublicationEvent", "DeploymentEvent"),
        payload=("rejected_object_id", "reason"),
    ),
    _spec(
        "QuarantineEvent", "oak",
        "Isolate an object with unresolved integrity, safety, provenance, or IP risk.",
        parents=("QualityGateEvent", "RiskAssessmentEvent", "IncidentEvent"),
        payload=("object_id", "reason", "release_conditions"),
    ),
    _spec(
        "ArchiveEvent", "oak",
        "Remove an object from active queues without deleting its history.",
        parents=("DemotionEvent", "RetirementEvent", "RejectionEvent"),
        payload=("object_id", "reason"),
    ),
    _spec(
        "RestorationEvent", "oak",
        "Restore an archived or quarantined object after explicit gate satisfaction.",
        parents=("ArchiveEvent", "QuarantineEvent", "ApprovalEvent"),
        payload=("object_id", "satisfied_conditions"), approval=True,
    ),

    # 6. Positive and negative memory
    _spec(
        "MMinusRule", "memory",
        "Convert failure or refutation into a reusable anti-error constraint.",
        parents=("ResultPacket", "RefutationEvent", "ModelRejectedEvent", "IncidentEvent"),
        payload=("context", "prohibited_inference", "reusable_rule"),
        gate="failure_ancestry_required",
    ),
    _spec(
        "MPlusRule", "memory",
        "Record a reproducible positive pattern without upgrading it to universal truth.",
        parents=("ResultPacket", "ReplicationEvent", "ProofEvent"),
        payload=("context", "reusable_pattern", "limits"),
    ),
    _spec(
        "CounterexampleEvent", "memory",
        "Preserve a concrete case violating a claim or implementation assumption.",
        parents=("ClaimEvent", "ResultPacket", "ProofEvent"),
        payload=("counterexample", "target_claim_ids"),
    ),
    _spec(
        "FailureContextEvent", "memory",
        "Capture environment, versions, data, and conditions surrounding an observed failure.",
        parents=("ResultPacket", "IncidentEvent", "ModelRejectedEvent"),
        payload=("failure_id", "environment", "conditions"),
    ),
    _spec(
        "AntiPatternEvent", "memory",
        "Generalize repeated failures into a detectable anti-pattern.",
        parents=("MMinusRule", "FailureContextEvent"),
        payload=("signature", "detection_rule"),
    ),
    _spec(
        "LessonEvent", "memory",
        "Document a bounded lesson linking evidence to a changed procedure.",
        parents=("MMinusRule", "MPlusRule", "CounterexampleEvent"),
        payload=("lesson", "affected_processes"),
    ),
    _spec(
        "ConstraintEvent", "memory",
        "Promote a lesson into a machine-checkable constraint.",
        parents=("LessonEvent", "MMinusRule", "ComplianceEvent"),
        payload=("constraint", "enforcement_point"),
    ),
    _spec(
        "MemoryPropagationEvent", "memory",
        "Apply a memory rule to related claims, models, experiments, or products.",
        parents=("MMinusRule", "MPlusRule", "ConstraintEvent"),
        payload=("source_memory_id", "target_ids", "effect"),
    ),

    # 7. Actions, publication, and value routing
    _spec(
        "ActionProposal", "action",
        "Propose a next action with expected information gain, risk, cost, and rollback.",
        parents=("OAKTransition", "MMinusRule", "MPlusRule", "ResidualEvent"),
        payload=("action", "expected_information_gain", "rollback"),
        gate="proposal_not_execution",
    ),
    _spec(
        "TaskPlannedEvent", "action",
        "Turn an approved action into bounded work with owner and acceptance criteria.",
        parents=("ActionProposal", "ApprovalEvent"),
        payload=("task", "owner", "acceptance_criteria"),
    ),
    _spec(
        "RollbackEvent", "action",
        "Record rollback or compensation after a failed or unsafe change.",
        parents=("IncidentEvent", "DeploymentEvent", "ExperimentClosedEvent"),
        payload=("target_id", "rollback_steps", "result"), approval=True,
    ),
    _spec(
        "CompensationEvent", "action",
        "Record an alternative compensating action when literal rollback is impossible.",
        parents=("IncidentEvent", "RollbackEvent"),
        payload=("harm_or_debt", "compensation"), approval=True,
    ),
    _spec(
        "PublicationEvent", "action",
        "Prepare or record publication with evidence, IP, license, and privacy gates.",
        parents=("PromotionEvent", "IPClassificationEvent", "ApprovalEvent"),
        payload=("artifact_id", "audience", "license"), approval=True,
        reversible=False, gate="human_ip_privacy_review_required",
    ),
    _spec(
        "IPClassificationEvent", "action",
        "Classify an artifact as public, patent candidate, trade secret, confidential, or licensed.",
        parents=("ClaimEvent", "ResultPacket", "ActionProposal"),
        payload=("object_id", "classification", "rationale"), approval=True,
    ),
    _spec(
        "ProductHypothesisEvent", "action",
        "Connect a capability to a user problem, offer, and falsifiable market hypothesis.",
        parents=("ResultPacket", "MPlusRule", "ActionProposal"),
        payload=("problem", "user_segment", "offer", "failure_condition"),
        gate="market_hypothesis_not_revenue",
    ),
    _spec(
        "CustomerEvidenceEvent", "action",
        "Record consented external customer evidence, outcome, and limitations.",
        parents=("ProductHypothesisEvent", "DeploymentEvent"),
        payload=("customer_segment", "evidence_kind", "outcome"),
        approval=True, gate="privacy_and_consent_required",
    ),

    # 8. Operations, economics, safety, and lifecycle
    _spec(
        "RevenueEvidenceEvent", "operations",
        "Record validated revenue evidence without extrapolating future demand.",
        parents=("CustomerEvidenceEvent", "DeploymentEvent"),
        payload=("amount", "currency", "transaction_type"), approval=True,
        gate="accounting_evidence_required",
    ),
    _spec(
        "CostEvidenceEvent", "operations",
        "Record compute, labor, equipment, maintenance, or opportunity cost.",
        parents=("ExperimentSpec", "DeploymentEvent", "TaskPlannedEvent"),
        payload=("amount", "currency", "cost_kind"),
    ),
    _spec(
        "RiskAssessmentEvent", "operations",
        "Assess scientific, safety, legal, privacy, IP, operational, and financial risks.",
        parents=("ActionProposal", "ExperimentSpec", "DeploymentEvent"),
        payload=("risk_vector", "mitigations"),
    ),
    _spec(
        "ComplianceEvent", "operations",
        "Record a compliance requirement, assessment, or unresolved obligation.",
        parents=("RiskAssessmentEvent", "PublicationEvent", "DeploymentEvent"),
        payload=("framework", "status", "evidence"), approval=True,
    ),
    _spec(
        "DeploymentEvent", "operations",
        "Record a bounded deployment with environment, version, approval, and rollback.",
        parents=("TaskPlannedEvent", "RiskAssessmentEvent", "ApprovalEvent"),
        payload=("environment", "version", "rollback"), approval=True,
        gate="deployment_requires_explicit_authorization",
    ),
    _spec(
        "IncidentEvent", "operations",
        "Record unexpected harm, failure, drift, outage, or governance breach.",
        parents=("DeploymentEvent", "MeasurementRun", "SimulationRun"),
        payload=("severity", "impact", "containment"),
    ),
    _spec(
        "MaintenanceEvent", "operations",
        "Record repair, recalibration, dependency update, or model refresh.",
        parents=("IncidentEvent", "SyndromeEvent", "CostEvidenceEvent"),
        payload=("maintenance_kind", "affected_objects", "result"),
    ),
    _spec(
        "RetirementEvent", "operations",
        "Retire a model, instrument, product, service, or workflow while preserving provenance.",
        parents=("MaintenanceEvent", "DemotionEvent", "CostEvidenceEvent"),
        payload=("object_id", "reason", "migration_or_archive"), approval=True,
        reversible=False,
    ),
)

EVENT_SPEC_BY_NAME = {spec.name: spec for spec in EVENT_CATALOG}
EVENT_TYPES = tuple(spec.name for spec in EVENT_CATALOG)
EVENT_FAMILIES = tuple(dict.fromkeys(spec.family for spec in EVENT_CATALOG))


def event_spec(name: str) -> EventTypeSpec:
    try:
        return EVENT_SPEC_BY_NAME[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported discovery event type: {name}") from exc


def catalog_manifest() -> dict[str, object]:
    return {
        "schema": "omega_discovery_kernel.event_catalog.v0.2",
        "event_type_count": len(EVENT_CATALOG),
        "family_count": len(EVENT_FAMILIES),
        "families": list(EVENT_FAMILIES),
        "events": [spec.to_dict() for spec in EVENT_CATALOG],
        "oak_boundary": (
            "Catalog membership defines a workflow contract, not scientific truth, "
            "causal validity, safety certification, patentability, or market value."
        ),
    }


assert len(EVENT_CATALOG) == 64
assert len(EVENT_SPEC_BY_NAME) == 64
assert len(EVENT_FAMILIES) == 8
