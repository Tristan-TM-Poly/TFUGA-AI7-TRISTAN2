from __future__ import annotations

import hashlib
import json
import tempfile
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable

from .campaign import CampaignCheckpoint, plan_campaign, run_campaign_slice
from .campaign_bundle import (
    CampaignBundle,
    LocalContentAddressedStore,
    WorkerManifest,
    get_bundle,
    put_bundle,
)
from .campaign_coordinator import CampaignCoordinator, CoordinatorLedger
from .campaign_runtime import compare_process_execution
from .experiment_graph import SelectionDecision, build_campaign_experiment_graph
from .game_spec import GameSpecCompiler
from .layout import ArenaLayout
from .layout_evolution import evaluate_map_generalization, seed_layout_population
from .simulation import ArenaConfig, run_arena_t0
from .verification import audit_match


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class IntegratedOAKBenchConfig:
    seed: int = 1401
    max_steps: int = 8
    layout_count: int = 3
    campaign_shards: int = 2
    process_workers: int = 2
    fairness_threshold: float = 0.50

    def validate(self) -> None:
        if self.max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        if self.layout_count < 3:
            raise ValueError("layout_count must be >= 3 for train/validation split")
        if self.campaign_shards < 1 or self.process_workers < 1:
            raise ValueError("campaign_shards/process_workers must be >= 1")
        if not 0.0 <= self.fairness_threshold <= 1.0:
            raise ValueError("fairness_threshold must be in [0, 1]")


@dataclass(frozen=True)
class FaultInjectionResult:
    fault_id: str
    detected: bool
    detector: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityRecord:
    capability: str
    status: str
    evidence_scope: str
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntegratedOAKBenchReport:
    config: IntegratedOAKBenchConfig
    accepted: bool
    invariant_checks: dict[str, bool]
    receipts: dict[str, str]
    fault_matrix: tuple[FaultInjectionResult, ...]
    capabilities: tuple[CapabilityRecord, ...]
    empirical_timings_seconds: dict[str, float]
    observed_process_speedup: float | None
    deterministic_receipt: str

    def deterministic_payload(self) -> dict[str, Any]:
        return {
            "config": asdict(self.config),
            "accepted": self.accepted,
            "invariant_checks": {key: self.invariant_checks[key] for key in sorted(self.invariant_checks)},
            "receipts": {key: self.receipts[key] for key in sorted(self.receipts)},
            "fault_matrix": [row.to_dict() for row in self.fault_matrix],
            "capabilities": [row.to_dict() for row in self.capabilities],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.deterministic_payload(),
            "empirical_timings_seconds": {
                key: self.empirical_timings_seconds[key]
                for key in sorted(self.empirical_timings_seconds)
            },
            "observed_process_speedup": self.observed_process_speedup,
            "deterministic_receipt": self.deterministic_receipt,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def run_integrated_oakbench(config: IntegratedOAKBenchConfig | None = None) -> IntegratedOAKBenchReport:
    cfg = config or IntegratedOAKBenchConfig()
    cfg.validate()
    timings: dict[str, float] = {}

    def timed(name: str, fn: Callable[[], Any]) -> Any:
        start = time.perf_counter()
        value = fn()
        timings[name] = round(time.perf_counter() - start, 9)
        return value

    spec_payload = _fixed_spec(cfg)
    compiled = timed(
        "compile_spec",
        lambda: GameSpecCompiler(layout_fairness_threshold=cfg.fairness_threshold).compile(spec_payload),
    )
    if not compiled.accepted or compiled.layout is None:
        raise ValueError("integrated benchmark fixed GameSpec must compile and pass OAK")

    first, second = compiled.agents[:2]
    match = timed(
        "arena_match",
        lambda: run_arena_t0(first, second, seed=cfg.seed, config=compiled.config, layout=compiled.layout),
    )
    repeat = run_arena_t0(first, second, seed=cfg.seed, config=compiled.config, layout=compiled.layout)
    match_audit = audit_match(match, layout_fairness_threshold=cfg.fairness_threshold)

    layouts = timed(
        "seed_layout_population",
        lambda: seed_layout_population(
            compiled.layout,
            cfg.layout_count,
            seed=cfg.seed + 1,
            mutation_steps=1,
            repair_attempts=128,
            fairness_threshold=cfg.fairness_threshold,
        ),
    )
    map_generalization = timed(
        "map_generalization",
        lambda: evaluate_map_generalization(
            compiled.agents,
            layouts[:-1],
            layouts[-1:],
            seeds=(cfg.seed + 2,),
            arena_template=ArenaConfig(max_steps=cfg.max_steps),
            fairness_threshold=cfg.fairness_threshold,
        ),
    )

    manifest = timed(
        "plan_campaign",
        lambda: plan_campaign(
            compiled.agents,
            layouts=layouts[:2],
            seeds=(cfg.seed + 3,),
            arena_template=ArenaConfig(max_steps=cfg.max_steps),
            mirrored=True,
            shard_count=cfg.campaign_shards,
            layout_fairness_threshold=cfg.fairness_threshold,
        ),
    )
    checkpoint, campaign_report = timed(
        "campaign_execute",
        lambda: run_campaign_slice(manifest),
    )

    with tempfile.TemporaryDirectory(prefix="omega-oakbench-r100-") as directory:
        store = LocalContentAddressedStore(Path(directory) / "cas")
        worker = WorkerManifest("oakbench-worker", max_concurrent_shards=max(1, cfg.campaign_shards))
        bundle = CampaignBundle.from_state(manifest, checkpoint=checkpoint, workers=(worker,))
        artifact_receipt = timed("bundle_store", lambda: put_bundle(store, bundle))
        restored_bundle = get_bundle(store, artifact_receipt)
        restored_manifest, restored_checkpoint, restored_workers = restored_bundle.restore()
        if restored_checkpoint is None:
            raise ValueError("restored benchmark bundle lost checkpoint")
        restored_checkpoint.validate_for(restored_manifest)

        clean_artifact_bytes = store.get_bytes(artifact_receipt)
        cas_path = store.path_for(artifact_receipt)

        coordinator = CampaignCoordinator(restored_manifest, max_attempts=1)
        coordinator.register_worker(restored_workers[0])
        coordinator.heartbeat(restored_workers[0].worker_id)
        first_shard = restored_manifest.shards[0].shard_id
        coordinator.assign(first_shard, restored_workers[0].worker_id)
        coordinator.acknowledge(first_shard, restored_workers[0].worker_id)
        coordinator.succeed(first_shard, restored_workers[0].worker_id, restored_checkpoint.checkpoint_receipt)
        coordinator_audit = coordinator.audit()

        first_result = next(iter(restored_checkpoint.completed.values()))
        memory = {
            "plus": {
                "integrated-run": {
                    "agent_id": compiled.agents[0].agent_id,
                    "result_receipt": first_result.result_receipt,
                    "checkpoint_receipt": restored_checkpoint.checkpoint_receipt,
                }
            },
            "minus": {
                "boundary": {
                    "agent_id": compiled.agents[0].agent_id,
                    "note": "integrated benchmark evidence is benchmark-scoped",
                }
            },
        }
        decision = SelectionDecision(
            decision_id="retain-integrated-candidate",
            subject_node_id=f"agent:{compiled.agents[0].agent_id}",
            action="retain",
            evidence_receipts=(first_result.result_receipt, restored_checkpoint.checkpoint_receipt),
            score_components={"integrated_signal": 1.0},
            rationale_code="r100_oakbench",
        )
        graph = timed(
            "experiment_graph",
            lambda: build_campaign_experiment_graph(
                restored_manifest,
                checkpoint=restored_checkpoint,
                coordinator_ledger=coordinator.ledger,
                memory_payload=memory,
                decisions=(decision,),
            ),
        )
        graph_audit = graph.audit()
        closure = graph.evidence_closure("decision:retain-integrated-candidate")

        process_comparison = timed(
            "process_comparison",
            lambda: compare_process_execution(restored_manifest, workers=cfg.process_workers),
        )

        fault_matrix = tuple(
            _run_fault_matrix(
                compiled=compiled,
                match=match,
                manifest=restored_manifest,
                checkpoint=restored_checkpoint,
                bundle=restored_bundle,
                store=store,
                artifact_receipt=artifact_receipt,
                clean_artifact_bytes=clean_artifact_bytes,
                cas_path=cas_path,
                coordinator=coordinator,
                first_result=first_result,
                layouts=layouts,
                config=cfg,
            )
        )

    invariant_checks = {
        "compiled_spec_accepted": compiled.accepted,
        "match_audit_accepted": match_audit.accepted,
        "match_replay_deterministic": match.replay_hash == repeat.replay_hash,
        "fixed_layout_identity_present": match.layout_hash == compiled.layout.layout_hash,
        "held_out_map_sets_disjoint": set(map_generalization.training_layout_hashes).isdisjoint(
            map_generalization.validation_layout_hashes
        ),
        "campaign_complete": campaign_report.complete_campaign,
        "bundle_restore_plan_equal": restored_manifest.plan_receipt == manifest.plan_receipt,
        "bundle_restore_checkpoint_equal": restored_checkpoint.checkpoint_receipt == checkpoint.checkpoint_receipt,
        "coordinator_audit_accepted": coordinator_audit.accepted,
        "experiment_graph_audit_accepted": graph_audit.accepted,
        "decision_closure_has_result": any(node_id.startswith("result:") for node_id in closure),
        "decision_closure_has_checkpoint": any(node_id.startswith("checkpoint:") for node_id in closure),
        "process_checkpoint_equivalent": process_comparison.deterministic_equivalence,
        "all_faults_detected": all(row.detected for row in fault_matrix),
    }

    receipts = {
        "layout_hash": compiled.layout.layout_hash,
        "match_replay_hash": match.replay_hash,
        "map_generalization_receipt": map_generalization.receipt_hash,
        "campaign_plan_receipt": manifest.plan_receipt,
        "campaign_checkpoint_receipt": checkpoint.checkpoint_receipt,
        "bundle_receipt": bundle.bundle_receipt,
        "bundle_artifact_sha256": artifact_receipt.content_sha256,
        "coordinator_head_receipt": coordinator.ledger.head_receipt or "",
        "experiment_graph_receipt": graph.graph_receipt,
        "selection_decision_receipt": decision.decision_receipt,
    }
    capabilities = _capability_matrix()
    accepted = all(invariant_checks.values())
    deterministic_payload = {
        "config": asdict(cfg),
        "accepted": accepted,
        "invariant_checks": {key: invariant_checks[key] for key in sorted(invariant_checks)},
        "receipts": {key: receipts[key] for key in sorted(receipts)},
        "fault_matrix": [row.to_dict() for row in fault_matrix],
        "capabilities": [row.to_dict() for row in capabilities],
    }
    return IntegratedOAKBenchReport(
        config=cfg,
        accepted=accepted,
        invariant_checks=invariant_checks,
        receipts=receipts,
        fault_matrix=fault_matrix,
        capabilities=capabilities,
        empirical_timings_seconds=timings,
        observed_process_speedup=process_comparison.observed_speedup,
        deterministic_receipt=_canonical_hash(deterministic_payload),
    )


def _fixed_spec(cfg: IntegratedOAKBenchConfig) -> dict[str, Any]:
    return {
        "spec_id": "r100-integrated-oakbench",
        "version": "0.1",
        "environment": {
            "width": 7,
            "height": 5,
            "initial_energy": 24,
            "harvest_energy": 5,
            "move_cost": 1,
            "attack_cost": 2,
            "attack_damage": 6,
            "max_steps": cfg.max_steps,
        },
        "layout": {
            "width": 7,
            "height": 5,
            "left_spawn": [0, 2],
            "right_spawn": [6, 2],
            "resources": [[2, 1], [2, 3], [4, 1], [4, 3]],
            "obstacles": [[3, 0], [3, 4]],
        },
        "agents": [
            {"agent_id": "oak-alpha", "seek_resource": 0.85, "aggression": 0.25, "conservation": 0.55, "exploration": 0.20},
            {"agent_id": "oak-beta", "seek_resource": 0.50, "aggression": 0.70, "conservation": 0.30, "exploration": 0.40},
            {"agent_id": "oak-gamma", "seek_resource": 0.65, "aggression": 0.45, "conservation": 0.70, "exploration": 0.65},
        ],
        "rules": {"allowed_actions": ["move", "harvest", "attack", "stay"]},
        "metadata": {"purpose": "R1.0 integrated OAKBench"},
    }


def _run_fault_matrix(
    *,
    compiled,
    match,
    manifest,
    checkpoint,
    bundle,
    store,
    artifact_receipt,
    clean_artifact_bytes: bytes,
    cas_path: Path,
    coordinator,
    first_result,
    layouts,
    config: IntegratedOAKBenchConfig,
) -> list[FaultInjectionResult]:
    results: list[FaultInjectionResult] = []

    tampered_match = replace(match, replay_hash="0" * 64)
    results.append(
        FaultInjectionResult(
            "replay_hash_tamper",
            not audit_match(tampered_match, check_determinism=False).accepted,
            "audit_match",
        )
    )

    disconnected = ArenaLayout(
        width=5,
        height=3,
        left_spawn=(0, 1),
        right_spawn=(4, 1),
        obstacles=((2, 0), (2, 1), (2, 2)),
    )
    results.append(
        FaultInjectionResult(
            "disconnected_layout",
            not disconnected.audit(fairness_threshold=1.0).accepted,
            "ArenaLayout.audit",
        )
    )

    checkpoint_copy = CampaignCheckpoint(
        plan_receipt=checkpoint.plan_receipt,
        completed=dict(checkpoint.completed),
    )
    job_id = next(iter(checkpoint_copy.completed))
    checkpoint_copy.completed[job_id] = replace(
        checkpoint_copy.completed[job_id],
        result_receipt="0" * 64,
    )
    results.append(
        FaultInjectionResult(
            "checkpoint_result_tamper",
            _raises_value_error(lambda: checkpoint_copy.validate_for(manifest)),
            "CampaignCheckpoint.validate_for",
        )
    )

    bundle_payload = bundle.to_dict()
    bundle_payload["manifest"] = dict(bundle_payload["manifest"])
    bundle_payload["manifest"]["seeds"] = [999]
    results.append(
        FaultInjectionResult(
            "bundle_manifest_tamper",
            _raises_value_error(lambda: CampaignBundle.from_dict(bundle_payload)),
            "CampaignBundle.from_dict",
        )
    )

    cas_path.write_bytes(b"tampered-cas-bytes")
    results.append(
        FaultInjectionResult(
            "cas_content_tamper",
            _raises_value_error(lambda: store.get_bytes(artifact_receipt)),
            "LocalContentAddressedStore.get_bytes",
        )
    )
    cas_path.write_bytes(clean_artifact_bytes)

    events = list(coordinator.ledger.events)
    events[0] = replace(events[0], payload={"tampered": True})
    tampered_ledger = CoordinatorLedger(coordinator.ledger.plan_receipt, events=events)
    results.append(
        FaultInjectionResult(
            "coordinator_event_tamper",
            _raises_value_error(tampered_ledger.validate_chain),
            "CoordinatorLedger.validate_chain",
        )
    )

    unsupported_decision = SelectionDecision(
        decision_id="fault-missing-evidence",
        subject_node_id=f"agent:{compiled.agents[0].agent_id}",
        action="promote",
        evidence_receipts=("missing-evidence-receipt",),
        score_components={"score": 999.0},
        rationale_code="fault_injection",
    )
    unsupported_graph = build_campaign_experiment_graph(
        manifest,
        checkpoint=checkpoint,
        decisions=(unsupported_decision,),
    )
    results.append(
        FaultInjectionResult(
            "selection_missing_evidence",
            not unsupported_graph.audit().accepted,
            "ExperimentGraph.audit",
        )
    )

    results.append(
        FaultInjectionResult(
            "held_out_layout_leakage",
            _raises_value_error(
                lambda: evaluate_map_generalization(
                    compiled.agents,
                    (layouts[0],),
                    (layouts[0],),
                    seeds=(config.seed + 4,),
                    arena_template=ArenaConfig(max_steps=config.max_steps),
                    fairness_threshold=config.fairness_threshold,
                )
            ),
            "evaluate_map_generalization",
        )
    )

    wrong_worker = CampaignCoordinator(manifest, max_attempts=1)
    wrong_worker.register_worker(WorkerManifest("owner"))
    wrong_worker.register_worker(WorkerManifest("intruder"))
    wrong_worker.heartbeat("owner")
    wrong_worker.heartbeat("intruder")
    shard_id = manifest.shards[0].shard_id
    wrong_worker.assign(shard_id, "owner")
    before = len(wrong_worker.ledger.events)
    detected = _raises_value_error(lambda: wrong_worker.acknowledge(shard_id, "intruder"))
    detected = detected and len(wrong_worker.ledger.events) == before
    results.append(
        FaultInjectionResult(
            "wrong_worker_ack",
            detected,
            "CampaignCoordinator ownership gate",
        )
    )

    return results


def _raises_value_error(fn: Callable[[], Any]) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


def _capability_matrix() -> tuple[CapabilityRecord, ...]:
    rows = (
        CapabilityRecord("deterministic Arena-T0 replay", "demonstrated_local", "R0.1 + R1.0 integrated rerun", "not physical truth"),
        CapabilityRecord("sparse/event scheduler", "demonstrated_local", "R0.2 focused tests", "work-unit accounting is not hardware speedup"),
        CapabilityRecord("MAP-Elites quality diversity", "demonstrated_local", "R0.3 focused tests", "coverage is not behavioral completeness"),
        CapabilityRecord("Hall of Fame and M+/M-", "demonstrated_local", "R0.4 focused tests", "memory records are not proof"),
        CapabilityRecord("agent-environment coevolution", "demonstrated_local", "R0.5 held-out seeds", "held-out seeds are not real-world generalization"),
        CapabilityRecord("bounded GameSpec compiler", "demonstrated_local", "R0.6 + R1.0 compile", "compiled spec is not a fun game"),
        CapabilityRecord("fixed hashed layouts", "demonstrated_local", "R0.7 + R1.0 replay provenance", "geometric symmetry is not strategic fairness"),
        CapabilityRecord("adversarial layout evolution", "demonstrated_local", "R0.8 + R1.0 held-out maps", "adversarial score is not universal difficulty"),
        CapabilityRecord("sharded checkpoint campaigns", "demonstrated_local", "R0.9 + R1.0 complete campaign", "sharding is not speedup"),
        CapabilityRecord("local process runtime", "demonstrated_local", "R0.10 + R1.0 process equivalence", "observed speedup is not guaranteed speedup"),
        CapabilityRecord("portable bundles / local CAS / TTL leases", "demonstrated_local", "R0.11 + R1.0 restore", "local CAS/TTL are not remote durability/consensus"),
        CapabilityRecord("causal coordinator ledger", "demonstrated_local", "R0.12 + R1.0 audit", "event-chain integrity is not external event truth"),
        CapabilityRecord("ExperimentGraph evidence closure", "demonstrated_local", "R0.13 + R1.0 decision closure", "provenance closure is not logical proof"),
        CapabilityRecord("distributed consensus", "not_demonstrated", "no real consensus backend", "must not be claimed"),
        CapabilityRecord("remote durable artifact storage", "not_demonstrated", "only local CAS protocol implemented", "must not be claimed"),
        CapabilityRecord("guaranteed multi-process speedup", "not_demonstrated", "only empirical local observation", "must not be claimed"),
        CapabilityRecord("strategic fairness / fun / general intelligence", "not_demonstrated", "outside current benchmark evidence", "must not be inferred from scores"),
    )
    return rows
