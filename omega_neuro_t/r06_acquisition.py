from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Mapping, Tuple
from urllib.parse import quote

from .public_sources import get_public_source
from .r06_protocol import admission_gate, get_protocol


@dataclass(frozen=True)
class AcquisitionPlan:
    """Immutable plan linking a preregistered hypothesis to exact source assets."""

    plan_id: str
    hypothesis_id: str
    source_id: str
    protocol_hash: str
    source_version: str
    resource_locator: str
    asset_ids: Tuple[str, ...]
    requested_fields: Tuple[str, ...]
    grouping_keys: Tuple[str, ...]
    expected_formats: Tuple[str, ...]
    query_or_selection: str
    provenance_review_status: str = "REQUIRED"
    license_review_status: str = "REQUIRED"
    payload_hash_status: str = "PENDING_ACQUISITION"
    network_fetch_authorized: bool = False
    automatic_biological_promotion: bool = False

    def __post_init__(self) -> None:
        for name in (
            "plan_id",
            "hypothesis_id",
            "source_id",
            "protocol_hash",
            "source_version",
            "resource_locator",
            "query_or_selection",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if len(self.protocol_hash) != 64:
            raise ValueError("protocol_hash must be a SHA-256 digest")
        if not self.requested_fields or not self.grouping_keys or not self.expected_formats:
            raise ValueError("requested_fields, grouping_keys and expected_formats must be non-empty")
        gate = admission_gate(self.hypothesis_id, self.source_id)
        if gate["protocol_hash"] != self.protocol_hash:
            raise ValueError("acquisition plan protocol_hash does not match preregistration")
        if self.automatic_biological_promotion:
            raise ValueError("acquisition cannot automatically promote biological claims")

    def canonical_dict(self) -> Mapping[str, object]:
        return asdict(self)

    def digest(self) -> str:
        payload = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def allen_p1_plan(*, source_version: str, specimen_ids: Tuple[str, ...] = ()) -> AcquisitionPlan:
    """Freeze an Allen Cell Types metadata/morphology/ephys selection for P1.

    `source_version` is a user-assigned immutable evidence label that must map
    to recorded API/file identifiers and payload hashes in the evidence ledger.
    """

    hypothesis = "P1_DENDRITIC_ADDRESS"
    protocol = get_protocol(hypothesis)
    criteria = "model::ApiCellTypesSpecimenDetail,rma::criteria,[nr__reconstruction_type$nenull]"
    if specimen_ids:
        criteria += ",[id$in" + ",".join(specimen_ids) + "]"
    locator = "https://api.brain-map.org/api/v2/data/query.json?criteria=" + quote(criteria, safe=":,[]$'")
    return AcquisitionPlan(
        plan_id=f"allen-p1-{source_version}",
        hypothesis_id=hypothesis,
        source_id="allen_cell_types",
        protocol_hash=protocol.digest(),
        source_version=source_version,
        resource_locator=locator,
        asset_ids=specimen_ids,
        requested_fields=(
            "specimen_id",
            "species",
            "donor",
            "cortical_layer",
            "cell_type",
            "ephys_features",
            "nwb_file_id",
            "morphology_reconstruction_id",
            "swc_file_id",
        ),
        grouping_keys=("specimen_id", "donor_id"),
        expected_formats=("JSON metadata", "NWB", "SWC"),
        query_or_selection=criteria,
    )


def dandi_plan(
    *,
    hypothesis_id: str,
    dandiset_id: str,
    published_version: str,
    asset_ids: Tuple[str, ...] = (),
) -> AcquisitionPlan:
    if not dandiset_id or not published_version:
        raise ValueError("dandiset_id and published_version are required")
    source_id = "dandi_nwb"
    protocol = get_protocol(hypothesis_id)
    if source_id not in protocol.source_priority:
        raise ValueError(f"DANDI is not preregistered for {hypothesis_id}")
    locator = f"https://api.dandiarchive.org/api/dandisets/{dandiset_id}/versions/{published_version}/assets/"
    return AcquisitionPlan(
        plan_id=f"dandi-{dandiset_id}-{published_version}-{hypothesis_id.lower()}",
        hypothesis_id=hypothesis_id,
        source_id=source_id,
        protocol_hash=protocol.digest(),
        source_version=f"dandiset:{dandiset_id}@{published_version}",
        resource_locator=locator,
        asset_ids=asset_ids,
        requested_fields=(
            "dandiset_id",
            "published_version",
            "asset_id",
            "path",
            "contentUrl",
            "license",
            "subject/session metadata",
            "NWB/BIDS experimental metadata",
        ),
        grouping_keys=("subject_id", "session_id", "experiment_or_specimen_id"),
        expected_formats=("NWB", "BIDS/JSON metadata"),
        query_or_selection="published-version asset listing followed by hypothesis-specific variable mapping",
    )


def microns_p3_plan(
    *,
    materialization_version: str,
    coregistration_table: str = "coregistration_manual_v3",
    connectivity_tables: Tuple[str, ...] = ("synapses",),
) -> AcquisitionPlan:
    hypothesis = "P3_HIGHER_ORDER_WIRING"
    protocol = get_protocol(hypothesis)
    allowed_coreg = {"coregistration_manual_v3", "apl_functional_coreg_forward_v5"}
    if coregistration_table not in allowed_coreg:
        raise ValueError("coregistration_table must be a preregistered MICrONS table class")
    if not materialization_version:
        raise ValueError("materialization_version is required")
    asset_ids = (coregistration_table, *connectivity_tables)
    return AcquisitionPlan(
        plan_id=f"microns-p3-{materialization_version}-{coregistration_table}",
        hypothesis_id=hypothesis,
        source_id="microns_mm3",
        protocol_hash=protocol.digest(),
        source_version=f"materialization:{materialization_version}",
        resource_locator="https://www.microns-explorer.org/cortical-mm3",
        asset_ids=asset_ids,
        requested_fields=(
            "root_id",
            "pre_root_id",
            "post_root_id",
            "synapse_count_or_weight",
            "cell_type",
            "cortical_area",
            "depth",
            "session",
            "scan_idx",
            "unit_id",
            "coregistration_residual",
            "coregistration_score",
            "preregistered_functional_target",
        ),
        grouping_keys=("root_id", "session", "scan_idx", "unit_id"),
        expected_formats=("CAVE table export", "functional tabular/array export"),
        query_or_selection=(
            f"freeze materialization={materialization_version}; coregistration={coregistration_table}; "
            f"connectivity={','.join(connectivity_tables)}"
        ),
    )


def acquisition_plan_summary(plan: AcquisitionPlan) -> Mapping[str, object]:
    source = get_public_source(plan.source_id)
    return {
        **plan.canonical_dict(),
        "plan_hash": plan.digest(),
        "provider": source.provider,
        "provenance_review_required": True,
        "license_review_required": True,
        "payload_hash_required_after_fetch": True,
        "automatic_biological_promotion": False,
    }
