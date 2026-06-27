from __future__ import annotations

import hashlib
import json

from local_digest.demo_data import write_demo_dataset
from local_digest.manifest import (
    ReviewInfo,
    SourceInfo,
    build_manifest,
    checksum_entries,
    discover_output_files,
    sha256_file,
    write_checksum_registry,
    write_manifest,
)


def test_sha256_file_matches_hashlib(tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("alpha\n", encoding="utf-8")

    assert sha256_file(sample) == hashlib.sha256(b"alpha\n").hexdigest()


def test_build_manifest_records_source_review_and_outputs(tmp_path) -> None:
    write_demo_dataset(tmp_path, seed=11, count=2)
    files = discover_output_files(tmp_path)
    source = SourceInfo(adapter="demo", query="seed=11", filters={"kind": "sample"}, limits={"count": 2})
    review = ReviewInfo(status="draft", notes=["generated sample data"])

    manifest = build_manifest(
        source=source,
        review=review,
        outputs=files,
        base_dir=tmp_path,
        git_commit="abc123",
        generated_sample_data=True,
        created_at_utc="2026-01-01T00:00:00Z",
    )

    payload = manifest.to_dict()
    assert payload["git_commit"] == "abc123"
    assert payload["source"]["adapter"] == "demo"
    assert payload["source"]["limits"]["count"] == 2
    assert payload["review"]["status"] == "draft"
    assert payload["generated_sample_data"] is True
    assert len(payload["outputs"]) == 5
    assert all(item["sha256"] for item in payload["outputs"])


def test_write_manifest_and_checksum_registry(tmp_path) -> None:
    write_demo_dataset(tmp_path, seed=3, count=1)
    files = discover_output_files(tmp_path)
    entries = checksum_entries(files, base_dir=tmp_path)
    manifest = build_manifest(
        source=SourceInfo(adapter="demo", query="seed=3"),
        outputs=files,
        base_dir=tmp_path,
        created_at_utc="2026-01-01T00:00:00Z",
    )

    manifest_path = write_manifest(tmp_path / "manifest.json", manifest)
    registry_path = write_checksum_registry(tmp_path / "checksums.json", entries)

    manifest_payload = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    registry_payload = json.loads((tmp_path / "checksums.json").read_text(encoding="utf-8"))

    assert manifest_path.endswith("manifest.json")
    assert registry_path.endswith("checksums.json")
    assert manifest_payload["manifest_version"] == "1.0"
    assert "demo_dataset.json" in registry_payload
