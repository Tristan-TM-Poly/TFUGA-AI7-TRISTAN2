"""Small deterministic benchmarks for Kage Bunshin selection strategies."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from .core import AgentProposal, ChakraBudget, oak_merge


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def majority_vote(proposals: Sequence[AgentProposal]) -> AgentProposal | None:
    """Choose the most common conclusion, then highest confidence.

    This intentionally naive baseline ignores evidence quality and provenance.
    """

    if not proposals:
        return None
    counts = Counter(_normalize(proposal.conclusion) for proposal in proposals)
    winning_conclusion = min(
        (conclusion for conclusion, count in counts.items() if count == max(counts.values())),
        default="",
    )
    candidates = [
        proposal
        for proposal in proposals
        if _normalize(proposal.conclusion) == winning_conclusion
    ]
    return sorted(candidates, key=lambda proposal: (-proposal.confidence, proposal.proposal_id))[0]


def highest_confidence(proposals: Sequence[AgentProposal]) -> AgentProposal | None:
    """Choose reported confidence without inspecting evidence."""

    if not proposals:
        return None
    return sorted(proposals, key=lambda proposal: (-proposal.confidence, proposal.proposal_id))[0]


@dataclass(frozen=True)
class StrategyBenchmark:
    expected_proposal_id: str
    oak_merge_id: str | None
    majority_vote_id: str | None
    highest_confidence_id: str | None

    @property
    def oak_merge_correct(self) -> bool:
        return self.oak_merge_id == self.expected_proposal_id

    @property
    def majority_vote_correct(self) -> bool:
        return self.majority_vote_id == self.expected_proposal_id

    @property
    def highest_confidence_correct(self) -> bool:
        return self.highest_confidence_id == self.expected_proposal_id


def benchmark_strategies(
    proposals: Sequence[AgentProposal],
    *,
    expected_proposal_id: str,
    available_budget: ChakraBudget | None = None,
) -> StrategyBenchmark:
    """Compare OAKMerge with two deliberately weak baselines."""

    oak = oak_merge(proposals, available_budget=available_budget).accepted
    majority = majority_vote(proposals)
    confidence = highest_confidence(proposals)
    return StrategyBenchmark(
        expected_proposal_id=expected_proposal_id,
        oak_merge_id=oak.proposal_id if oak else None,
        majority_vote_id=majority.proposal_id if majority else None,
        highest_confidence_id=confidence.proposal_id if confidence else None,
    )
