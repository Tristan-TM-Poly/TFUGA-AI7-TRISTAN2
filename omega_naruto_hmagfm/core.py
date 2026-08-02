"""Executable OAK scaffold for Ω-NARUTO-HMAGFM-HGFMnD².

The module converts narrative metaphors into bounded, testable software objects.
It makes no claim that fictional mechanisms exist physically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from math import isfinite
from typing import Iterable, Mapping, Sequence


class ClaimStatus(IntEnum):
    """Monotonic epistemic ladder used by OAKMerge."""

    F0_FICTION = 0
    I1_INTUITION = 1
    H2_HYPOTHESIS = 2
    D3_DEFINITION = 3
    S4_SIMULATION = 4
    P5_PROTOTYPE = 5
    B6_BENCHMARK = 6
    E7_EVIDENCE = 7
    R8_REPLICATED = 8
    C9_CANON = 9


@dataclass(frozen=True)
class ChakraBudget:
    """Bounded resource vector for one clone-agent execution."""

    compute: float = 0.0
    memory: float = 0.0
    energy: float = 0.0
    time: float = 0.0
    attention: float = 0.0
    human_review: float = 0.0

    def __post_init__(self) -> None:
        values = self.as_mapping().values()
        if any(not isfinite(value) or value < 0.0 for value in values):
            raise ValueError("chakra resources must be finite and non-negative")

    def as_mapping(self) -> Mapping[str, float]:
        return {
            "compute": self.compute,
            "memory": self.memory,
            "energy": self.energy,
            "time": self.time,
            "attention": self.attention,
            "human_review": self.human_review,
        }

    def fits_within(self, available: "ChakraBudget") -> bool:
        return all(
            requested <= available.as_mapping()[name]
            for name, requested in self.as_mapping().items()
        )

    def total(self) -> float:
        return sum(self.as_mapping().values())


@dataclass(frozen=True)
class AgentProposal:
    """One isolated Kage Bunshin result submitted to OAKMerge."""

    proposal_id: str
    agent_id: str
    hypothesis: str
    conclusion: str
    status: ClaimStatus
    confidence: float
    evidence: Sequence[str] = field(default_factory=tuple)
    counterevidence: Sequence[str] = field(default_factory=tuple)
    provenance: Sequence[str] = field(default_factory=tuple)
    uncertainty: float = 1.0
    safety_risk: float = 0.0
    privacy_risk: float = 0.0
    ip_risk: float = 0.0
    cost: ChakraBudget = field(default_factory=ChakraBudget)

    def __post_init__(self) -> None:
        if not self.proposal_id.strip() or not self.agent_id.strip():
            raise ValueError("proposal_id and agent_id are required")
        if not self.hypothesis.strip() or not self.conclusion.strip():
            raise ValueError("hypothesis and conclusion are required")
        for name, value in {
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "safety_risk": self.safety_risk,
            "privacy_risk": self.privacy_risk,
            "ip_risk": self.ip_risk,
        }.items():
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")

    @property
    def has_support(self) -> bool:
        return bool(self.evidence) and bool(self.provenance)

    @property
    def publication_blocked(self) -> bool:
        return max(self.safety_risk, self.privacy_risk, self.ip_risk) >= 0.25


@dataclass(frozen=True)
class NegativeMemoryEntry:
    proposal_id: str
    reason: str
    retained_conclusion: str


@dataclass(frozen=True)
class OAKMergeResult:
    accepted: AgentProposal | None
    ranked_proposal_ids: tuple[str, ...]
    contradictions: tuple[tuple[str, str], ...]
    rejected: tuple[NegativeMemoryEntry, ...]
    next_experiment: str | None


_STATUS_WEIGHT = {
    ClaimStatus.F0_FICTION: 0.00,
    ClaimStatus.I1_INTUITION: 0.05,
    ClaimStatus.H2_HYPOTHESIS: 0.15,
    ClaimStatus.D3_DEFINITION: 0.25,
    ClaimStatus.S4_SIMULATION: 0.40,
    ClaimStatus.P5_PROTOTYPE: 0.55,
    ClaimStatus.B6_BENCHMARK: 0.70,
    ClaimStatus.E7_EVIDENCE: 0.82,
    ClaimStatus.R8_REPLICATED: 0.93,
    ClaimStatus.C9_CANON: 1.00,
}


def proposal_score(proposal: AgentProposal) -> float:
    """Return a deterministic evidence-aware ranking score in [0, 1].

    Missing provenance or evidence is strongly penalized. Risk never increases
    the score. The function ranks local proposals; it does not certify truth.
    """

    support = min(len(proposal.evidence), 4) / 4.0
    provenance = min(len(proposal.provenance), 3) / 3.0
    counterevidence_penalty = min(len(proposal.counterevidence), 4) / 8.0
    risk_penalty = max(
        proposal.safety_risk,
        proposal.privacy_risk,
        proposal.ip_risk,
    )
    cost_penalty = min(proposal.cost.total() / 100.0, 0.10)

    raw = (
        0.28 * _STATUS_WEIGHT[proposal.status]
        + 0.22 * proposal.confidence
        + 0.18 * (1.0 - proposal.uncertainty)
        + 0.16 * support
        + 0.16 * provenance
        - 0.12 * counterevidence_penalty
        - 0.25 * risk_penalty
        - cost_penalty
    )
    if not proposal.has_support:
        raw -= 0.30
    return max(0.0, min(1.0, raw))


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _contradictions(
    proposals: Sequence[AgentProposal],
) -> tuple[tuple[str, str], ...]:
    """Detect explicit conclusion disagreement for the same hypothesis.

    Semantic contradiction detection belongs in a later model-assisted layer.
    The deterministic core intentionally uses a conservative exact criterion.
    """

    pairs: list[tuple[str, str]] = []
    for index, left in enumerate(proposals):
        for right in proposals[index + 1 :]:
            same_hypothesis = _normalize(left.hypothesis) == _normalize(
                right.hypothesis
            )
            different_conclusion = _normalize(left.conclusion) != _normalize(
                right.conclusion
            )
            if same_hypothesis and different_conclusion:
                pairs.append((left.proposal_id, right.proposal_id))
    return tuple(pairs)


def oak_merge(
    proposals: Iterable[AgentProposal],
    *,
    available_budget: ChakraBudget | None = None,
) -> OAKMergeResult:
    """Merge clone-agent results while preserving evidence and residues.

    Selection rules:
    - reject over-budget proposals when a budget is supplied;
    - reject publication-blocked proposals from acceptance, but preserve them;
    - require evidence and provenance for acceptance;
    - rank deterministically by evidence-aware score then proposal ID;
    - preserve contradictions and recommend a discriminating experiment.
    """

    items = tuple(proposals)
    if not items:
        return OAKMergeResult(None, (), (), (), None)

    ids = [proposal.proposal_id for proposal in items]
    if len(ids) != len(set(ids)):
        raise ValueError("proposal_id values must be unique")

    contradictions = _contradictions(items)
    rejected: list[NegativeMemoryEntry] = []
    candidates: list[AgentProposal] = []

    for proposal in items:
        if available_budget is not None and not proposal.cost.fits_within(
            available_budget
        ):
            rejected.append(
                NegativeMemoryEntry(
                    proposal.proposal_id,
                    "chakra budget exceeded",
                    proposal.conclusion,
                )
            )
        elif proposal.publication_blocked:
            rejected.append(
                NegativeMemoryEntry(
                    proposal.proposal_id,
                    "privacy, IP, or safety gate blocked acceptance",
                    proposal.conclusion,
                )
            )
        elif not proposal.has_support:
            rejected.append(
                NegativeMemoryEntry(
                    proposal.proposal_id,
                    "missing evidence or provenance",
                    proposal.conclusion,
                )
            )
        else:
            candidates.append(proposal)

    ranked = sorted(
        candidates,
        key=lambda proposal: (-proposal_score(proposal), proposal.proposal_id),
    )
    accepted = ranked[0] if ranked else None

    for proposal in ranked[1:]:
        rejected.append(
            NegativeMemoryEntry(
                proposal.proposal_id,
                "lower evidence-aware rank; retained for future falsification",
                proposal.conclusion,
            )
        )

    next_experiment = None
    if contradictions:
        next_experiment = (
            "Run a preregistered discriminating experiment using the shared "
            "hypothesis, blinded evaluation criteria, identical inputs, and "
            "an explicit failure threshold for every competing conclusion."
        )

    return OAKMergeResult(
        accepted=accepted,
        ranked_proposal_ids=tuple(p.proposal_id for p in ranked),
        contradictions=contradictions,
        rejected=tuple(rejected),
        next_experiment=next_experiment,
    )
