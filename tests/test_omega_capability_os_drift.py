from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_capability_os_t.drift import (
    benchmark_fixture,
    benchmark_fixture_corpus,
    generate_drift_cases,
    load_fixture_corpus,
    load_fixture_corpus_file,
)


FIXTURE_PATH = Path("examples/capability_os_r06_fixture_corpus.json")


def _fixtures():
    return load_fixture_corpus_file(FIXTURE_PATH)


def test_r06_fixture_corpus_has_explicit_source_fidelity_boundaries():
    fixtures = _fixtures()
    assert len(fixtures) == 6
    captured = [item for item in fixtures if item.source_kind == "captured_sanitized"]
    synthetic = [item for item in fixtures if item.source_kind == "contract_synthetic"]
    assert len(captured) == 3
    assert len(synthetic) == 3
    assert {item.provider for item in fixtures} == {
        "github",
        "files",
        "drive",
        "gmail",
        "calendar",
        "web",
    }
    assert all(item.source_fidelity for item in fixtures)


def test_r06_fixture_corpus_contains_no_live_private_identifiers():
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    forbidden = (
        "mail.google.com/",
        "calendar.google.com/calendar/",
        "drive.google.com/file/d/",
        "file_00000000",
        "1apvamnhSPdxBjD7xh2i7MFMddI1nQXHR",
        "1HrE0t56lz_La4TOF0NFPfmhyeCcxr2Tz",
    )
    for token in forbidden:
        assert token not in text
    assert "raw_private_content_committed" in text
    assert '"raw_private_content_committed": false' in text


def test_r06_generates_deterministic_case_counts():
    fixtures = _fixtures()
    counts = {item.provider: len(generate_drift_cases(item)) for item in fixtures}
    assert counts["github"] == 20
    assert all(counts[name] == 19 for name in counts if name != "github")


def test_r06_benchmark_classifies_all_115_cases_without_mismatch():
    report = benchmark_fixture_corpus(_fixtures())
    assert report["status"] == "PASS", report["classification_mismatches"]
    assert report["fixture_count"] == 6
    assert report["captured_sanitized_fixture_count"] == 3
    assert report["contract_synthetic_fixture_count"] == 3
    assert report["case_count"] == 115
    assert report["correct_count"] == 115
    assert report["mismatch_count"] == 0
    assert report["classification_accuracy"] == 1.0
    assert report["breaking_detection_rate"] == 1.0


@pytest.mark.parametrize("provider", ["github", "files", "drive", "gmail", "calendar", "web"])
def test_r06_provider_matrix_is_closed(provider):
    report = benchmark_fixture_corpus(_fixtures())
    row = report["providers"][provider]
    assert row["fixtures"] == 1
    assert row["mismatches"] == 0
    assert row["classification_accuracy"] == 1.0
    assert row["breaking_detection_rate"] == 1.0


def test_r06_benign_wrappers_survive_with_exact_normalized_signature():
    for fixture in _fixtures():
        report = benchmark_fixture(fixture)
        benign = [
            case
            for case in report["cases"]
            if case["expected"] == "SURVIVE"
        ]
        assert benign
        assert all(case["actual"] == "SURVIVE" for case in benign), report


def test_r06_identity_misbinding_and_missing_outputs_fail_closed():
    for fixture in _fixtures():
        report = benchmark_fixture(fixture)
        by_suffix = {
            case["case_id"].split(":")[-1]: case
            for case in report["cases"]
        }
        assert by_suffix["connector-mismatch"]["actual"] == "REJECT"
        assert by_suffix["action-mismatch"]["actual"] == "REJECT"
        assert by_suffix["required-output-dropped"]["actual"] == "REJECT"


def test_r06_provider_errors_become_typed_failure_receipts():
    for fixture in _fixtures():
        report = benchmark_fixture(fixture)
        provider_error = next(
            case
            for case in report["cases"]
            if case["case_id"].endswith(":provider-error")
        )
        assert provider_error["actual"] == "FAILURE_RECEIPT"
        assert provider_error["correct"] is True


def test_r06_semantic_type_and_null_drift_are_detected_not_silently_counted_compatible():
    for fixture in _fixtures():
        report = benchmark_fixture(fixture)
        semantic = [
            case
            for case in report["cases"]
            if case["expected"] == "DETECT"
        ]
        assert semantic
        assert all(case["actual"] in {"DEGRADED", "REJECT"} for case in semantic)
        assert all(case["correct"] for case in semantic)


def test_r06_candidate_bound_github_stale_sha_is_rejected():
    fixture = next(item for item in _fixtures() if item.provider == "github")
    report = benchmark_fixture(fixture)
    stale = next(
        case
        for case in report["cases"]
        if case["case_id"].endswith(":candidate-sha-stale")
    )
    assert stale["actual"] == "REJECT"
    assert stale["correct"] is True


def test_r06_schema_breaks_emit_m_minus_candidates_without_calling_them_real_incidents():
    report = benchmark_fixture_corpus(_fixtures())
    findings = report["m_minus_candidates"]
    assert findings
    assert all(item["classification"] == "M_MINUS_CANDIDATE" for item in findings)
    assert all(item["kind"] == "schema_drift_observation" for item in findings)


def test_r06_report_is_deterministic_for_same_corpus():
    first = benchmark_fixture_corpus(_fixtures())
    second = benchmark_fixture_corpus(_fixtures())
    assert first == second


def test_r06_invalid_fixture_source_kind_fails_closed():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["fixtures"][0]["source_kind"] = "pretend_live"
    with pytest.raises(ValueError, match="source_kind"):
        load_fixture_corpus(payload)


def test_r06_baseline_contract_does_not_upgrade_synthetic_fixture_to_live_evidence():
    fixtures = _fixtures()
    synthetic = [item for item in fixtures if item.source_kind == "contract_synthetic"]
    assert synthetic
    for fixture in synthetic:
        assert "synthetic" in fixture.source_fidelity
        assert "synthetic" in str(fixture.provenance.get("basis", "")).lower()
