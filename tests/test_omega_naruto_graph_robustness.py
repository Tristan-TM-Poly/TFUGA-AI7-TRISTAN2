from xml.etree import ElementTree

import pytest

from omega_naruto_hmagfm import (
    AgentProposal,
    ChakraBudget,
    ClaimStatus,
    ProposalPerturbation,
    RobustnessScenario,
    analyze_decision_robustness,
    build_hgfmn_graph,
    default_robustness_scenarios,
    oak_merge,
)


def fixture() -> tuple[AgentProposal, ...]:
    shared = {
        "hypothesis": "Which proposal is best supported?",
        "cost": ChakraBudget(compute=1.0, memory=1.0, time=1.0),
    }
    return (
        AgentProposal(
            proposal_id="HYPE-A",
            agent_id="clone-a",
            conclusion="Unsupported consensus wins.",
            status=ClaimStatus.C9_CANON,
            confidence=0.99,
            uncertainty=0.05,
            **shared,
        ),
        AgentProposal(
            proposal_id="HYPE-B",
            agent_id="clone-b",
            conclusion="Unsupported consensus wins.",
            status=ClaimStatus.C9_CANON,
            confidence=0.98,
            uncertainty=0.05,
            **shared,
        ),
        AgentProposal(
            proposal_id="SUPPORTED",
            agent_id="clone-supported",
            conclusion="Documented minority wins in this fixture.",
            status=ClaimStatus.B6_BENCHMARK,
            confidence=0.79,
            uncertainty=0.10,
            evidence=("benchmark.csv", "baseline.csv", "protocol.md"),
            provenance=("commit:verified", "dataset:v1"),
            **shared,
        ),
    )


def test_hgfmn_graph_preserves_evidence_provenance_conflicts_and_mminus() -> None:
    proposals = fixture()
    result = oak_merge(proposals)
    graph = build_hgfmn_graph(proposals, result)
    payload = graph.to_dict()
    node_ids = [node["id"] for node in payload["nodes"]]
    edge_relations = [edge["relation"] for edge in payload["edges"]]
    assert len(node_ids) == len(set(node_ids))
    assert "proposal:SUPPORTED" in node_ids
    assert "oak:decision" in node_ids
    assert edge_relations.count("supported_by") == 3
    assert edge_relations.count("derived_from") == 2
    assert edge_relations.count("retains_in_mminus") == 2
    assert edge_relations.count("locally_selects") == 1
    assert edge_relations.count("contradicts") == 2


def test_graphml_is_well_formed_and_deterministic() -> None:
    proposals = fixture()
    graph = build_hgfmn_graph(proposals, oak_merge(proposals))
    first = graph.to_graphml()
    second = build_hgfmn_graph(reversed(proposals), oak_merge(proposals)).to_graphml()
    assert first == second
    root = ElementTree.fromstring(first)
    assert root.tag.endswith("graphml")


def test_default_robustness_suite_exposes_one_intentional_instability() -> None:
    proposals = fixture()
    analysis = analyze_decision_robustness(
        proposals,
        default_robustness_scenarios("SUPPORTED", "HYPE-A"),
    )
    assert analysis.base_winner_id == "SUPPORTED"
    assert analysis.stable_fraction == 0.8
    assert analysis.unstable_scenarios == ("accepted_risk_plus_0_30",)
    decisions = {item.scenario: item.winner_id for item in analysis.scenario_decisions}
    assert decisions["accepted_risk_plus_0_30"] is None


def test_robustness_rejects_unknown_proposal_ids() -> None:
    scenario = RobustnessScenario(
        "unknown",
        (ProposalPerturbation("MISSING", confidence_delta=0.1),),
    )
    with pytest.raises(ValueError, match="unknown proposal_id"):
        analyze_decision_robustness(fixture(), (scenario,))
