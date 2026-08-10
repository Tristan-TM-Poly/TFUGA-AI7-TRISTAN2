from __future__ import annotations

from dataclasses import replace

from omega_game.engines.campaign import plan_campaign, run_campaign_slice
from omega_game.engines.campaign_bundle import WorkerManifest
from omega_game.engines.campaign_coordinator import CampaignCoordinator
from omega_game.engines.evolution import seed_population
from omega_game.engines.experiment_graph import (
    ExperimentGraph,
    ExperimentNode,
    SelectionDecision,
    build_campaign_experiment_graph,
)
from omega_game.engines.layout import ArenaLayout
from omega_game.engines.simulation import ArenaConfig


def _layout() -> ArenaLayout:
    return ArenaLayout(
        width=5,
        height=3,
        left_spawn=(0, 1),
        right_spawn=(4, 1),
        resources=((1, 0), (1, 2), (3, 0), (3, 2)),
    )


def _campaign():
    population = seed_population(3, seed=1301)
    manifest = plan_campaign(
        population,
        layouts=(_layout(),),
        seeds=(1,),
        arena_template=ArenaConfig(max_steps=4),
        shard_count=2,
        mirrored=True,
    )
    checkpoint, _ = run_campaign_slice(manifest)
    return population, manifest, checkpoint


def test_campaign_graph_contains_agents_layout_seed_jobs_results_checkpoint() -> None:
    population, manifest, checkpoint = _campaign()
    graph = build_campaign_experiment_graph(manifest, checkpoint=checkpoint)
    graph.validate()
    kinds = {node.kind for node in graph.nodes.values()}
    assert {"agent", "layout", "seed", "shard", "job", "result", "checkpoint"}.issubset(kinds)
    assert sum(node.kind == "agent" for node in graph.nodes.values()) == len(population)
    assert sum(node.kind == "job" for node in graph.nodes.values()) == manifest.job_count
    assert sum(node.kind == "result" for node in graph.nodes.values()) == manifest.job_count
    assert graph.audit().accepted


def test_graph_receipt_is_deterministic() -> None:
    _, manifest, checkpoint = _campaign()
    a = build_campaign_experiment_graph(manifest, checkpoint=checkpoint)
    b = build_campaign_experiment_graph(manifest, checkpoint=checkpoint)
    assert a.to_json() == b.to_json()
    assert a.graph_receipt == b.graph_receipt


def test_selection_decision_with_present_evidence_is_connected_and_accepted() -> None:
    population, manifest, checkpoint = _campaign()
    first_result = next(iter(checkpoint.completed.values()))
    decision = SelectionDecision(
        decision_id="promote-alpha",
        subject_node_id=f"agent:{population[0].agent_id}",
        action="promote",
        evidence_receipts=(checkpoint.checkpoint_receipt, first_result.result_receipt),
        score_components={"quality": 0.8, "robustness": 0.7},
        rationale_code="benchmark_candidate",
    )
    graph = build_campaign_experiment_graph(manifest, checkpoint=checkpoint, decisions=(decision,))
    audit = graph.audit()
    assert audit.accepted
    decision_id = "decision:promote-alpha"
    support_edges = [edge for edge in graph.edges if edge.target == decision_id and edge.kind == "supports_decision"]
    assert len(support_edges) >= 2
    closure = set(graph.evidence_closure(decision_id))
    assert f"agent:{population[0].agent_id}" in closure
    assert any(node_id.startswith("checkpoint:") for node_id in closure)
    assert any(node_id.startswith("result:") for node_id in closure)
    assert any(node_id.startswith("job:") for node_id in closure)


def test_selection_decision_with_missing_receipt_is_rejected_by_audit() -> None:
    population, manifest, checkpoint = _campaign()
    decision = SelectionDecision(
        decision_id="unsupported",
        subject_node_id=f"agent:{population[0].agent_id}",
        action="promote",
        evidence_receipts=("missing-evidence-receipt",),
        score_components={"score": 999.0},
        rationale_code="score_without_evidence",
    )
    graph = build_campaign_experiment_graph(manifest, checkpoint=checkpoint, decisions=(decision,))
    audit = graph.audit()
    assert not audit.accepted
    assert "decision:unsupported" in audit.missing_decision_evidence
    assert audit.missing_decision_evidence["decision:unsupported"] == ("missing-evidence-receipt",)


def test_selection_decision_requires_evidence_and_known_subject() -> None:
    _, manifest, checkpoint = _campaign()
    for decision in (
        SelectionDecision("none", "agent:missing", "promote", (checkpoint.checkpoint_receipt,)),
        SelectionDecision("empty", "agent:whatever", "promote", ()),
    ):
        try:
            build_campaign_experiment_graph(manifest, checkpoint=checkpoint, decisions=(decision,))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid decision should fail before promotion graph")


def test_coordinator_events_become_causally_linked_graph_nodes() -> None:
    _, manifest, checkpoint = _campaign()
    coordinator = CampaignCoordinator(manifest, max_attempts=1)
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.heartbeat("worker-a")
    shard_id = manifest.shards[0].shard_id
    coordinator.assign(shard_id, "worker-a")
    coordinator.acknowledge(shard_id, "worker-a")
    coordinator.succeed(shard_id, "worker-a", checkpoint.checkpoint_receipt)
    graph = build_campaign_experiment_graph(
        manifest,
        checkpoint=checkpoint,
        coordinator_ledger=coordinator.ledger,
    )
    event_nodes = [node for node in graph.nodes.values() if node.kind == "coordinator_event"]
    assert len(event_nodes) == len(coordinator.ledger.events)
    causal_edges = [edge for edge in graph.edges if edge.kind == "causal_predecessor"]
    assert len(causal_edges) == max(0, len(event_nodes) - 1)
    assert graph.audit().accepted


def test_memory_payload_links_known_agent_layout_and_result_references() -> None:
    population, manifest, checkpoint = _campaign()
    result = next(iter(checkpoint.completed.values()))
    memory = {
        "plus": {
            "good": {
                "agent_id": population[0].agent_id,
                "result_receipt": result.result_receipt,
                "layout_hash": manifest.layouts[0].layout_hash,
            }
        },
        "minus": {
            "bad": {
                "agent_id": population[1].agent_id,
                "reason": "counterexample",
            }
        },
    }
    graph = build_campaign_experiment_graph(manifest, checkpoint=checkpoint, memory_payload=memory)
    memory_nodes = [node for node in graph.nodes.values() if node.kind in {"memory_plus", "memory_minus"}]
    assert len(memory_nodes) == 2
    memory_edges = [edge for edge in graph.edges if edge.kind == "recorded_in_memory"]
    assert len(memory_edges) >= 4
    assert graph.audit().accepted


def test_node_receipt_tamper_is_detected() -> None:
    _, manifest, checkpoint = _campaign()
    graph = build_campaign_experiment_graph(manifest, checkpoint=checkpoint)
    node_id = next(iter(graph.nodes))
    graph.nodes[node_id] = replace(graph.nodes[node_id], node_receipt="0" * 64)
    try:
        graph.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("tampered node receipt should fail")


def test_conflicting_node_definition_and_dangling_edge_fail_closed() -> None:
    graph = ExperimentGraph("test")
    graph.create_node("a", "kind-a", attributes={"x": 1})
    try:
        graph.add_node(ExperimentNode.create("a", "kind-a", attributes={"x": 2}))
    except ValueError:
        pass
    else:
        raise AssertionError("conflicting node definition should fail")
    try:
        graph.connect("a", "missing", "bad")
    except ValueError:
        pass
    else:
        raise AssertionError("dangling edge should fail")
