from dataclasses import replace

import pytest

from omega_neuro_t.r06_acquisition import acquisition_plan_summary, allen_p1_plan
from omega_neuro_t.r06_evidence import EvidenceAssetRecord, EvidenceBundleRecord, mapping_digest
from omega_neuro_t.r06_protocol import get_protocol


ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64


def _asset() -> EvidenceAssetRecord:
    plan = allen_p1_plan(source_version="probe-v1", specimen_ids=("313862022",))
    return EvidenceAssetRecord(
        source_id="allen_cell_types",
        source_version="probe-v1",
        asset_id="specimen:313862022",
        resource_uri="https://celltypes.brain-map.org/",
        payload_sha256=ZERO,
        payload_bytes=123,
        acquisition_plan_hash=plan.digest(),
        license_id="REVIEWED-SOURCE-SPECIFIC",
        citation="Allen Cell Types Database specimen 313862022",
        variable_mapping_hash=ONE,
        grouping_mapping_hash=TWO,
        provenance_review_status="REVIEWED",
        license_review_status="REVIEWED",
        retrieval_date="2026-08-09",
    )


def test_asset_record_requires_real_hash_shapes_and_never_promotes():
    asset = _asset()
    assert len(asset.digest()) == 64
    assert asset.automatic_biological_promotion is False
    with pytest.raises(ValueError):
        replace(asset, payload_sha256="bad")
    with pytest.raises(ValueError):
        replace(asset, automatic_biological_promotion=True)


def test_mapping_digest_is_deterministic_and_semantic():
    first = mapping_digest({"target": "x", "group": ["cell", "donor"]})
    second = mapping_digest({"group": ["cell", "donor"], "target": "x"})
    changed = mapping_digest({"target": "y", "group": ["cell", "donor"]})
    assert first == second
    assert changed != first


def test_evidence_bundle_binds_assets_to_executable_protocol():
    asset = _asset()
    plan = allen_p1_plan(source_version="probe-v1", specimen_ids=("313862022",))
    protocol = get_protocol("P1_DENDRITIC_ADDRESS")
    bundle = EvidenceBundleRecord(
        bundle_id="allen-p1-probe-v1",
        hypothesis_id="P1_DENDRITIC_ADDRESS",
        protocol_hash=protocol.digest(),
        acquisition_plan_hash=plan.digest(),
        asset_record_hashes=(asset.digest(),),
        variable_contract_hash=mapping_digest({"target": "held_out_ephys_feature"}),
        split_contract_hash=mapping_digest({"group": "specimen_id", "outer": "donor_id"}),
        negative_control_contract_hash=mapping_digest({"control": "permute_morphology_within_strata"}),
    )
    assert len(bundle.digest()) == 64
    assert bundle.status == "EVIDENCE_PREPARED_NOT_CLAIM_PROMOTED"
    assert bundle.automatic_biological_promotion is False
    with pytest.raises(ValueError):
        replace(bundle, protocol_hash=THREE)
    with pytest.raises(ValueError):
        replace(bundle, automatic_biological_promotion=True)
