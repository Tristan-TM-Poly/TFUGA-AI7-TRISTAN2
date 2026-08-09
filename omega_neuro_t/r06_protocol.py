from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from typing import Dict, Mapping, Tuple

from .public_sources import PublicSourceSpec, get_public_source


@dataclass(frozen=True)
class FrozenEvaluationProtocol:
    """Pre-registered evaluation contract for one hypothesis/source family."""

    protocol_id: str
    hypothesis_id: str
    source_priority: Tuple[str, ...]
    target_definition: str
    group_key_policy: str
    baseline_family: Tuple[str, ...]
    candidate_family: Tuple[str, ...]
    metrics: Tuple[str, ...]
    ablations: Tuple[str, ...]
    negative_controls: Tuple[str, ...]
    confounds: Tuple[str, ...]
    split_policy: str
    minimum_external_conditions: int = 1
    preregistered: bool = True
    automatic_biological_promotion: bool = False
    protocol_version: str = "r0.6.0"

    def __post_init__(self) -> None:
        for name in (
            "protocol_id",
            "hypothesis_id",
            "target_definition",
            "group_key_policy",
            "split_policy",
            "protocol_version",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        for name in (
            "source_priority",
            "baseline_family",
            "candidate_family",
            "metrics",
            "negative_controls",
            "confounds",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if self.minimum_external_conditions < 1:
            raise ValueError("minimum_external_conditions must be >= 1")
        if not self.preregistered:
            raise ValueError("R0.6 protocols must be preregistered")
        if self.automatic_biological_promotion:
            raise ValueError("evaluation scores cannot automatically promote biological claims")
        for source_id in self.source_priority:
            source = get_public_source(source_id)
            if self.hypothesis_id not in source.candidate_hypotheses:
                raise ValueError(f"source {source_id} does not declare support for {self.hypothesis_id}")

    def canonical_dict(self) -> Mapping[str, object]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def mutated(self, **changes: object) -> "FrozenEvaluationProtocol":
        """Return a changed protocol; its digest must change if semantics change."""

        return replace(self, **changes)


PROTOCOLS: Dict[str, FrozenEvaluationProtocol] = {
    "P1_DENDRITIC_ADDRESS": FrozenEvaluationProtocol(
        protocol_id="omega-neuro-r06-p1-v1",
        hypothesis_id="P1_DENDRITIC_ADDRESS",
        source_priority=("allen_cell_types", "dandi_nwb"),
        target_definition=(
            "predict a preregistered held-out electrophysiology response/feature using the same target across baseline "
            "and morphology-aware candidate models"
        ),
        group_key_policy="specimen/cell is indivisible; donor/session becomes an outer holdout when repeated units exist",
        baseline_family=("cell-level scalar/ephys covariates without dendritic morphology",),
        candidate_family=("baseline plus preregistered morphology/address descriptors",),
        metrics=("held_out_MSE", "OAK_penalized_score", "between_fold_uncertainty"),
        ablations=("remove_morphology", "remove_address_features", "coarsen_address_resolution"),
        negative_controls=("permute morphology/address labels within admissible strata",),
        confounds=("species", "donor", "cell_type", "cortical_layer", "recording_protocol", "morphology_availability"),
        split_policy="group-safe folds plus at least one external condition not used to choose features",
        minimum_external_conditions=1,
    ),
    "P2_SYNAPTIC_STATE_TENSOR": FrozenEvaluationProtocol(
        protocol_id="omega-neuro-r06-p2-v1",
        hypothesis_id="P2_SYNAPTIC_STATE_TENSOR",
        source_priority=("dandi_nwb", "allen_cell_types"),
        target_definition=(
            "predict a preregistered held-out response using a scalar state proxy versus a multidimensional state "
            "representation available in the selected experiment"
        ),
        group_key_policy="subject/specimen/session identity is indivisible according to the experimental hierarchy",
        baseline_family=("single scalar state proxy",),
        candidate_family=("multidimensional state tensor available before target observation",),
        metrics=("held_out_MSE", "OAK_penalized_score", "between_fold_uncertainty"),
        ablations=("remove_context", "collapse_state_dimensions", "remove_interactions"),
        negative_controls=("permute context/state dimensions within admissible experimental strata",),
        confounds=("subject", "specimen", "session", "stimulus", "protocol", "cell_type", "batch"),
        split_policy="group-safe folds with no future/target leakage and external-condition reproduction",
        minimum_external_conditions=1,
    ),
    "P3_HIGHER_ORDER_WIRING": FrozenEvaluationProtocol(
        protocol_id="omega-neuro-r06-p3-v1",
        hypothesis_id="P3_HIGHER_ORDER_WIRING",
        source_priority=("microns_mm3",),
        target_definition=(
            "predict a preregistered functional/connectivity observable from pairwise descriptors versus higher-order "
            "motif descriptors without using the target to define motifs"
        ),
        group_key_policy=(
            "neuron/root-id and repeated functional unit identities are indivisible; materialization and coregistration "
            "confidence are retained as provenance"
        ),
        baseline_family=("pairwise strength/degree/recurrence descriptors",),
        candidate_family=("baseline plus order-3/order-4 motif and context interactions",),
        metrics=("held_out_MSE", "OAK_penalized_score", "between_fold_uncertainty", "negative_control_gap"),
        ablations=("collapse_to_pairwise", "remove_context", "remove_higher_order_interactions"),
        negative_controls=("permute motif assignments while preserving admissible degree/context strata",),
        confounds=(
            "cell_type",
            "cortical_area",
            "depth",
            "proofreading_state",
            "coregistration_confidence",
            "materialization_version",
        ),
        split_policy="root-id-safe held-out groups with manually verified coregistration subset as preferred confirmation",
        minimum_external_conditions=1,
    ),
}


def get_protocol(hypothesis_id: str) -> FrozenEvaluationProtocol:
    try:
        return PROTOCOLS[hypothesis_id]
    except KeyError as exc:
        raise KeyError(f"unknown R0.6 hypothesis protocol: {hypothesis_id}") from exc


def admission_gate(hypothesis_id: str, source_id: str) -> Mapping[str, object]:
    protocol = get_protocol(hypothesis_id)
    source: PublicSourceSpec = get_public_source(source_id)
    if source_id not in protocol.source_priority:
        raise ValueError(f"source {source_id} is not preregistered for {hypothesis_id}")
    return {
        "protocol_id": protocol.protocol_id,
        "protocol_hash": protocol.digest(),
        "hypothesis_id": hypothesis_id,
        "source_id": source_id,
        "source_provider": source.provider,
        "preregistered": protocol.preregistered,
        "provenance_review_required": source.provenance_review_required,
        "license_review_required": source.license_review_required,
        "asset_version_required": True,
        "payload_hash_required": True,
        "group_leakage_barrier_required": True,
        "negative_control_required": True,
        "automatic_biological_promotion": False,
        "status": "ADMISSIBLE_FOR_DATA_PREPARATION_NOT_CLAIM_PROMOTION",
    }


def protocol_registry() -> Mapping[str, Mapping[str, object]]:
    return {
        hypothesis_id: {
            **protocol.canonical_dict(),
            "protocol_hash": protocol.digest(),
        }
        for hypothesis_id, protocol in sorted(PROTOCOLS.items())
    }
