from __future__ import annotations

import json

from omega_game.engines.campaign import plan_campaign, run_campaign_slice
from omega_game.engines.campaign_bundle import WorkerManifest
from omega_game.engines.campaign_coordinator import CampaignCoordinator
from omega_game.engines.evolution import seed_population
from omega_game.engines.experiment_graph import SelectionDecision, build_campaign_experiment_graph
from omega_game.engines.simulation import ArenaConfig


def main() -> int:
    population = seed_population(3, seed=1301)
    manifest = plan_campaign(
        population,
        seeds=(1, 2),
        arena_template=ArenaConfig(max_steps=6, resource_count=3),
        shard_count=2,
    )
    checkpoint, _ = run_campaign_slice(manifest)

    coordinator = CampaignCoordinator(manifest, max_attempts=1)
    coordinator.register_worker(WorkerManifest("worker-a"))
    coordinator.heartbeat("worker-a")
    shard_id = manifest.shards[0].shard_id
    coordinator.assign(shard_id, "worker-a")
    coordinator.acknowledge(shard_id, "worker-a")
    coordinator.succeed(shard_id, "worker-a", checkpoint.checkpoint_receipt)

    first_result = next(iter(checkpoint.completed.values()))
    memory = {
        "plus": {
            "candidate-supported": {
                "agent_id": population[0].agent_id,
                "result_receipt": first_result.result_receipt,
                "checkpoint_receipt": checkpoint.checkpoint_receipt,
            }
        },
        "minus": {
            "boundary": {
                "agent_id": population[0].agent_id,
                "note": "benchmark evidence is not general intelligence"
            }
        },
    }
    decision = SelectionDecision(
        decision_id="retain-candidate",
        subject_node_id=f"agent:{population[0].agent_id}",
        action="retain",
        evidence_receipts=(first_result.result_receipt, checkpoint.checkpoint_receipt),
        score_components={"benchmark_signal": 0.8},
        rationale_code="retain_for_next_experiment",
    )
    graph = build_campaign_experiment_graph(
        manifest,
        checkpoint=checkpoint,
        coordinator_ledger=coordinator.ledger,
        memory_payload=memory,
        decisions=(decision,),
    )
    audit = graph.audit()
    if not audit.accepted:
        raise SystemExit(f"experiment graph audit failed: {audit.flags}")

    decision_node = "decision:retain-candidate"
    print(
        json.dumps(
            {
                "graph_receipt": graph.graph_receipt,
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
                "audit": audit.to_dict(),
                "decision": graph.nodes[decision_node].to_dict(),
                "evidence_closure": graph.evidence_closure(decision_node),
                "boundaries": [
                    "provenance completeness does not prove scientific truth",
                    "many supporting edges do not automatically increase truth probability",
                    "selection decisions remain benchmark-scoped and reviewable"
                ]
            },
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
