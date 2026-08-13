from __future__ import annotations

import pytest

from omega_capability_os_t.core import Capability
from omega_capability_os_t.github_memory import (
    CapabilityObservation,
    CapabilityRequest,
    GitHubMemoryIndex,
    PRMemory,
    _tokens,
)
from omega_capability_os_t.github_memory_evolution import (
    CrossRepositoryCapabilityGraph,
    LLMTFederationCompiler,
    LLMTIdentity,
    ResidualCodeCompiler,
    ReuseOutcomeLearner,
    ReuseOutcomeReceipt,
    TemporalSupersessionMiner,
    compile_evolution_court,
)


def _cap(
    capability_id: str,
    produces: tuple[str, ...],
    *,
    source: str = "registry:test",
    consumes: tuple[str, ...] = ("repository",),
    domains: tuple[str, ...] = ("github", "memory"),
) -> CapabilityObservation:
    cap = Capability(
        capability_id=capability_id,
        domains=domains,
        consumes=consumes,
        produces=produces,
        authority="read",
        quality=0.95,
        information_gain=0.90,
        verifiability=0.95,
        reuse=0.95,
        cost=0.10,
        latency=0.10,
        risk=0.05,
    )
    return CapabilityObservation(
        capability=cap,
        source_ref=source,
        keywords=_tokens((capability_id, *domains, *consumes, *produces)),
    )


def _request(*outputs: str) -> CapabilityRequest:
    return CapabilityRequest(
        request_id="REQ-1",
        description="GitHub cumulative memory capability graph residual compiler",
        domains=("github", "memory"),
        consumes=("repository",),
        produces=tuple(outputs),
    )


def test_temporal_supersession_is_review_only_and_adds_no_strong_edge() -> None:
    index = GitHubMemoryIndex()
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=10,
            state="closed",
            title="GitHub memory compiler",
            body="first memory compiler",
            files=("omega/memory.py", "tests/test_memory.py"),
            updated_at="2026-08-01T00:00:00Z",
        )
    )
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=20,
            state="open",
            title="GitHub memory compiler R2",
            body="second memory compiler",
            files=("omega/memory.py", "tests/test_memory.py", "omega/graph.py"),
            updated_at="2026-08-02T00:00:00Z",
        )
    )

    report = TemporalSupersessionMiner(threshold=0.20).mine(index)

    assert report["candidate_count"] == 1
    row = report["candidates"][0]
    assert row["older_ref"] == "pr:o/r#10"
    assert row["newer_ref"] == "pr:o/r#20"
    assert row["review_required"] is True
    assert report["strong_edges_added"] == 0
    assert not [edge for edge in index.graph.edges if edge.relation in {"supersedes", "replaces"}]


def test_explicit_supersedes_remains_strong_but_miner_does_not_invent_it() -> None:
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory(repository="o/r", number=1, state="closed", title="old"))
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=2,
            state="open",
            title="new",
            body="supersedes: #1",
        )
    )
    strong = [edge for edge in index.graph.edges if edge.relation == "supersedes"]
    assert len(strong) == 1
    assert strong[0].source == "pr:o/r#2"
    assert strong[0].target == "pr:o/r#1"


def test_residual_compiler_blocks_generation_when_reuse_is_complete() -> None:
    index = GitHubMemoryIndex()
    index.capabilities["github.memory.full"] = _cap(
        "github.memory.full", ("pr_index", "capability_graph")
    )
    spec = ResidualCodeCompiler(index).compile(_request("pr_index", "capability_graph"))
    assert spec.decision == "REUSE"
    assert spec.residual_outputs == ()
    assert spec.generation_scope == "integration_only"
    assert spec.generation_allowed is False


def test_residual_compiler_emits_only_missing_outputs_for_extend() -> None:
    index = GitHubMemoryIndex()
    index.capabilities["github.memory.partial"] = _cap("github.memory.partial", ("pr_index",))
    spec = ResidualCodeCompiler(index).compile(_request("pr_index", "capability_graph"))
    assert spec.decision == "EXTEND"
    assert spec.residual_outputs == ("capability_graph",)
    assert spec.generation_scope == "residual_outputs_only"
    assert spec.generation_allowed is True


def test_inspect_blocks_generation_until_exact_candidate_inspection() -> None:
    index = GitHubMemoryIndex()
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=99,
            state="open",
            title="GitHub cumulative memory graph",
            body="candidate historical implementation",
        )
    )
    spec = ResidualCodeCompiler(index).compile(_request("brand_new_output"))
    assert spec.decision == "INSPECT"
    assert spec.generation_allowed is False
    assert "pr:o/r#99" in spec.exact_inspection_refs


def test_reuse_outcome_requires_evidence_and_never_reads_merge_state() -> None:
    with pytest.raises(ValueError, match="evidence"):
        ReuseOutcomeReceipt(
            receipt_id="R0",
            request_id="REQ",
            action="REUSE",
            selected_capabilities=("cap.a",),
            outcome="SUCCESS",
        )

    receipt = ReuseOutcomeReceipt(
        receipt_id="R1",
        request_id="REQ",
        action="REUSE",
        selected_capabilities=("cap.a",),
        outcome="SUCCESS",
        defect_delta=-0.5,
        evidence_refs=("ci:123", "benchmark:abc"),
    )
    assert receipt.memory_class == "M+"
    assert receipt.utility > 1.0


def test_reuse_outcome_learning_preserves_m_plus_m_minus_and_uncertain() -> None:
    learner = ReuseOutcomeLearner()
    report = learner.learn(
        [
            ReuseOutcomeReceipt("1", "REQ", "REUSE", ("cap.a",), "SUCCESS", evidence_refs=("ci:1",)),
            ReuseOutcomeReceipt("2", "REQ", "REUSE", ("cap.a",), "FAILURE", evidence_refs=("ci:2",)),
            ReuseOutcomeReceipt("3", "REQ", "EXTEND", ("cap.b",), "DEGRADED", evidence_refs=("ci:3",)),
        ]
    )
    assert report["memory_counts"] == {"M+": 1, "M-": 1, "M?": 1}
    assert report["actions"]["REUSE"]["n"] == 2
    assert set(report["capabilities"]["cap.a"]["evidence_refs"]) == {"ci:1", "ci:2"}


def test_cross_repository_matching_contract_is_candidate_not_equivalence() -> None:
    left = GitHubMemoryIndex()
    right = GitHubMemoryIndex()
    left.capabilities["cap.shared"] = _cap("cap.shared", ("x",), source="left-registry")
    right.capabilities["cap.shared"] = _cap("cap.shared", ("x",), source="right-registry")

    report = CrossRepositoryCapabilityGraph().merge({"o/left": left, "o/right": right})
    assert report["repository_count"] == 2
    assert len(report["shared_contracts"]) == 1
    assert report["conflicts"] == []
    assert "!= shared implementation" in report["shared_contracts"][0]["boundary"]


def test_cross_repository_contract_conflict_is_not_silently_overwritten() -> None:
    left = GitHubMemoryIndex()
    right = GitHubMemoryIndex()
    left.capabilities["cap.shared"] = _cap("cap.shared", ("x",), source="left-registry")
    right.capabilities["cap.shared"] = _cap("cap.shared", ("y",), source="right-registry")

    report = CrossRepositoryCapabilityGraph().merge({"o/left": left, "o/right": right})
    assert report["shared_contracts"] == []
    assert len(report["conflicts"]) == 1
    assert report["conflicts"][0]["left_signature"] != report["conflicts"][0]["right_signature"]


def test_llmt_federation_is_bounded_and_cannot_widen_to_write() -> None:
    index = GitHubMemoryIndex()
    index.capabilities["github.memory.full"] = _cap(
        "github.memory.full", ("pr_index", "capability_graph")
    )
    index.add_pr(PRMemory(repository="o/r", number=447, state="open", title="GitHub cumulative memory"))
    compiler = LLMTFederationCompiler(index)
    report = compiler.compile(
        _request("pr_index", "capability_graph"),
        [
            LLMTIdentity("global", "global", "*", "draft"),
            LLMTIdentity("pr447", "pr", "PR 447 github memory", "draft", "global"),
            LLMTIdentity("module-memory", "module", "github memory", "read", "pr447"),
        ],
        max_items=3,
    )
    assert report["packet_count"] == 3
    assert len({packet["fingerprint"] for packet in report["packets"]}) == 3
    assert {packet["authority_ceiling"] for packet in report["packets"]} <= {"read", "draft"}
    assert all(packet["parent_context_fingerprint"] == report["global_context_fingerprint"] for packet in report["packets"])

    with pytest.raises(ValueError, match="read or draft"):
        LLMTIdentity("writer", "module", "x", "write")


def test_llmt_federation_rejects_unknown_parent() -> None:
    index = GitHubMemoryIndex()
    with pytest.raises(ValueError, match="unknown LLMT parent"):
        LLMTFederationCompiler(index).compile(
            _request("x"), [LLMTIdentity("child", "module", "x", "draft", "missing")]
        )


def test_full_evolution_court_is_deterministic_and_oak_pass() -> None:
    index = GitHubMemoryIndex()
    index.capabilities["github.memory.full"] = _cap(
        "github.memory.full", ("pr_index", "capability_graph")
    )
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=447,
            state="open",
            title="GitHub cumulative memory",
            body="extends: #417",
            files=("omega_capability_os_t/github_memory.py",),
            updated_at="2026-08-13T01:00:00Z",
        )
    )
    receipt = ReuseOutcomeReceipt(
        "outcome-1", "REQ-1", "REUSE", ("github.memory.full",), "SUCCESS", evidence_refs=("ci:green",)
    )
    identities = (LLMTIdentity("global", "global", "*"),)

    left = compile_evolution_court(index, _request("pr_index", "capability_graph"), outcome_receipts=(receipt,), identities=identities)
    right = compile_evolution_court(index, _request("pr_index", "capability_graph"), outcome_receipts=(receipt,), identities=identities)

    assert left == right
    assert left["oak"]["status"] == "PASS"
    assert len(left["fingerprint"]) == 64
    assert left["residual_artifact"]["generation_allowed"] is False
    assert left["reuse_policy"]["memory_counts"]["M+"] == 1
