import json
from pathlib import Path

from rosette_tristan.bench_corpus import (
    CorpusCase,
    CorpusManifest,
    create_minimal_corpus,
    load_manifest,
    validate_corpus,
    validate_manifest,
)


def test_create_minimal_corpus_validates(tmp_path: Path):
    manifest_path = create_minimal_corpus(tmp_path)
    assert manifest_path.exists()
    report = validate_corpus(manifest_path)
    assert report["oak_status"] == "corpus_valid_not_certified"
    assert report["case_count"] == 2
    assert report["corpus_quality_score"] == 1.0


def test_load_manifest_roundtrip(tmp_path: Path):
    manifest_path = create_minimal_corpus(tmp_path)
    manifest = load_manifest(manifest_path)
    assert manifest.name == "rosette_minimal_annotated_corpus"
    assert {case.case_id for case in manifest.cases} == {"clean_text_001", "paged_text_001"}


def test_validate_manifest_catches_missing_file(tmp_path: Path):
    manifest = CorpusManifest(
        name="bad",
        version="0.1",
        cases=[CorpusCase(case_id="missing", case_type="clean_text", path="missing.txt")],
    )
    findings = validate_manifest(manifest, root=tmp_path)
    assert any(finding.severity == "error" and "missing file" in finding.message for finding in findings)


def test_validate_manifest_catches_unknown_type():
    manifest = CorpusManifest(
        name="bad",
        version="0.1",
        cases=[CorpusCase(case_id="bad", case_type="weird", path="x.txt")],
    )
    findings = validate_manifest(manifest)
    assert any("unsupported case_type" in finding.message for finding in findings)


def test_validate_corpus_writes_expected_json_shape(tmp_path: Path):
    manifest_path = create_minimal_corpus(tmp_path)
    report = validate_corpus(manifest_path)
    encoded = json.dumps(report)
    decoded = json.loads(encoded)
    assert decoded["name"] == "rosette_minimal_annotated_corpus"
    assert "oak_rules" in decoded
