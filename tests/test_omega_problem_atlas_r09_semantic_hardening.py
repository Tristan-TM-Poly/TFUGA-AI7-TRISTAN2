from __future__ import annotations

import json
import runpy
from pathlib import Path

from omega_millennium_t.r09 import compile_promotion_gate


def _bundle() -> dict:
    return runpy.run_path("tests/test_omega_problem_atlas_r09_promotion_gate.py")["_build_bundle"]()


def _receipt(tmp_path: Path, bundle: dict) -> dict:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    output = tmp_path / "output"
    compile_promotion_gate(path, output)
    return json.loads((output / "promotion_receipt.json").read_text(encoding="utf-8"))


def test_reproducibility_digests_must_be_sha256(tmp_path: Path) -> None:
    bundle = _bundle()
    check = next(item for item in bundle["checks"] if item["check_kind"] == "reproducibility_snapshot")
    check["metadata"]["code_digest"] = "short"
    receipt = _receipt(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert any(item.endswith(":code_digest") for item in receipt["blockers"])


def test_metadata_references_must_resolve(tmp_path: Path) -> None:
    bundle = _bundle()
    novelty = next(item for item in bundle["checks"] if item["check_kind"] == "novelty_review")
    novelty["metadata"]["comparison_reference_ids"] = ["ref.unknown"]
    receipt = _receipt(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert any(item.startswith("check_metadata_reference_missing:") for item in receipt["blockers"])


def test_evidence_cannot_postdate_request(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["evidence"][0]["observed_at"] = "2026-08-04T18:00:00Z"
    receipt = _receipt(tmp_path, bundle)
    assert "evidence_after_request:ref.primary" in receipt["blockers"]


def test_review_cannot_postdate_request(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["checks"][0]["reviewed_at"] = "2026-08-04T18:00:00Z"
    receipt = _receipt(tmp_path, bundle)
    assert any(item.startswith("review_after_request:") for item in receipt["blockers"])


def test_signature_cannot_predate_request(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["signatures"][0]["signed_at"] = "2026-08-02T18:00:00Z"
    receipt = _receipt(tmp_path, bundle)
    assert "signature_before_request:sig.gate" in receipt["blockers"]


def test_search_cutoff_cannot_be_after_request(tmp_path: Path) -> None:
    bundle = _bundle()
    literature = next(item for item in bundle["checks"] if item["check_kind"] == "literature_search")
    literature["metadata"]["search_cutoff"] = "2026-08-04"
    receipt = _receipt(tmp_path, bundle)
    assert any(item.startswith("search_cutoff_after_request:") for item in receipt["blockers"])


def test_public_signature_reference_must_be_external_receipt(tmp_path: Path) -> None:
    bundle = _bundle()
    bundle["signatures"][0]["signature_ref"] = "sha256:" + bundle["signatures"][0]["payload_digest"]
    receipt = _receipt(tmp_path, bundle)
    assert "external_signature_reference_invalid:sig.gate" in receipt["blockers"]
