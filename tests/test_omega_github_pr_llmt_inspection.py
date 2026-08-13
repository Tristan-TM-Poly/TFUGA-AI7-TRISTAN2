from __future__ import annotations

import base64

from omega_capability_os_t.github_memory import GitHubMemoryIndex, GitHubPRSource, PRMemory
from omega_capability_os_t.github_pr_llmt_inspection import (
    compile_inspection_checkpoint,
    compile_inspection_plan,
    inspect_portfolio,
)


def _portfolio():
    return {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "f" * 64,
        "packets": [
            {
                "target": {"ref": "pr:o/r#10", "head_sha": "t10"},
                "historical_retrieval": {
                    "candidates": [
                        {"ref": "pr:o/r#1", "rank": 1, "head_sha": "abc"},
                        {"ref": "pr:o/r#2", "rank": 2, "head_sha": "def"},
                    ]
                },
                "known_later_descendants": [],
            },
            {
                "target": {"ref": "pr:o/r#11", "head_sha": "t11"},
                "historical_retrieval": {
                    "candidates": [
                        {"ref": "pr:o/r#1", "rank": 2, "head_sha": "abc"},
                        {"ref": "pr:o/r#3", "rank": 1, "head_sha": "ghi"},
                    ]
                },
                "known_later_descendants": [
                    {"source_ref": "pr:o/r#12"},
                ],
            },
            {
                "target": {"ref": "pr:o/r#12", "head_sha": "t12"},
                "historical_retrieval": {"candidates": []},
                "known_later_descendants": [],
            },
        ],
    }


def test_inspection_plan_deduplicates_and_prioritizes_fanout():
    plan = compile_inspection_plan(_portfolio(), max_candidates=1)
    assert plan["planned_unique_ref_count"] == 4
    assert plan["pending_ref_count"] == 4
    assert plan["completed_current_ref_count"] == 0
    assert plan["selected_ref_count"] == 1
    assert plan["backlog_ref_count"] == 3
    assert plan["selected_refs"] == ["pr:o/r#1"]
    assert plan["candidates"][0]["head_sha"] == "abc"
    assert plan["candidates"][0]["fanout"] == 2
    assert plan["selected_packet_coverage_count"] == 2
    assert plan["selected_packet_coverage_fraction"] == round(2 / 3, 6)
    assert plan["operational_budget"]["architecture_hard_cap"] is False
    assert plan["authority"]["write_authority_granted"] is False


def test_inspection_plan_without_budget_keeps_all_candidates():
    plan = compile_inspection_plan(_portfolio())
    assert plan["selected_ref_count"] == plan["planned_unique_ref_count"] == 4
    assert plan["backlog_ref_count"] == 0


def test_inspection_overlay_reuses_explicit_zoom_and_maps_back_to_targets():
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory("o/r", 1, "closed", "shared memory root", head_sha="abc"))
    index.add_pr(PRMemory("o/r", 2, "closed", "secondary root", head_sha="def"))
    index.add_pr(PRMemory("o/r", 3, "closed", "third root", head_sha="ghi"))
    index.add_pr(PRMemory("o/r", 12, "open", "later descendant", head_sha="t12"))
    calls: list[str] = []
    source_text = "class SharedKernel:\n    def reuse(self):\n        return True\n"

    def transport(url: str):
        calls.append(url)
        if url.endswith("/pulls/1"):
            return {
                "number": 1,
                "state": "closed",
                "merged": True,
                "title": "shared memory root",
                "body": "",
                "head": {"sha": "abc", "ref": "feat/root"},
                "base": {"ref": "main"},
            }
        if "/pulls/1/files" in url:
            return [{"filename": "omega/shared.py", "status": "added"}]
        if "/contents/omega/shared.py?ref=abc" in url:
            return {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(source_text.encode()).decode(),
            }
        raise AssertionError(f"only the highest-fanout selected ref should be hydrated: {url}")

    plan, overlay, checkpoint = inspect_portfolio(
        index,
        _portfolio(),
        GitHubPRSource(api_base="https://example.invalid", transport=transport),
        max_candidates=1,
        max_files_per_pr=2,
    )
    assert plan["selected_refs"] == ["pr:o/r#1"]
    assert overlay["selected_ref_count"] == 1
    assert overlay["hydrated_ref_count"] == 1
    assert overlay["cumulative_hydrated_ref_count"] == 1
    assert overlay["changed_file_count"] == 1
    assert overlay["symbol_count"] == 2
    assert overlay["error_count"] == 0
    assert overlay["packet_coverage_after_successful_hydration"] == 2
    item = overlay["overlays"][0]
    assert item["ref"] == "pr:o/r#1"
    assert item["fanout"] == 2
    assert item["head_sha"] == "abc"
    assert item["changed_files"] == ["omega/shared.py"]
    assert len(item["symbol_assets"]) == 2
    assert item["inspection_state"] == "HYDRATED_STATIC_AST"
    assert checkpoint["completed_heads"] == {"pr:o/r#1": "abc"}
    assert not any("/pulls/2" in call or "/pulls/3" in call for call in calls)


def test_checkpoint_skips_unchanged_head_and_moved_head_becomes_pending_again():
    prior_overlay = {
        "schema": "omega-pr-llmt-inspection-overlay/v0.1.0",
        "portfolio_fingerprint": "f" * 64,
        "overlays": [
            {
                "ref": "pr:o/r#1",
                "head_sha": "abc",
                "inspection_state": "HYDRATED_STATIC_AST",
                "affected_targets": ["pr:o/r#10", "pr:o/r#11"],
            }
        ],
    }
    checkpoint = compile_inspection_checkpoint(prior_overlay)
    plan = compile_inspection_plan(_portfolio(), max_candidates=1, checkpoint=checkpoint)
    assert plan["completed_current_ref_count"] == 1
    assert plan["completed_current_refs"] == ["pr:o/r#1"]
    assert plan["pending_ref_count"] == 3
    assert plan["selected_refs"] == ["pr:o/r#3"]
    assert plan["stale_checkpoint_ref_count"] == 0

    moved = _portfolio()
    for packet in moved["packets"]:
        for candidate in packet["historical_retrieval"]["candidates"]:
            if candidate["ref"] == "pr:o/r#1":
                candidate["head_sha"] = "moved"
    stale_plan = compile_inspection_plan(moved, max_candidates=1, checkpoint=checkpoint)
    assert stale_plan["completed_current_ref_count"] == 0
    assert stale_plan["stale_checkpoint_refs"] == ["pr:o/r#1"]
    assert stale_plan["selected_refs"] == ["pr:o/r#1"]


def test_prior_overlay_is_merged_with_new_wave_evidence():
    prior_overlay = {
        "schema": "omega-pr-llmt-inspection-overlay/v0.1.0",
        "portfolio_fingerprint": "f" * 64,
        "overlays": [
            {
                "ref": "pr:o/r#1",
                "head_sha": "abc",
                "inspection_state": "HYDRATED_STATIC_AST",
                "affected_targets": ["pr:o/r#10", "pr:o/r#11"],
                "fanout": 2,
                "evidence_axes": ["historical_retrieval"],
                "best_historical_rank": 1,
                "lifecycle": "MERGED",
                "title": "root",
                "changed_files": ["root.py"],
                "symbol_assets": ["symbol:root"],
                "errors": [],
            }
        ],
    }
    checkpoint = compile_inspection_checkpoint(prior_overlay)
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory("o/r", 1, "closed", "root", head_sha="abc"))
    index.add_pr(PRMemory("o/r", 2, "closed", "second", head_sha="def"))
    index.add_pr(PRMemory("o/r", 3, "closed", "third", head_sha="ghi"))
    index.add_pr(PRMemory("o/r", 12, "open", "desc", head_sha="t12"))
    source_text = "def third():\n    return 3\n"

    def transport(url: str):
        if url.endswith("/pulls/3"):
            return {
                "number": 3,
                "state": "closed",
                "merged": True,
                "title": "third",
                "body": "",
                "head": {"sha": "ghi", "ref": "feat/third"},
                "base": {"ref": "main"},
            }
        if "/pulls/3/files" in url:
            return [{"filename": "third.py", "status": "added"}]
        if "/contents/third.py?ref=ghi" in url:
            return {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(source_text.encode()).decode(),
            }
        raise AssertionError(url)

    plan, overlay, next_checkpoint = inspect_portfolio(
        index,
        _portfolio(),
        GitHubPRSource(api_base="https://example.invalid", transport=transport),
        max_candidates=1,
        checkpoint=checkpoint,
        prior_overlay=prior_overlay,
    )
    assert plan["selected_refs"] == ["pr:o/r#3"]
    assert {row["ref"] for row in overlay["overlays"]} == {"pr:o/r#1", "pr:o/r#3"}
    assert overlay["cumulative_hydrated_ref_count"] == 2
    assert overlay["packet_coverage_after_successful_hydration"] == 2
    assert next_checkpoint["completed_heads"] == {
        "pr:o/r#1": "abc",
        "pr:o/r#3": "ghi",
    }


def test_inspection_plan_rejects_invalid_budget_schema_and_checkpoint():
    try:
        compile_inspection_plan(_portfolio(), max_candidates=-1)
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("negative budget must fail closed")

    bad = dict(_portfolio())
    bad["schema"] = "wrong"
    try:
        compile_inspection_plan(bad)
    except ValueError as exc:
        assert "unsupported portfolio schema" in str(exc)
    else:
        raise AssertionError("unknown portfolio schema must fail closed")

    try:
        compile_inspection_plan(_portfolio(), checkpoint={"schema": "wrong"})
    except ValueError as exc:
        assert "unsupported checkpoint schema" in str(exc)
    else:
        raise AssertionError("unknown checkpoint schema must fail closed")
