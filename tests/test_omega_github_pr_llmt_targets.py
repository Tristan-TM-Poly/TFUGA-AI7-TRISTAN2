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

    assert report["schema"] == "omega-pr-llmt-target-filegraph/v0.2.0"
    assert report["hydrated_target_count"] == 2
    assert report["error_count"] == 0
    assert report["total_changed_file_observations"] == 4
    assert report["unique_changed_file_count"] == 3
    assert report["shared_file_count"] == 1
    assert report["overlap_edge_count"] == 1
    assert report["targets_with_file_overlap_count"] == 2
    assert report["reconstruction_pair_count"] == 0
    assert report["shared_files"][0]["path"] == "omega/shared.py"
    assert report["shared_files"][0]["fanout"] == 2
    edge = report["overlap_edges"][0]
    assert edge["shared_file_count"] == 1
    assert edge["shared_files"] == ["omega/shared.py"]
    assert report["changed_file_distribution"]["p90"] == 2
    assert report["authority"]["write_authority_granted"] is False
    assert not any("/contents/" in call for call in calls)
    assert hydrated.assets
    assert all(asset.source_kind == "pr_changed_file" for asset in hydrated.assets.values())
    assert all(asset.source_kind != "pr_head_python_ast_symbol" for asset in hydrated.assets.values())


def test_target_file_graph_classifies_declared_reconstruction_without_claiming_blob_identity():
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory("o/r", 20, "open", "source"))
    index.add_pr(PRMemory("o/r", 21, "open", "reconstruction"))

    def transport(url: str):
        if url.endswith("/pulls/20"):
            return {
                "number": 20,
                "state": "open",
                "title": "source",
                "body": "original implementation",
                "head": {"sha": "src", "ref": "feat/source"},
                "base": {"ref": "main"},
            }
        if url.endswith("/pulls/21"):
            return {
                "number": 21,
                "state": "open",
                "title": "reconstruction",
                "body": "## OAK reconstruction of #20\nReplayed on current main.",
                "head": {"sha": "new", "ref": "feat/rebuild"},
                "base": {"ref": "main"},
            }
        if "/pulls/20/files" in url or "/pulls/21/files" in url:
            return [
                {"filename": "omega/kernel.py", "status": "added"},
                {"filename": "tests/test_kernel.py", "status": "added"},
            ]
        raise AssertionError(url)

    portfolio = {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "r" * 64,
        "packets": [
            {"target": {"ref": "pr:o/r#21"}},
            {"target": {"ref": "pr:o/r#20"}},
        ],
    }
    report, _ = compile_target_file_graph(
        index,
        portfolio,
        GitHubPRSource(api_base="https://example.invalid", transport=transport),
    )
    assert report["reconstruction_pair_count"] == 1
    pair = report["reconstruction_pairs"][0]
    assert pair["source_ref"] == "pr:o/r#20"
    assert pair["reconstruction_ref"] == "pr:o/r#21"
    assert pair["shared_file_count"] == 2
    assert pair["same_changed_file_set"] is True
    assert "reconstruction of #20" in pair["evidence"]
    assert "SAME_CHANGED_FILE_SET != SAME_BLOBS" in report["oak_boundaries"]


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
