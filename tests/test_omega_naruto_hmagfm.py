import pytest

from omega_naruto_hmagfm import (
    AgentProposal,
    ChakraBudget,
    ClaimStatus,
    oak_merge,
    proposal_score,
)


SHARED_HYPOTHESIS = "Parallel exploration improves the selected result."


def proposal(
    proposal_id: str,
    conclusion: str,
    *,
    status: ClaimStatus,
    confidence: float,
    evidence: tuple[str, ...] = (),
    provenance: tuple[str, ...] = (),
    uncertainty: float = 0.2,
    cost: ChakraBudget | None = None,
    safety_risk: float = 0.0,
) -> AgentProposal:
    return AgentProposal(
        proposal_id=proposal_id,
        agent_id=f"clone-{proposal_id}",
        hypothesis=SHARED_HYPOTHESIS,
        conclusion=conclusion,
        status=status,
        confidence=confidence,
        evidence=evidence,
        provenance=provenance,
        uncertainty=uncertainty,
        cost=cost or ChakraBudget(compute=1.0, time=1.0),
        safety_risk=safety_risk,
    )


def test_kage_bunshin_merge_preserves_conflict_and_selects_best_support() -> None:
    unsupported = proposal(
        "KB-001",
        "Parallel exploration always improves results.",
        status=ClaimStatus.H2_HYPOTHESIS,
        confidence=0.99,
    )
    simulation = proposal(
        "KB-002",
        "Parallel exploration improves results in the simulated fixture.",
        status=ClaimStatus.S4_SIMULATION,
        confidence=0.72,
        evidence=("simulation.json",),
        provenance=("seed-42",),
        uncertainty=0.25,
    )
    benchmark = proposal(
        "KB-003",
        "Parallel exploration improves median fixture score by 8 percent.",
        status=ClaimStatus.B6_BENCHMARK,
        confidence=0.83,
        evidence=("benchmark.csv", "baseline.csv", "test_protocol.md"),
        provenance=("commit:abc123", "dataset:v1"),
        uncertainty=0.12,
    )

    result = oak_merge((unsupported, simulation, benchmark))

    assert result.accepted is not None
    assert result.accepted.proposal_id == "KB-003"
    assert result.ranked_proposal_ids == ("KB-003", "KB-002")
    assert len(result.contradictions) == 3
    assert result.next_experiment is not None

    rejected = {entry.proposal_id: entry.reason for entry in result.rejected}
    assert "missing evidence or provenance" in rejected["KB-001"]
    assert "lower evidence-aware rank" in rejected["KB-002"]


def test_budget_gate_blocks_overallocated_clone() -> None:
    expensive = proposal(
        "KB-EXPENSIVE",
        "The expensive route wins.",
        status=ClaimStatus.B6_BENCHMARK,
        confidence=0.95,
        evidence=("result.csv",),
        provenance=("commit:def456",),
        cost=ChakraBudget(compute=12.0, memory=4.0, time=3.0),
    )

    result = oak_merge(
        (expensive,),
        available_budget=ChakraBudget(compute=5.0, memory=5.0, time=5.0),
    )

    assert result.accepted is None
    assert result.rejected[0].reason == "chakra budget exceeded"


def test_safety_gate_preserves_but_does_not_accept_blocked_proposal() -> None:
    blocked = proposal(
        "KB-RISK",
        "Publish private records to improve observability.",
        status=ClaimStatus.E7_EVIDENCE,
        confidence=0.9,
        evidence=("private-records.csv",),
        provenance=("restricted-source",),
        safety_risk=0.6,
    )

    result = oak_merge((blocked,))

    assert result.accepted is None
    assert "safety gate" in result.rejected[0].reason


def test_score_penalizes_unsupported_confidence() -> None:
    unsupported = proposal(
        "KB-HYPE",
        "High confidence without evidence.",
        status=ClaimStatus.C9_CANON,
        confidence=1.0,
    )
    supported = proposal(
        "KB-SUPPORTED",
        "Moderate confidence with evidence.",
        status=ClaimStatus.S4_SIMULATION,
        confidence=0.65,
        evidence=("simulation.json", "protocol.md"),
        provenance=("commit:789",),
    )

    assert proposal_score(supported) > proposal_score(unsupported)


def test_invalid_chakra_budget_is_rejected() -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        ChakraBudget(compute=-1.0)


def test_empty_merge_is_explicit() -> None:
    result = oak_merge(())

    assert result.accepted is None
    assert result.ranked_proposal_ids == ()
    assert result.rejected == ()
    assert result.next_experiment is None
