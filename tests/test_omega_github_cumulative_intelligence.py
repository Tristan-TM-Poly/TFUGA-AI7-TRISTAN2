from omega_capability_os_t.github_cumulative_intelligence import (
    CumulativeIntelligenceCompiler,
    HistoryArchaeologist,
    MinimalReuseCoalitionCompiler,
    PRGenomeCompiler,
)
from omega_capability_os_t.github_memory import CapabilityRequest, GitHubMemoryIndex, PRMemory


def _indexes():
    repo_a = "Tristan/example-a"
    repo_b = "Tristan/example-b"

    a = GitHubMemoryIndex()
    a.add_pr(
        PRMemory(
            repository=repo_a,
            number=1,
            state="closed",
            merged=True,
            title="Ω-HGFM memory compiler",
            body="M-: duplicated context caused regression\nsource pr: #0",
            head_sha="a" * 40,
            files=("omega/memory.py", "tests/test_memory.py"),
        )
    )
    a.add_pr(
        PRMemory(
            repository=repo_a,
            number=2,
            state="closed",
            merged=False,
            title="Closed reconstruction experiment",
            body="reconstructs: #1\nAlternative retained for future reuse.",
            head_sha="b" * 40,
            files=("omega/reconstruction.py",),
        )
    )
    a.ingest_capability_registry(
        {
            "capabilities": [
                {
                    "id": "github.memory.index",
                    "domains": ["github", "memory"],
                    "consumes": ["repository"],
                    "produces": ["pr_index"],
                    "authority": "read",
                    "quality": 0.95,
                    "information_gain": 0.95,
                    "verifiability": 0.95,
                    "reuse": 0.99,
                    "cost": 0.10,
                    "latency": 0.10,
                    "risk": 0.03,
                    "alternatives": [],
                    "failure_modes": [],
                }
            ]
        },
        source_ref=f"pr:{repo_a}#1",
    )

    b = GitHubMemoryIndex()
    b.add_pr(
        PRMemory(
            repository=repo_b,
            number=5,
            state="open",
            draft=True,
            title="LLMT context compiler",
            body="stacked on: Tristan/example-a#1",
            head_sha="c" * 40,
            files=("omega/context.py",),
        )
    )
    b.add_pr(
        PRMemory(
            repository=repo_b,
            number=6,
            state="open",
            draft=False,
            title="Application reuse court",
            body="extends: #5",
            head_sha="d" * 40,
            files=("omega/reuse.py",),
        )
    )
    b.ingest_capability_registry(
        {
            "capabilities": [
                {
                    "id": "github.llmt.context",
                    "domains": ["github", "memory", "llmt"],
                    "consumes": ["pr_index"],
                    "produces": ["llmt_context"],
                    "authority": "read",
                    "quality": 0.94,
                    "information_gain": 0.94,
                    "verifiability": 0.96,
                    "reuse": 0.99,
                    "cost": 0.08,
                    "latency": 0.08,
                    "risk": 0.03,
                    "alternatives": [],
                    "failure_modes": [],
                }
            ]
        },
        source_ref=f"pr:{repo_b}#5",
    )

    return {repo_a: a, repo_b: b}


def _request():
    return CapabilityRequest(
        request_id="new-pr",
        description="reuse historical GitHub PR memory for LLMT context",
        domains=("github", "memory", "llmt"),
        consumes=("repository",),
        produces=("pr_index", "llmt_context"),
    )


def test_history_covers_open_draft_merged_and_closed_not_merged():
    receipt = HistoryArchaeologist.coverage(_indexes())
    assert receipt.repository_count == 2
    assert receipt.pr_count == 4
    assert receipt.open_count == 1
    assert receipt.draft_count == 1
    assert receipt.merged_count == 1
    assert receipt.closed_not_merged_count == 1
    assert receipt.exact_state_partition is True


def test_closed_prs_remain_in_genome_and_merged_is_not_m_plus():
    indexes = _indexes()
    genomes = PRGenomeCompiler().compile_all(indexes)
    merged = genomes["pr:Tristan/example-a#1"]
    closed = genomes["pr:Tristan/example-a#2"]
    assert merged.lifecycle == "MERGED"
    assert merged.epistemic_memory == "M?"
    assert closed.lifecycle == "CLOSED"
    assert "omega/reconstruction.py" in closed.changed_files
    assert any("regression" in line for line in merged.failure_memory)


def test_archaeology_preserves_cross_repo_and_reconstruction_lineage():
    signals = HistoryArchaeologist.lineage(_indexes())
    triples = {(row.source_ref, row.target_ref, row.relation) for row in signals}
    assert (
        "pr:Tristan/example-a#2",
        "pr:Tristan/example-a#1",
        "reconstructs",
    ) in triples
    assert (
        "pr:Tristan/example-b#5",
        "pr:Tristan/example-a#1",
        "stacked_on",
    ) in triples


def test_minimal_reuse_coalition_covers_explicit_contract_outputs():
    coalition = MinimalReuseCoalitionCompiler().compile(_indexes(), _request())
    assert coalition.reuse_coverage_ratio == 1.0
    assert coalition.residual_outputs == ()
    assert len(coalition.selected_capabilities) == 2
    assert "pr:Tristan/example-a#1" in coalition.source_refs
    assert "pr:Tristan/example-b#5" in coalition.source_refs


def test_cumulative_intelligence_compiles_one_memory_many_llmt_views():
    compiler = CumulativeIntelligenceCompiler()
    first = compiler.compile(_indexes(), _request(), max_items=4)
    second = compiler.compile(_indexes(), _request(), max_items=4)

    assert first["fingerprint"] == second["fingerprint"]
    assert first["history_coverage"]["pr_count"] == 4
    assert first["minimal_reuse_coalition"]["reuse_coverage_ratio"] == 1.0
    assert first["generation_constitution"]["search_all_history_before_create"] is True
    assert first["generation_constitution"]["create_only_residual"] is True
    assert first["generation_constitution"]["write_authority_granted"] is False
    assert first["memory_lenses"]["packet_count"] == 6
    assert any(hit["ref"] == "pr:Tristan/example-a#1" for hit in first["negative_memory_hits"])
    assert "MERGED != M+" in first["oak_boundaries"]


def test_research_abi_bridge_preserves_read_authority():
    from omega_research_abi_t.github_cumulative_intelligence_bridge import adapt_cumulative_intelligence

    report = CumulativeIntelligenceCompiler().compile(_indexes(), _request(), max_items=3)
    envelope = adapt_cumulative_intelligence(report)
    assert envelope.graph == "knowledge"
    assert envelope.authority == "read"
    assert envelope.oak_state == "UNKNOWN"
    assert envelope.object_type == "github_cumulative_intelligence_context"
