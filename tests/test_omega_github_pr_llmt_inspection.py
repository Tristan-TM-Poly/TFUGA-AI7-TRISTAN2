from __future__ import annotations

import base64

from omega_capability_os_t.github_memory import GitHubMemoryIndex, GitHubPRSource, PRMemory
from omega_capability_os_t.github_pr_llmt_inspection import (
    compile_inspection_plan,
    inspect_portfolio,
)


def _portfolio():
    return {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "f" * 64,
        "packets": [
            {
                "target": {"ref": "pr:o/r#10"},
                "historical_retrieval": {
                    "candidates": [
                        {"ref": "pr:o/r#1", "rank": 1},
                        {"ref": "pr:o/r#2", "rank": 2},
                    ]
                },
                "known_later_descendants": [],
            },
            {
                "target": {"ref": "pr:o/r#11"},
                "historical_retrieval": {
                    "candidates": [
                        {"ref": "pr:o/r#1", "rank": 2},
                        {"ref": "pr:o/r#3", "rank": 1},
                    ]
                },
                "known_later_descendants": [
                    {"source_ref": "pr:o/r#12"},
                ],
            },
        ],
    }


def test_inspection_plan_deduplicates_and_prioritizes_fanout():
    plan = compile_inspection_plan(_portfolio(), max_candidates=1)
    assert plan["planned_unique_ref_count"] == 4
    assert plan["selected_ref_count"] == 1
    assert plan["backlog_ref_count"] == 3
    assert plan["selected_refs"] == ["pr:o/r#1"]
    assert plan["candidates"][0]["fanout"] == 2
    assert plan["selected_packet_coverage_count"] == 2
    assert plan["selected_packet_coverage_fraction"] == 1.0
    assert plan["operational_budget"]["architecture_hard_cap"] is False
    assert plan["authority"]["write_authority_granted"] is False


def test_inspection_plan_without_budget_keeps_all_candidates():
    plan = compile_inspection_plan(_portfolio())
    assert plan["selected_ref_count"] == plan["planned_unique_ref_count"] == 4
    assert plan["backlog_ref_count"] == 0


def test_inspection_overlay_reuses_explicit_zoom_and_maps_back_to_targets():
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory("o/r", 1, "closed", "shared memory root"))
    index.add_pr(PRMemory("o/r", 2, "closed", "secondary root"))
    index.add_pr(PRMemory("o/r", 3, "closed", "third root"))
    index.add_pr(PRMemory("o/r", 12, "open", "later descendant"))
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

    plan, overlay = inspect_portfolio(
        index,
        _portfolio(),
        GitHubPRSource(api_base="https://example.invalid", transport=transport),
        max_candidates=1,
        max_files_per_pr=2,
    )
    assert plan["selected_refs"] == ["pr:o/r#1"]
    assert overlay["selected_ref_count"] == 1
    assert overlay["hydrated_ref_count"] == 1
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
    assert not any("/pulls/2" in call or "/pulls/3" in call for call in calls)


def test_inspection_plan_rejects_invalid_budget_and_schema():
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
