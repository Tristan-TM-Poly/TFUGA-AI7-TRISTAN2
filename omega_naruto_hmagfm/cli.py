"""Command-line demonstration for Ω-NARUTO-HMAGFM-HGFMnD²."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .benchmark import benchmark_strategies
from .core import AgentProposal, ChakraBudget, ClaimStatus, oak_merge
from .gates import evaluate_publication
from .genjutsu import audit_proposal
from .graph import build_hgfmn_graph
from .integration import to_claim_packet, to_mminus_registry
from .robustness import (
    analyze_decision_robustness,
    default_robustness_scenarios,
)


def _fixture() -> tuple[AgentProposal, ...]:
    common = {
        "hypothesis": "Which strategy selects the best supported result?",
        "cost": ChakraBudget(compute=1.0, memory=1.0, time=1.0),
    }
    return (
        AgentProposal(
            proposal_id="HYPE-A",
            agent_id="clone-hype-a",
            conclusion="The unsupported route wins.",
            status=ClaimStatus.C9_CANON,
            confidence=0.99,
            uncertainty=0.05,
            **common,
        ),
        AgentProposal(
            proposal_id="HYPE-B",
            agent_id="clone-hype-b",
            conclusion="The unsupported route wins.",
            status=ClaimStatus.C9_CANON,
            confidence=0.98,
            uncertainty=0.05,
            **common,
        ),
        AgentProposal(
            proposal_id="SUPPORTED",
            agent_id="clone-supported",
            conclusion="The documented route wins in this fixture.",
            status=ClaimStatus.B6_BENCHMARK,
            confidence=0.79,
            uncertainty=0.10,
            evidence=("benchmark.csv", "baseline.csv", "protocol.md"),
            provenance=("commit:verified", "dataset:v1"),
            **common,
        ),
    )


def build_report() -> dict[str, Any]:
    proposals = _fixture()
    merged = oak_merge(proposals)
    benchmark = benchmark_strategies(
        proposals,
        expected_proposal_id="SUPPORTED",
    )
    accepted = merged.accepted
    gate = (
        evaluate_publication(accepted, human_review_completed=False)
        if accepted is not None
        else None
    )
    findings = {
        proposal.proposal_id: [
            {
                "code": finding.code.value,
                "severity": finding.severity,
                "message": finding.message,
            }
            for finding in audit_proposal(proposal)
        ]
        for proposal in proposals
    }
    mminus = to_mminus_registry(merged)
    graph = build_hgfmn_graph(proposals, merged)
    robustness = analyze_decision_robustness(
        proposals,
        default_robustness_scenarios("SUPPORTED", "HYPE-A"),
    )

    return {
        "schema": "omega_naruto_hmagfm.report.v1.2",
        "oak_boundary": (
            "Local deterministic fixture only; not external validation, "
            "certification, or a physical claim."
        ),
        "accepted": to_claim_packet(merged),
        "ranked_proposal_ids": list(merged.ranked_proposal_ids),
        "contradictions": [list(pair) for pair in merged.contradictions],
        "publication_gate": None
        if gate is None
        else {
            "decision": gate.decision.value,
            "reasons": list(gate.reasons),
            "release_allowed": gate.release_allowed,
        },
        "genjutsu_findings": findings,
        "benchmark": {
            "expected_proposal_id": benchmark.expected_proposal_id,
            "oak_merge_id": benchmark.oak_merge_id,
            "majority_vote_id": benchmark.majority_vote_id,
            "highest_confidence_id": benchmark.highest_confidence_id,
            "oak_merge_correct": benchmark.oak_merge_correct,
            "majority_vote_correct": benchmark.majority_vote_correct,
            "highest_confidence_correct": benchmark.highest_confidence_correct,
        },
        "robustness": {
            "base_winner_id": robustness.base_winner_id,
            "stable_fraction": robustness.stable_fraction,
            "unstable_scenarios": list(robustness.unstable_scenarios),
            "scenario_decisions": [
                {
                    "scenario": item.scenario,
                    "winner_id": item.winner_id,
                    "changed": item.changed,
                }
                for item in robustness.scenario_decisions
            ],
            "non_claim": (
                "Sensitivity diagnostics do not establish scientific truth or "
                "global optimality."
            ),
        },
        "hgfmn_graph": graph.to_dict(),
        "mminus": {
            "entries": [
                {
                    "error": entry.error,
                    "rule": entry.rule,
                    "fix": entry.fix,
                    "status": entry.status,
                }
                for entry in mminus.entries
            ],
            "next_action": mminus.next_action,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Ω-NARUTO Kage Bunshin–OAKMerge fixture."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path; stdout is always emitted.",
    )
    parser.add_argument(
        "--graphml-output",
        type=Path,
        help="Optional deterministic HGFMnD² GraphML output path.",
    )
    args = parser.parse_args(argv)

    report = build_report()
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.graphml_output is not None:
        proposals = _fixture()
        graph = build_hgfmn_graph(proposals, oak_merge(proposals))
        args.graphml_output.parent.mkdir(parents=True, exist_ok=True)
        args.graphml_output.write_text(graph.to_graphml(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
