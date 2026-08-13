from __future__ import annotations

from omega_capability_os_t.github_memory import GitHubMemoryIndex, GitHubPRSource, PRMemory
from omega_capability_os_t.github_pr_llmt_targets import compile_target_file_graph


def _portfolio():
    return {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "a" * 64,
        "packets": [
            {"target": {"ref": "pr:o/r#11"}},
            {"target": {"ref": "pr:o/r#10"}},
        ],
    }


def test_target_file_graph_hydrates_all_targets_without_source_content_fetch():
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory("o/r", 10, "open", "first target"))
    index.add_pr(PRMemory("o/r", 11, "open", "second target"))
    calls: list[str] = []

    def transport(url: str):
        calls.append(url)
        if url.endswith("/pulls/10"):
            return {
                "number": 10,
                "state": "open",
                "title": "first target",
                "head": {"sha": "a10", "ref": "feat/10"},
                "base": {"ref": "main"},
            }
        if url.endswith("/pulls/11"):
            return {
                "number": 11,
                "state": "open",
                "title": "second target",
                "head": {"sha": "a11", "ref": "feat/11"},
                "base": {"ref": "main"},
            }
        if "/pulls/10/files" in url:
            return [
                {"filename": "omega/shared.py", "status": "modified"},
                {"filename": "docs/ten.md", "status": "added"},
            ]
        if "/pulls/11/files" in url:
            return [
                {"filename": "omega/shared.py", "status": "modified"},
                {"filename": "omega/eleven.py", "status": "added"},
            ]
        raise AssertionError(f"target filegraph must not fetch file contents: {url}")

    report, hydrated = compile_target_file_graph(
        index,
        _portfolio(),
        GitHubPRSource(api_base="https://example.invalid", transport=transport),
    )

    assert report["hydrated_target_count"] == 2
    assert report["error_count"] == 0
    assert report["total_changed_file_observations"] == 4
    assert report["unique_changed_file_count"] == 3
    assert report["shared_file_count"] == 1
    assert report["overlap_edge_count"] == 1
    assert report["targets_with_file_overlap_count"] == 2
    assert report["shared_files"][0]["path"] == "omega/shared.py"
    assert report["shared_files"][0]["fanout"] == 2
    edge = report["overlap_edges"][0]
    assert edge["shared_file_count"] == 1
    assert edge["shared_files"] == ["omega/shared.py"]
    assert report["changed_file_distribution"]["p90"] == 2
    assert report["authority"]["write_authority_granted"] is False
    assert not any("/contents/" in call for call in calls)
    assert not hydrated.assets


def test_target_file_graph_budget_is_operational_not_architectural():
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory("o/r", 10, "open", "first target"))
    index.add_pr(PRMemory("o/r", 11, "open", "second target"))

    def transport(url: str):
        if url.endswith("/pulls/11"):
            return {
                "number": 11,
                "state": "open",
                "title": "second target",
                "head": {"sha": "a11", "ref": "feat/11"},
                "base": {"ref": "main"},
            }
        if "/pulls/11/files" in url:
            return []
        raise AssertionError(url)

    report, _ = compile_target_file_graph(
        index,
        _portfolio(),
        GitHubPRSource(api_base="https://example.invalid", transport=transport),
        max_targets=1,
    )
    assert report["operational_budget"]["max_targets"] == 1
    assert report["operational_budget"]["architecture_hard_cap"] is False
    assert report["operational_budget"]["selected_target_count"] == 1
    assert report["operational_budget"]["total_target_count"] == 2


def test_target_file_graph_fails_closed_on_invalid_input():
    index = GitHubMemoryIndex()
    source = GitHubPRSource(api_base="https://example.invalid", transport=lambda url: None)
    try:
        compile_target_file_graph(index, _portfolio(), source, max_targets=-1)
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("negative max_targets must fail closed")

    bad = dict(_portfolio())
    bad["schema"] = "wrong"
    try:
        compile_target_file_graph(index, bad, source)
    except ValueError as exc:
        assert "unsupported portfolio schema" in str(exc)
    else:
        raise AssertionError("unknown portfolio schema must fail closed")
