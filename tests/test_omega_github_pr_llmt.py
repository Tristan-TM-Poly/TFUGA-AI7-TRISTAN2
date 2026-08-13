from __future__ import annotations

import pytest

from omega_capability_os_t.github_memory import GitHubMemoryIndex, PRMemory
from omega_capability_os_t.github_pr_llmt import (
    compile_pr_llmt_portfolio,
    compile_pr_work_packet,
    rank_prior_candidates,
)


def _index() -> GitHubMemoryIndex:
    repository = "o/r"
    index = GitHubMemoryIndex()
    index.add_pr(
        PRMemory(
            repository=repository,
            number=1,
            state="closed",
            merged=True,
            title="memory foundation",
            body="M-: avoid duplicate memory implementations",
            head_ref="feat/memory-foundation",
            head_sha="a" * 40,
        )
    )
    index.add_pr(
        PRMemory(
            repository=repository,
            number=2,
            state="open",
            draft=True,
            title="memory federation",
            body="extends: #1",
            head_ref="feat/memory-federation",
            base_ref="feat/memory-foundation",
            head_sha="b" * 40,
        )
    )
    index.add_pr(
        PRMemory(
            repository=repository,
            number=3,
            state="open",
            draft=True,
            title="memory intelligence",
            body="extends: #2",
            head_ref="feat/memory-intelligence",
            base_ref="feat/memory-federation",
            head_sha="c" * 40,
        )
    )
    return index


def test_prior_ranker_never_returns_target_or_future_pr() -> None:
    index = _index()
    target = index.prs["pr:o/r#2"]
    refs = rank_prior_candidates(index, target, top_k=8)
    assert refs == ("pr:o/r#1",)
    assert all(int(ref.rsplit("#", 1)[1]) < target.number for ref in refs)


def test_work_packet_separates_prior_ranking_from_later_descendant() -> None:
    index = _index()
    packet = compile_pr_work_packet(index, index.prs["pr:o/r#2"], top_k=8)
    assert packet["target"]["ref"] == "pr:o/r#2"
    assert packet["historical_retrieval"]["ranker_version"] == "frozen-v0.1"
    assert [row["ref"] for row in packet["historical_retrieval"]["candidates"]] == ["pr:o/r#1"]
    assert any(row["target_ref"] == "pr:o/r#1" for row in packet["declared_prior_lineage"])
    assert any(row["source_ref"] == "pr:o/r#3" for row in packet["known_later_descendants"])
    assert packet["inspection_contract"]["write_authority_granted"] is False
    assert packet["inspection_contract"]["merge_authority_granted"] is False


def test_portfolio_packetizes_every_open_or_draft_pr() -> None:
    portfolio = compile_pr_llmt_portfolio(_index(), top_k=8)
    assert portfolio["open_or_draft_pr_count"] == 2
    assert portfolio["packet_count"] == 2
    assert {packet["target"]["ref"] for packet in portfolio["packets"]} == {
        "pr:o/r#2",
        "pr:o/r#3",
    }
    assert portfolio["authority"]["write_authority_granted"] is False
    assert portfolio["authority"]["merge_authority_granted"] is False
    for packet in portfolio["packets"]:
        target_number = packet["target"]["number"]
        assert all(
            candidate["number"] < target_number
            for candidate in packet["historical_retrieval"]["candidates"]
        )


def test_portfolio_is_deterministic() -> None:
    left = compile_pr_llmt_portfolio(_index(), top_k=2)
    right = compile_pr_llmt_portfolio(_index(), top_k=2)
    assert left == right
    assert len(left["fingerprint"]) == 64


def test_closed_target_is_rejected() -> None:
    index = _index()
    with pytest.raises(ValueError):
        compile_pr_work_packet(index, index.prs["pr:o/r#1"])


def test_nonpositive_top_k_is_rejected() -> None:
    index = _index()
    with pytest.raises(ValueError):
        rank_prior_candidates(index, index.prs["pr:o/r#2"], top_k=0)
