from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

from omega_capability_os_t.github_memory import GitHubPRSource
from omega_capability_os_t.github_pr_llmt_measurements import (
    compile_reconstruction_blob_measurements,
)


def _filegraph():
    return {
        "schema": "omega-pr-llmt-target-filegraph/v0.2.0",
        "fingerprint": "g" * 64,
        "targets": [
            {
                "ref": "pr:example/repo#10",
                "head_sha": "1" * 40,
                "changed_file_count": 2,
                "changed_files": ["pkg/a.py", "pkg/b.py"],
            },
            {
                "ref": "pr:example/repo#11",
                "head_sha": "2" * 40,
                "changed_file_count": 2,
                "changed_files": ["pkg/a.py", "pkg/b.py"],
            },
        ],
        "reconstruction_pairs": [
            {
                "source_ref": "pr:example/repo#10",
                "reconstruction_ref": "pr:example/repo#11",
                "shared_file_count": 2,
                "shared_files": ["pkg/a.py", "pkg/b.py"],
                "source_changed_file_count": 2,
                "reconstruction_changed_file_count": 2,
                "same_changed_file_set": True,
                "evidence": "Clean reconstruction of #10",
            }
        ],
    }


def _requests():
    return {
        "schema": "omega-pr-llmt-measurement-requests/v0.1.0",
        "fingerprint": "r" * 64,
        "requests": [
            {
                "request_id": "request-source",
                "target_ref": "pr:example/repo#10",
                "measurement_kind": "reconstruction_equivalence_test",
            },
            {
                "request_id": "request-reconstruction",
                "target_ref": "pr:example/repo#11",
                "measurement_kind": "reconstruction_equivalence_test",
            },
            {
                "request_id": "request-other",
                "target_ref": "pr:example/repo#11",
                "measurement_kind": "negative_memory_context_check",
            },
        ],
    }


def _source(*, mismatch: bool = False, missing: bool = False) -> GitHubPRSource:
    blobs = {
        ("1" * 40, "pkg/a.py"): "a" * 40,
        ("1" * 40, "pkg/b.py"): "b" * 40,
        ("2" * 40, "pkg/a.py"): "a" * 40,
        ("2" * 40, "pkg/b.py"): ("c" * 40 if mismatch else "b" * 40),
    }

    def transport(url: str):
        parsed = urlparse(url)
        path_marker = "/contents/"
        assert path_marker in parsed.path
        path = unquote(parsed.path.split(path_marker, 1)[1])
        ref = parse_qs(parsed.query)["ref"][0]
        if missing and path == "pkg/b.py" and ref == "2" * 40:
            return {"type": "file", "size": 1}
        return {
            "type": "file",
            "sha": blobs[(ref, path)],
            "size": 10,
            "url": url,
        }

    return GitHubPRSource(api_base="https://api.example.test", transport=transport)


def test_reconstruction_blob_measurement_proves_exact_changed_blob_identity_only():
    result = compile_reconstruction_blob_measurements(_filegraph(), _requests(), _source())

    assert result["pair_count"] == 1
    assert result["compared_file_count"] == 2
    assert result["blob_match_count"] == 2
    assert result["blob_mismatch_count"] == 0
    assert result["error_count"] == 0
    assert result["full_changed_blob_equivalence_count"] == 1
    assert result["associated_request_count"] == 2
    row = result["measurements"][0]
    assert row["outcome"] == "MATCH_FULL_CHANGED_SET"
    assert row["all_shared_blob_sha_equal"] is True
    assert row["full_changed_blob_equivalence"] is True
    assert row["associated_request_ids"] == ["request-reconstruction", "request-source"]
    assert row["request_satisfaction"] == "PARTIAL_STRUCTURAL_EVIDENCE"
    assert row["request_fully_resolved"] is False
    assert row["supersession_authority_granted"] is False
    assert "BYTE_IDENTITY != BEHAVIORAL_EQUIVALENCE" in result["oak_boundaries"]
    assert len(result["fingerprint"]) == 64


def test_reconstruction_blob_measurement_records_negative_evidence_without_pipeline_failure():
    result = compile_reconstruction_blob_measurements(
        _filegraph(), _requests(), _source(mismatch=True)
    )

    row = result["measurements"][0]
    assert row["outcome"] == "MISMATCH"
    assert row["blob_match_count"] == 1
    assert row["blob_mismatch_count"] == 1
    assert row["full_changed_blob_equivalence"] is False
    assert result["blob_mismatch_count"] == 1
    assert result["error_count"] == 0


def test_reconstruction_blob_measurement_holds_when_github_evidence_is_incomplete():
    result = compile_reconstruction_blob_measurements(
        _filegraph(), _requests(), _source(missing=True)
    )

    row = result["measurements"][0]
    assert row["outcome"] == "HOLD_INCOMPLETE"
    assert row["error_count"] == 1
    assert row["compared_file_count"] == 1
    assert row["full_changed_blob_equivalence"] is False
    assert result["error_count"] == 1


def test_structural_measurement_never_grants_write_merge_or_supersession_authority():
    result = compile_reconstruction_blob_measurements(_filegraph(), _requests(), _source())

    assert result["authority"]["write_authority_granted"] is False
    assert result["authority"]["merge_authority_granted"] is False
    assert result["authority"]["supersession_authority_granted"] is False
    assert all(row["request_fully_resolved"] is False for row in result["measurements"])
