import omega_naruto_hmagfm as naruto


def test_public_api_exports_r11_operational_surface() -> None:
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
        "audit_proposal",
        "benchmark_strategies",
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
