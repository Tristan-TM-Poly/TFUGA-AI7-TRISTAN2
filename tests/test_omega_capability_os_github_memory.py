from __future__ import annotations

from omega_capability_os_t.github_memory import (
    CapabilityGraph,
    CapabilityRequest,
    GitHubMemoryIndex,
    GitHubPRSource,
    GraphEdge,
    PRMemory,
    ReuseBeforeCreateGate,
    extract_explicit_relations,
)


def registry():
    return {
        "capabilities": [
            {
                "id": "github.pr-memory.scan",
                "domains": ["github", "memory"],
                "consumes": ["repository"],
                "produces": ["pr_index"],
                "quality": 0.95,
                "verifiability": 0.95,
                "reuse": 0.95,
                "cost": 0.15,
                "risk": 0.05,
            },
            {
                "id": "github.capability-graph.compile",
                "domains": ["github", "graph"],
                "consumes": ["pr_index"],
                "produces": ["capability_graph"],
                "quality": 0.90,
                "verifiability": 0.95,
                "reuse": 0.90,
                "cost": 0.20,
                "risk": 0.05,
            },
        ]
    }


def request(*outputs: str, description: str = "GitHub PR memory capability graph") -> CapabilityRequest:
    return CapabilityRequest(
        request_id="REQ-1",
        description=description,
        domains=("github",),
        consumes=("repository",),
        produces=tuple(outputs),
    )


def test_merged_pr_is_history_not_m_plus():
    pr = PRMemory(
        repository="owner/repo",
        number=7,
        state="closed",
        title="Useful merged implementation",
        merged=True,
    )
    assert pr.lifecycle == "MERGED"
    assert pr.epistemic_memory == "M?"


def test_explicit_lineage_only_is_promoted_to_typed_edges():
    pr = PRMemory(
        repository="owner/repo",
        number=20,
        state="open",
        title="compose old work",
        body="reuses: PR-12, #13\nsupersedes: #14\n",
    )
    edges = extract_explicit_relations(pr)
    triples = {(edge.source, edge.target, edge.relation) for edge in edges}
    assert (pr.ref, "pr:owner/repo#12", "uses") in triples
    assert (pr.ref, "pr:owner/repo#13", "uses") in triples
    assert (pr.ref, "pr:owner/repo#14", "supersedes") in triples


def test_graph_detects_supersession_cycles():
    graph = CapabilityGraph(
        [
            GraphEdge("a", "b", "supersedes", "explicit"),
            GraphEdge("b", "a", "supersedes", "explicit"),
        ]
    )
    try:
        graph.supersession_chain("a")
    except ValueError as exc:
        assert "cycle" in str(exc)
    else:
        raise AssertionError("cycle must fail closed")


def test_exact_formal_capability_is_reused_before_creation():
    index = GitHubMemoryIndex()
    index.ingest_capability_registry(registry(), "registry:owner/repo")
    decision = ReuseBeforeCreateGate(index).decide(request("pr_index"))
    assert decision.action == "REUSE"
    assert decision.selected_capabilities == ("github.pr-memory.scan",)
    assert decision.residual_outputs == ()
    assert decision.creation_allowed is False


def test_existing_capabilities_are_composed_before_creation():
    index = GitHubMemoryIndex()
    index.ingest_capability_registry(registry(), "registry:owner/repo")
    decision = ReuseBeforeCreateGate(index).decide(request("pr_index", "capability_graph"))
    assert decision.action == "COMPOSE"
    assert set(decision.selected_capabilities) == {
        "github.pr-memory.scan",
        "github.capability-graph.compile",
    }
    assert decision.coverage == 1.0
    assert decision.residual_outputs == ()


def test_partial_coverage_emits_only_residual_capability():
    index = GitHubMemoryIndex()
    index.ingest_capability_registry(registry(), "registry:owner/repo")
    decision = ReuseBeforeCreateGate(index).decide(request("pr_index", "semantic_symbol_map"))
    assert decision.action == "EXTEND"
    assert decision.selected_capabilities == ("github.pr-memory.scan",)
    assert decision.residual_outputs == ("semantic_symbol_map",)
    assert decision.creation_allowed is False


def test_historical_similarity_requires_inspection_not_reuse():
    index = GitHubMemoryIndex()
    index.add_pr(
        PRMemory(
            repository="owner/repo",
            number=31,
            state="closed",
            title="semantic overlap analyzer",
            files=("omega_arch/semantic_overlap_analyzer.py",),
        )
    )
    decision = ReuseBeforeCreateGate(index).decide(
        request("novel_output", description="semantic overlap analyzer")
    )
    assert decision.action == "INSPECT"
    assert decision.selected_capabilities == ()
    assert decision.creation_allowed is False
    assert decision.historical_candidates


def test_creation_is_allowed_only_when_no_reuse_or_inspection_candidate_exists():
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory("owner/repo", 1, "closed", "unrelated thermodynamics note"))
    decision = ReuseBeforeCreateGate(index).decide(
        request("quantum_frog_compiler", description="quantum frog compiler")
    )
    assert decision.action == "CREATE"
    assert decision.creation_allowed is True
    assert decision.residual_outputs == ("quantum_frog_compiler",)


def test_context_compiler_is_bounded_and_carries_gate_instructions():
    index = GitHubMemoryIndex()
    index.ingest_capability_registry(registry(), "registry:owner/repo")
    index.add_pr(PRMemory("owner/repo", 9, "open", "GitHub memory", files=("memory.py",)))
    packet = ReuseBeforeCreateGate(index).compile_context(request("pr_index"), max_items=2)
    assert packet["schema"] == "omega-github-llmt-context/v1"
    assert packet["decision"]["action"] == "REUSE"
    assert len(packet["decision"]["capability_candidates"]) <= 12
    assert "generate only residual capability" in " ".join(packet["instructions"])
    assert len(packet["fingerprint"]) == 64


def test_index_round_trip_preserves_prs_assets_capabilities_and_edges():
    index = GitHubMemoryIndex()
    index.ingest_capability_registry(registry(), "registry:owner/repo")
    index.add_pr(
        PRMemory(
            repository="owner/repo",
            number=20,
            state="open",
            title="memory compiler",
            body="extends: #19",
            files=("omega/memory.py",),
        )
    )
    encoded = index.to_dict()
    restored = GitHubMemoryIndex.from_dict(encoded)
    assert restored.to_dict()["fingerprint"] == encoded["fingerprint"]
    assert "pr:owner/repo#20" in restored.prs
    assert "github.pr-memory.scan" in restored.capabilities
    assert any(edge.relation == "extends" for edge in restored.graph.edges)


def test_master_atlas_candidates_remain_structural_not_semantic_truth():
    index = GitHubMemoryIndex()
    index.ingest_master_atlas(
        {
            "atlas_fingerprint": "a" * 64,
            "repository_count": 2,
            "truth_boundary": "structural only",
            "shared_component_candidates": [
                {
                    "normalized_name": "memory_kernel",
                    "members": [{"repository": "owner/a"}, {"repository": "owner/b"}],
                }
            ],
        }
    )
    asset = next(iter(index.assets.values()))
    assert asset.source_kind == "atlas_structural_candidate"
    assert asset.confidence < 0.5
    assert "semantic equivalence" in asset.boundary


def test_read_only_github_source_can_snapshot_all_prs_with_files_without_network():
    calls = []

    def transport(url: str):
        calls.append(url)
        if "/pulls/7/files" in url:
            return [{"filename": "omega/foo.py"}, {"filename": "tests/test_foo.py"}]
        if "/pulls?state=all" in url:
            return [
                {
                    "number": 7,
                    "state": "open",
                    "title": "foo capability",
                    "body": "",
                    "head": {"sha": "abc", "ref": "feat/foo"},
                    "base": {"ref": "main"},
                    "draft": False,
                }
            ]
        raise AssertionError(url)

    source = GitHubPRSource(api_base="https://example.invalid", transport=transport)
    snapshot = source.snapshot("owner/repo", include_files=True)
    assert snapshot[0]["number"] == 7
    assert snapshot[0]["files"] == ["omega/foo.py", "tests/test_foo.py"]
    index = GitHubMemoryIndex()
    index.ingest_pull_requests("owner/repo", snapshot)
    assert index.prs["pr:owner/repo#7"].head_sha == "abc"
    assert any("pulls?state=all" in call for call in calls)
    assert any("pulls/7/files" in call for call in calls)
