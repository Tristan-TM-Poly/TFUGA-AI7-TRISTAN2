from __future__ import annotations

from omega_capability_os_t.github_pr_llmt_findings import compile_pr_findings


def _portfolio():
    return {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "p" * 64,
        "packets": [
            {
                "target": {
                    "ref": "pr:o/r#10",
                    "number": 10,
                    "title": "first target",
                    "head_sha": "a" * 40,
                    "failure_memory": ["M-: target regression"],
                },
                "historical_retrieval": {
                    "candidates": [
                        {
                            "ref": "pr:o/r#1",
                            "rank": 1,
                            "failure_memory": ["avoid duplicate implementation"],
                        }
                    ]
                },
                "declared_prior_lineage": [
                    {"relation": "extends", "target_ref": "pr:o/r#1"}
                ],
                "known_later_descendants": [],
            },
            {
                "target": {
                    "ref": "pr:o/r#11",
                    "number": 11,
                    "title": "second target",
                    "head_sha": "b" * 40,
                    "failure_memory": [],
                },
                "historical_retrieval": {"candidates": [{"ref": "pr:o/r#2", "rank": 1, "failure_memory": []}]},
                "declared_prior_lineage": [],
                "known_later_descendants": [
                    {"source_ref": "pr:o/r#12", "relation": "extends"}
                ],
            },
        ],
    }


def _filegraph():
    return {
        "schema": "omega-pr-llmt-target-filegraph/v0.2.0",
        "portfolio_fingerprint": "p" * 64,
        "fingerprint": "f" * 64,
        "changed_file_distribution": {
            "large_change_candidates": ["pr:o/r#10"],
        },
        "targets": [
            {"ref": "pr:o/r#10", "changed_file_count": 80},
            {"ref": "pr:o/r#11", "changed_file_count": 4},
        ],
        "overlap_edges": [
            {
                "left": "pr:o/r#10",
                "right": "pr:o/r#11",
                "shared_file_count": 5,
                "shared_files": ["a.py", "b.py", "c.py", "d.py", "e.py"],
            }
        ],
        "reconstruction_pair_count": 0,
        "reconstruction_pairs": [],
    }


def _overlay():
    return {
        "schema": "omega-pr-llmt-inspection-overlay/v0.1.0",
        "portfolio_fingerprint": "p" * 64,
        "fingerprint": "i" * 64,
        "overlays": [
            {
                "ref": "pr:o/r#1",
                "affected_targets": ["pr:o/r#10"],
                "inspection_state": "HYDRATED_STATIC_AST",
                "head_sha": "c" * 40,
                "changed_files": ["old.py"],
                "symbol_assets": ["sym:a", "sym:b"],
                "fanout": 1,
                "best_historical_rank": 1,
                "errors": [],
            }
        ],
    }


def test_findings_combine_overlap_inspection_lineage_and_negative_memory():
    report = compile_pr_findings(_portfolio(), _filegraph(), _overlay())
    assert report["schema"] == "omega-pr-llmt-findings/v0.2.0"
    assert report["packet_count"] == 2
    by_ref = {row["target_ref"]: row for row in report["packets"]}
    first = by_ref["pr:o/r#10"]
    kinds = {row["finding_type"] for row in first["findings"]}
    assert "FILE_OVERLAP_REVIEW" in kinds
    assert "LARGE_CHANGE_SURFACE" in kinds
    assert "INSPECTED_REUSE_CANDIDATE" in kinds
    assert "DECLARED_PRIOR_LINEAGE" in kinds
    assert "NEGATIVE_MEMORY_AVAILABLE" in kinds
    assert "DEEP_EVIDENCE_GAP" not in kinds
    assert first["max_shared_file_count"] == 5
    assert first["inspected_reuse_candidate_count"] == 1
    assert first["negative_memory_count"] == 2


def test_findings_preserve_uncertainty_when_deep_evidence_missing():
    report = compile_pr_findings(_portfolio(), _filegraph(), _overlay())
    by_ref = {row["target_ref"]: row for row in report["packets"]}
    second = by_ref["pr:o/r#11"]
    kinds = {row["finding_type"] for row in second["findings"]}
    assert "DEEP_EVIDENCE_GAP" in kinds
    assert "KNOWN_LATER_DESCENDANT" in kinds
    assert second["inspected_reuse_candidate_count"] == 0
    assert report["packets_without_deep_reuse_evidence"] == 1
    assert report["packets_with_file_overlap"] == 2


def test_reconstruction_pair_replaces_generic_overlap_with_supersession_review():
    portfolio = {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "z" * 64,
        "packets": [
            {
                "target": {"ref": "pr:o/r#20", "number": 20, "title": "source", "head_sha": "s" * 40, "failure_memory": []},
                "historical_retrieval": {"candidates": []},
                "declared_prior_lineage": [],
                "known_later_descendants": [],
            },
            {
                "target": {"ref": "pr:o/r#21", "number": 21, "title": "rebuild", "head_sha": "r" * 40, "failure_memory": []},
                "historical_retrieval": {"candidates": []},
                "declared_prior_lineage": [],
                "known_later_descendants": [],
            },
        ],
    }
    filegraph = {
        "schema": "omega-pr-llmt-target-filegraph/v0.2.0",
        "portfolio_fingerprint": "z" * 64,
        "fingerprint": "g" * 64,
        "changed_file_distribution": {"large_change_candidates": []},
        "targets": [
            {"ref": "pr:o/r#20", "changed_file_count": 2},
            {"ref": "pr:o/r#21", "changed_file_count": 2},
        ],
        "overlap_edges": [
            {"left": "pr:o/r#20", "right": "pr:o/r#21", "shared_file_count": 2, "shared_files": ["a.py", "b.py"]}
        ],
        "reconstruction_pair_count": 1,
        "reconstruction_pairs": [
            {
                "source_ref": "pr:o/r#20",
                "reconstruction_ref": "pr:o/r#21",
                "evidence": "OAK reconstruction of #20",
                "shared_file_count": 2,
                "shared_files": ["a.py", "b.py"],
                "same_changed_file_set": True,
            }
        ],
    }
    overlay = {
        "schema": "omega-pr-llmt-inspection-overlay/v0.1.0",
        "portfolio_fingerprint": "z" * 64,
        "fingerprint": "o" * 64,
        "overlays": [],
    }
    report = compile_pr_findings(portfolio, filegraph, overlay)
    by_ref = {row["target_ref"]: row for row in report["packets"]}
    source_kinds = {row["finding_type"] for row in by_ref["pr:o/r#20"]["findings"]}
    rebuild_kinds = {row["finding_type"] for row in by_ref["pr:o/r#21"]["findings"]}
    assert "DECLARED_RECONSTRUCTION_SOURCE" in source_kinds
    assert "DECLARED_RECONSTRUCTION_PAIR" in rebuild_kinds
    assert "FILE_OVERLAP_REVIEW" not in source_kinds
    assert "FILE_OVERLAP_REVIEW" not in rebuild_kinds
    assert report["reconstruction_pair_count"] == 1
    assert "RECONSTRUCTION_PAIR != AUTOMATIC_SUPERSESSION" in report["oak_boundaries"]


def test_priority_score_is_triage_only_and_output_is_deterministic():
    left = compile_pr_findings(_portfolio(), _filegraph(), _overlay())
    right = compile_pr_findings(_portfolio(), _filegraph(), _overlay())
    assert left == right
    assert len(left["fingerprint"]) == 64
    assert "PRIORITY_SCORE != QUALITY_SCORE" in left["oak_boundaries"]
    assert left["authority"]["write_authority_granted"] is False
    assert left["authority"]["merge_authority_granted"] is False
    assert left["packets"][0]["priority_score"] >= left["packets"][1]["priority_score"]


def test_findings_fail_closed_on_schema_or_fingerprint_mismatch():
    bad = dict(_filegraph())
    bad["schema"] = "wrong"
    try:
        compile_pr_findings(_portfolio(), bad, _overlay())
    except ValueError as exc:
        assert "unsupported filegraph schema" in str(exc)
    else:
        raise AssertionError("wrong filegraph schema must fail closed")

    bad_overlay = dict(_overlay())
    bad_overlay["portfolio_fingerprint"] = "x" * 64
    try:
        compile_pr_findings(_portfolio(), _filegraph(), bad_overlay)
    except ValueError as exc:
        assert "fingerprint mismatch" in str(exc)
    else:
        raise AssertionError("mismatched evidence must fail closed")
