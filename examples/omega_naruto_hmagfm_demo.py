"""Minimal Kage Bunshin -> OAKMerge demonstration."""

from omega_naruto_hmagfm import (
    AgentProposal,
    ChakraBudget,
    ClaimStatus,
    oak_merge,
)


HYPOTHESIS = "Parallel agents improve evidence selection."


def main() -> None:
    proposals = (
        AgentProposal(
            proposal_id="clone-intuition",
            agent_id="scout",
            hypothesis=HYPOTHESIS,
            conclusion="The architecture should work in every domain.",
            status=ClaimStatus.I1_INTUITION,
            confidence=0.95,
        ),
        AgentProposal(
            proposal_id="clone-simulation",
            agent_id="simulator",
            hypothesis=HYPOTHESIS,
            conclusion="The architecture improves the synthetic fixture.",
            status=ClaimStatus.S4_SIMULATION,
            confidence=0.72,
            evidence=("synthetic-fixture-result",),
            provenance=("demo-seed-42",),
            uncertainty=0.24,
            cost=ChakraBudget(compute=2.0, time=1.0),
        ),
        AgentProposal(
            proposal_id="clone-benchmark",
            agent_id="oak-bench",
            hypothesis=HYPOTHESIS,
            conclusion="The architecture beats majority vote on the demo benchmark.",
            status=ClaimStatus.B6_BENCHMARK,
            confidence=0.82,
            evidence=("benchmark-result", "baseline-result", "protocol"),
            provenance=("demo-commit", "demo-dataset-v1"),
            uncertainty=0.12,
            cost=ChakraBudget(compute=3.0, time=2.0, human_review=1.0),
        ),
    )

    result = oak_merge(
        proposals,
        available_budget=ChakraBudget(
            compute=10.0,
            memory=10.0,
            energy=10.0,
            time=10.0,
            attention=10.0,
            human_review=10.0,
        ),
    )

    print("accepted:", result.accepted.proposal_id if result.accepted else None)
    print("ranking:", result.ranked_proposal_ids)
    print("contradictions:", result.contradictions)
    print("negative memory:")
    for entry in result.rejected:
        print(f"- {entry.proposal_id}: {entry.reason}")
    print("next experiment:", result.next_experiment)


if __name__ == "__main__":
    main()
