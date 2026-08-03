from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r03 import compile_max_atlas
from omega_millennium_t.r10 import audit_streaming_atlas, ingest_r03_max, verify_r03_max_source
from omega_millennium_t.r10.model import RuntimePolicy


def _policy() -> RuntimePolicy:
    return RuntimePolicy(batch_size=333, shard_target_bytes=65_536)


def _build_r03(tmp_path: Path) -> tuple[Path, dict]:
    output = tmp_path / "r03-max"
    report = compile_max_atlas(output)
    return output, report


def test_r03_fixture_receipts_are_reproduced_exactly(tmp_path: Path) -> None:
    source, r03_report = _build_r03(tmp_path)
    receipt = verify_r03_max_source(source)
    assert receipt["valid"] is True
    assert receipt["r03_manifest_digest"] == r03_report["manifest_digest"]
    assert receipt["r03_report_digest"] == r03_report["digest"]
    assert receipt["r03_problem_count"] == 72
    assert receipt["r03_cell_count"] == r03_report["research_cell_count"]
    assert len(receipt["artifacts"]) == 7


def test_r03_cells_stream_into_r10_and_bind_source_receipt(tmp_path: Path) -> None:
    source, r03_report = _build_r03(tmp_path)
    output = tmp_path / "r10"
    report = ingest_r03_max(source, output, policy=_policy())
    assert report["complete"] is True
    assert report["cell_count"] == r03_report["research_cell_count"]
    assert report["r03_manifest_digest_reproduced"] == r03_report["manifest_digest"]
    assert report["r03_report_digest_reproduced"] == r03_report["digest"]
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    compatibility = json.loads(
        (output / "r03_compatibility.json").read_text(encoding="utf-8")
    )
    assert manifest["source_compatibility"] == compatibility
    assert manifest["source_digest"] == r03_report["manifest_digest"]
    audit = audit_streaming_atlas(output)
    assert audit["valid"] is True, audit


def test_r03_partial_resume_matches_uninterrupted_manifest(tmp_path: Path) -> None:
    source, _ = _build_r03(tmp_path)
    full = tmp_path / "full"
    resumed = tmp_path / "resumed"
    ingest_r03_max(source, full, policy=_policy())
    first = ingest_r03_max(source, resumed, policy=_policy(), max_items=777)
    assert first["status"] == "checkpointed"
    second = ingest_r03_max(
        source,
        resumed,
        policy=_policy(),
        resume=True,
        clean=False,
    )
    assert second["complete"] is True
    full_manifest = json.loads((full / "manifest.json").read_text(encoding="utf-8"))
    resumed_manifest = json.loads((resumed / "manifest.json").read_text(encoding="utf-8"))
    assert resumed_manifest == full_manifest


def test_r03_artifact_tampering_fails_closed(tmp_path: Path) -> None:
    source, _ = _build_r03(tmp_path)
    cells_path = source / "research_cells.jsonl"
    with cells_path.open("a", encoding="utf-8") as handle:
        handle.write("{}\n")
    receipt = verify_r03_max_source(source)
    assert receipt["valid"] is False
    assert any(item.startswith("r03_artifact_sha256_mismatch:") for item in receipt["blockers"])
    with pytest.raises(ValueError, match="invalid R0.3 source"):
        ingest_r03_max(source, tmp_path / "r10", policy=_policy())


def test_r03_compatibility_file_tampering_is_detected(tmp_path: Path) -> None:
    source, _ = _build_r03(tmp_path)
    output = tmp_path / "r10"
    ingest_r03_max(source, output, policy=_policy())
    receipt_path = output / "r03_compatibility.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["r03_problem_count"] = 999
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    audit = audit_streaming_atlas(output)
    assert audit["valid"] is False
    assert "r03_compatibility_manifest_mismatch" in audit["errors"]
