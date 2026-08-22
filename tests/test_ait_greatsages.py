from sage_tristan.greatsages import (
    ClaimClass,
    GAUSS,
    MirrorKind,
    compile_report,
    dependency_layers,
    knowledge_snapshot,
    mirrors,
    pantheon_cycle,
    replay_card,
    to_histoscience_graph,
)


def test_gauss_snapshot_blocks_future_knowledge() -> None:
    snapshot = knowledge_snapshot(GAUSS, 1795)
    assert "cyclotomy_seed" in snapshot.blocked_atom_ids
    assert "gauss_1796_17gon" in snapshot.blocked_discovery_ids
    assert "gauss_1796_17gon" not in snapshot.available_discovery_ids
    assert snapshot.leakage_free is True


def test_gauss_1801_snapshot_contains_only_arrived_discoveries() -> None:
    snapshot = knowledge_snapshot(GAUSS, 1801)
    assert "gauss_1796_17gon" in snapshot.available_discovery_ids
    assert "gauss_1799_fta" in snapshot.available_discovery_ids
    assert "gauss_1801_ceres" in snapshot.available_discovery_ids
    assert "gauss_1809_theoria_motus" in snapshot.blocked_discovery_ids
    assert "least_squares_public" in snapshot.blocked_atom_ids


def test_replay_withholds_target_and_checks_prerequisites() -> None:
    card = replay_card(GAUSS, "gauss_1801_disquisitiones")
    assert card.year == 1801
    assert card.target_withheld is True
    assert card.prerequisites_available is True
    assert card.claim_class is ClaimClass.RECONSTRUCTION


def test_mirror_compiler_emits_eight_epistemically_typed_mirrors() -> None:
    cards = mirrors(GAUSS, "gauss_1801_ceres")
    assert len(cards) == 8
    assert {card.mirror_kind for card in cards} == set(MirrorKind)
    by_kind = {card.mirror_kind: card for card in cards}
    assert by_kind[MirrorKind.FUTURE].claim_class is ClaimClass.COUNTERFACTUAL
    assert by_kind[MirrorKind.TRISTAN].claim_class is ClaimClass.FERTILE_HYPOTHESIS
    assert "analogy limits" in by_kind[MirrorKind.DOMAIN].prompt


def test_discovery_dependency_graph_is_acyclic_and_complete() -> None:
    layers = dependency_layers(GAUSS)
    flattened = [node for layer in layers for node in layer]
    assert len(flattened) == len(GAUSS.discoveries)
    assert set(flattened) == {item.discovery_id for item in GAUSS.discoveries}
    assert flattened.index("gauss_1796_17gon") < flattened.index("gauss_1801_disquisitiones")
    assert flattened.index("gauss_1801_ceres") < flattened.index("gauss_1809_theoria_motus")


def test_histoscience_bridge_is_valid_and_source_connected() -> None:
    graph = to_histoscience_graph(GAUSS)
    audit = graph.audit()
    assert audit.valid is True
    assert audit.node_count == 10
    assert audit.edge_count == 16
    assert audit.orphan_node_ids == ()


def test_report_keeps_oak_claim_boundaries() -> None:
    report = compile_report(GAUSS, 1827)
    assert report["release"] == "R0.1"
    assert report["historical_truth_certified"] is False
    assert report["historical_impersonation_claimed"] is False
    assert report["counterfactuals_are_history"] is False
    assert report["histoscience_graph"]["valid"] is True
    assert len(report["mirror_kinds"]) == 8


def test_existing_ait_pantheon_can_operate_on_a_gated_sage_snapshot() -> None:
    result = pantheon_cycle(GAUSS, 1801, cycles=1, salt="test")
    assert result["engine"] == "AIT-PANTHEON-OMEGA"
    assert result["candidate_space_per_cycle"] == 256
    assert len(result["top16"]) == 16
    assert "Gauss" in result["mission"]
    assert "1801" in result["mission"]
