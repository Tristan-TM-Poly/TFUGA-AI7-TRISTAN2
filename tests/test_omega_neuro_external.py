import json

import pytest

from omega_neuro_t.dataset import observations_to_jsonl, synthetic_p1_dataset
from omega_neuro_t.external import load_verified_jsonl_bundle, run_p1_records_benchmark
from omega_neuro_t.provenance import build_manifest


def _write_bundle(tmp_path, access_mode="synthetic"):
    records = synthetic_p1_dataset(groups=12, trials_per_group=4, noise_scale=0.02)
    payload = observations_to_jsonl(records)
    manifest = build_manifest(
        payload,
        dataset_id="fixture",
        version="1",
        source_uri="local://fixture",
        license_id="test-only",
        access_mode=access_mode,
        citation="pytest fixture",
    )
    data_path = tmp_path / "data.jsonl"
    manifest_path = tmp_path / "manifest.json"
    data_path.write_bytes(payload)
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
    return data_path, manifest_path


def test_external_loader_rejects_payload_manifest_mismatch(tmp_path):
    data_path, manifest_path = _write_bundle(tmp_path)
    data_path.write_bytes(data_path.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="sha256"):
        load_verified_jsonl_bundle(data_path, manifest_path)


def test_external_benchmark_preserves_epistemic_gate_for_synthetic_source(tmp_path):
    data_path, manifest_path = _write_bundle(tmp_path, access_mode="synthetic")
    records, manifest = load_verified_jsonl_bundle(data_path, manifest_path)
    report = run_p1_records_benchmark(records, manifest, folds=3)
    assert report["source_claim"] == "synthetic"
    assert report["automatic_biological_promotion"] is False
    assert report["provenance_review_required"] is True
    assert report["oak"]["candidate_justified"] is True


def test_public_label_is_only_a_claim_and_never_auto_promotes(tmp_path):
    data_path, manifest_path = _write_bundle(tmp_path, access_mode="public")
    records, manifest = load_verified_jsonl_bundle(data_path, manifest_path)
    report = run_p1_records_benchmark(records, manifest, folds=3)
    assert report["source_claim"] == "claimed_empirical"
    assert report["provenance_review_required"] is True
    assert report["automatic_biological_promotion"] is False
