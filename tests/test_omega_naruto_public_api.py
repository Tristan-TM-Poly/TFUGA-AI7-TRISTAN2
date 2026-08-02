import omega_naruto_hmagfm as naruto


def test_public_api_exports_r12_operational_surface() -> None:
    expected = {
        "AgentProposal",
        "ChakraBudget",
        "ClaimStatus",
        "GateDecision",
        "GatePolicy",
        "GateReport",
        "GenjutsuCode",
        "GenjutsuFinding",
        "StrategyBenchmark",
        "GraphEdge",
        "GraphNode",
        "HGFMGraph",
        "DecisionRobustness",
        "ProposalPerturbation",
        "RobustnessScenario",
        "ScenarioDecision",
        "analyze_decision_robustness",
        "audit_proposal",
        "benchmark_strategies",
        "build_hgfmn_graph",
        "default_robustness_scenarios",
        "evaluate_publication",
        "has_blocking_finding",
        "highest_confidence",
        "majority_vote",
        "oak_merge",
        "proposal_score",
        "to_claim_packet",
        "to_mminus_registry",
    }
    assert expected.issubset(set(naruto.__all__))
    for name in expected:
        assert hasattr(naruto, name)
