from __future__ import annotations

from omega_capability_os_t.core import Capability
from omega_capability_os_t.github_memory import (
    CapabilityObservation,
    CapabilityRequest,
    GitHubMemoryIndex,
    PRMemory,
    _tokens,
)
from omega_capability_os_t.github_memory_replay import (
    compare_create_first_vs_reuse,
    compile_reuse_bench_court,
    replay_historical_lineage,
)


def _cap(capability_id: str, produces: tuple[str, ...]) -> CapabilityObservation:
    cap = Capability(
        capability_id=capability_id,
        domains=("github", "memory"),
        consumes=("repository",),
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
        source_ref=f"registry:{capability_id}",
        keywords=_tokens((capability_id, *cap.domains, *cap.consumes, *cap.produces)),
    )


def _request() -> CapabilityRequest:
    return CapabilityRequest(
        request_id="REQ-R08",
        description="GitHub memory index and capability graph",
        domains=("github", "memory"),
        consumes=("repository",),
        produces=("pr_index", "capability_graph"),
    )


def test_create_first_vs_full_reuse_avoids_all_output_tokens() -> None:
    index = GitHubMemoryIndex()
    index.capabilities["cap.full"] = _cap(
        "cap.full", ("pr_index", "capability_graph")
    )
    receipt = compare_create_first_vs_reuse(index, _request())
    assert receipt.reuse_action == "REUSE"
    assert receipt.create_first_new_outputs == ("capability_graph", "pr_index")
    assert receipt.reuse_first_residual_outputs == ()
    assert receipt.output_tokens_avoided == 2
    assert receipt.output_token_avoidance_fraction == 1.0
    assert "not measured LOC" in receipt.boundary


def test_create_first_vs_partial_reuse_measures_only_residual_proxy() -> None:
    index = GitHubMemoryIndex()
    index.capabilities["cap.partial"] = _cap("cap.partial", ("pr_index",))
    receipt = compare_create_first_vs_reuse(index, _request())
    assert receipt.reuse_action == "EXTEND"
    assert receipt.reuse_first_residual_outputs == ("capability_graph",)
    assert receipt.output_tokens_avoided == 1
    assert receipt.output_token_avoidance_fraction == 0.5
    assert receipt.generation_allowed is True


def test_no_prior_capability_matches_create_first_baseline() -> None:
    receipt = compare_create_first_vs_reuse(GitHubMemoryIndex(), _request())
    assert receipt.reuse_action == "CREATE"
    assert receipt.reuse_first_residual_outputs == ("capability_graph", "pr_index")
    assert receipt.output_token_avoidance_fraction == 0.0


def test_historical_replay_uses_title_only_and_hides_target_and_future_prs() -> None:
    index = GitHubMemoryIndex()
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=1,
            state="closed",
            title="GitHub memory reusable index",
            body="first implementation",
        )
    )
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=2,
            state="closed",
            title="Unrelated renderer",
            body="unrelated",
        )
    )
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=3,
            state="closed",
            title="GitHub memory federation",
            body="extends: #1\nreuses: #4",
        )
    )
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=4,
            state="open",
            title="GitHub memory future federation",
            body="future",
        )
    )

    report = replay_historical_lineage(index, top_k=2)
    assert report["eligible_target_count"] == 1
    case = report["cases"][0]
    assert case["target_ref"] == "pr:o/r#3"
    assert case["query_mode"] == "title_only"
    assert case["gold_lineage_refs"] == ["pr:o/r#1"]
    assert "pr:o/r#1" in case["hits"]
    assert "pr:o/r#3" not in case["retrieved_refs"]
    assert "pr:o/r#4" not in case["retrieved_refs"]
    assert report["target_leakage_count"] == 0
    assert report["future_leakage_count"] == 0
    assert report["micro_recall_at_k"] == 1.0


def test_historical_replay_skips_targets_without_explicit_past_lineage() -> None:
    index = GitHubMemoryIndex()
    index.add_pr(PRMemory(repository="o/r", number=1, state="closed", title="Old"))
    index.add_pr(PRMemory(repository="o/r", number=2, state="open", title="New"))
    report = replay_historical_lineage(index, top_k=1)
    assert report["eligible_target_count"] == 0
    assert report["skipped_no_lineage_count"] == 2
    assert report["micro_recall_at_k"] == 0.0
    assert report["future_leakage_count"] == 0


def test_replay_court_is_deterministic_and_oak_pass() -> None:
    index = GitHubMemoryIndex()
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=1,
            state="closed",
            title="GitHub memory reusable index",
        )
    )
    index.add_pr(
        PRMemory(
            repository="o/r",
            number=2,
            state="open",
            title="GitHub memory federation",
            body="extends: #1",
        )
    )

    left = compile_reuse_bench_court(index, top_k=3)
    right = compile_reuse_bench_court(index, top_k=3)

    assert left == right
    assert left["oak"]["status"] == "PASS"
    assert left["oak"]["synthetic_policy_pass"] is True
    assert left["oak"]["historical_temporal_leakage_free"] is True
    assert left["historical_lineage"]["future_leakage_count"] == 0
    assert len(left["fingerprint"]) == 64
    assert all(row["passed"] for row in left["synthetic_policy_cases"])
    assert "OUTPUT_TOKEN_AVOIDANCE != LOC_OR_TIME_SAVED" in left["oak"]["boundaries"]
