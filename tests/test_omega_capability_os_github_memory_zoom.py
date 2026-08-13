from __future__ import annotations

import base64

from omega_capability_os_t.github_memory import CapabilityRequest, GitHubMemoryIndex, GitHubPRSource, PRMemory
from omega_capability_os_t.github_memory_zoom import ProgressiveGitHubRetriever, extract_python_symbols


def test_ast_symbol_extractor_is_static_and_qualified():
    source = """
class MemoryKernel:
    def search(self, query):
        return query

async def build_context():
    return None
"""
    symbols = extract_python_symbols(source, "memory.py")
    observed = {(item.qualified_name, item.kind) for item in symbols}
    assert ("MemoryKernel", "class") in observed
    assert ("MemoryKernel.search", "method") in observed
    assert ("build_context", "async_function") in observed


def test_progressive_hydration_fetches_only_ranked_pr_and_extracts_symbols():
    index = GitHubMemoryIndex()
    index.add_pr(
        PRMemory(
            repository="owner/repo",
            number=7,
            state="open",
            title="semantic memory analyzer",
            body="",
        )
    )
    index.add_pr(
        PRMemory(
            repository="owner/repo",
            number=8,
            state="open",
            title="unrelated thermal solver",
            body="",
        )
    )
    request = CapabilityRequest(
        request_id="REQ-ZOOM",
        description="semantic memory analyzer",
        domains=("github", "memory"),
        produces=("semantic_memory",),
    )

    calls = []
    py_source = "class SemanticMemory:\n    def search(self, query):\n        return query\n"

    def transport(url: str):
        calls.append(url)
        if url.endswith("/pulls/7"):
            return {
                "number": 7,
                "state": "open",
                "title": "semantic memory analyzer",
                "body": "",
                "head": {"sha": "abc", "ref": "feat/memory"},
                "base": {"ref": "main"},
            }
        if "/pulls/7/files" in url:
            return [{"filename": "omega/semantic_memory.py", "status": "added"}]
        if "/contents/omega/semantic_memory.py?ref=abc" in url:
            return {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(py_source.encode()).decode(),
            }
        raise AssertionError(f"unexpected hydration call: {url}")

    retriever = ProgressiveGitHubRetriever(GitHubPRSource(api_base="https://example.invalid", transport=transport))
    receipt = retriever.hydrate(index, request, top_prs=1, max_files_per_pr=4)

    assert receipt.candidate_prs == ("pr:owner/repo#7",)
    assert receipt.hydrated_prs == ("pr:owner/repo#7",)
    assert receipt.changed_file_count == 1
    assert receipt.symbol_count == 2
    assert not receipt.errors
    assert any(asset.source_kind == "pr_head_python_ast_symbol" for asset in index.assets.values())
    assert not any("/pulls/8" in call for call in calls)


def test_bad_candidate_python_is_recorded_not_promoted_or_executed():
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory("owner/repo", 9, "open", "memory broken syntax"))
    request = CapabilityRequest("REQ-BAD", "memory broken syntax", produces=("memory",))

    def transport(url: str):
        if url.endswith("/pulls/9"):
            return {
                "number": 9,
                "state": "open",
                "title": "memory broken syntax",
                "head": {"sha": "bad", "ref": "feat/bad"},
                "base": {"ref": "main"},
            }
        if "/pulls/9/files" in url:
            return [{"filename": "bad.py", "status": "added"}]
        if "/contents/bad.py?ref=bad" in url:
            return {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(b"def broken(:\n").decode(),
            }
        raise AssertionError(url)

    receipt = ProgressiveGitHubRetriever(
        GitHubPRSource(api_base="https://example.invalid", transport=transport)
    ).hydrate(index, request, top_prs=1)

    assert receipt.symbol_count == 0
    assert len(receipt.errors) == 1
    assert "SyntaxError" in receipt.errors[0]["error"]
    assert all(asset.source_kind != "pr_head_python_ast_symbol" for asset in index.assets.values())
