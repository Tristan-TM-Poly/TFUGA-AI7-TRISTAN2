"""Deterministic demonstrations for Ω-RE-T∞ R0.6."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from typing import Any

from .adaptive_campaign_r06 import CampaignBudget, run_adaptive_campaign
from .byzantine_sim_r06 import deterministic_fault_campaign
from .calibration_chain_r06 import CalibrationRun, build_chain, verify_chain
from .experiment_registry_r06 import ExperimentRegistry, ExperimentSpec
from .nonlinear_design_r06 import ExperimentCandidate, polynomial_predictor, score_experiments
from .open_world_smc_r06 import Observation, Particle, run_smc
from .optional_signatures_r06 import backend_available
from .sqlite_leases_r06 import SQLiteLeaseQueue
from .transparency_log_r06 import TransparencyLog, leaf_hash, verify_inclusion


def smc_demo() -> dict[str, Any]:
    particles = (
        Particle("linear:-1", "linear", -1.0, 0.25, "demo"),
        Particle("linear:1", "linear", 1.0, 0.25, "demo"),
        Particle("quadratic:-1", "quadratic", -1.0, 0.25, "demo"),
        Particle("quadratic:1", "quadratic", 1.0, 0.25, "demo"),
    )

    def predictor(particle: Particle, experiment_id: str) -> float:
        x = {"e0": 0.0, "e1": 1.0, "e2": 2.0}[experiment_id]
        if particle.model_class == "linear":
            return particle.parameter * x
        if particle.model_class == "quadratic":
            return particle.parameter * x * x
        return particle.parameter + 0.5 * x

    report = run_smc(
        particles,
        (Observation("e0", 0.0, 0.2), Observation("e1", 1.1, 0.2), Observation("e2", 3.8, 0.25)),
        predictor,
        seed=17,
        novelty_threshold=2.5,
    )
    return asdict(report)


def design_demo() -> dict[str, Any]:
    candidates = (
        ExperimentCandidate("safe-low", (0.5,), 1.0, 0.05),
        ExperimentCandidate("safe-high", (2.0,), 2.0, 0.10),
        ExperimentCandidate("blocked-risk", (4.0,), 1.0, 0.9),
        ExperimentCandidate("blocked-auth", (1.0,), 0.2, 0.01, authorized=False),
    )
    report = score_experiments(
        candidates,
        (polynomial_predictor((0.0, 1.0)), polynomial_predictor((0.0, 0.5, 0.4))),
        budget=3.0,
        max_risk=0.2,
        novelty={"safe-high": 0.8},
    )
    return asdict(report)


def leases_demo() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        queue = SQLiteLeaseQueue(Path(directory) / "leases.db")
        inserted = queue.enqueue((f"item-{index}", {"value": index}) for index in range(3))
        first = queue.acquire(worker_id="worker-a", now=0, ttl=3)
        assert first is not None
        queue.heartbeat(lease_id=first.lease_id, worker_id="worker-a", now=1, ttl=3)
        committed = queue.commit(lease_id=first.lease_id, worker_id="worker-a", result={"score": 1}, now=2)
        second = queue.acquire(worker_id="worker-b", now=3, ttl=1)
        assert second is not None
        retry = queue.acquire(worker_id="worker-c", now=5, ttl=2)
        assert retry is not None
        queue.fail(lease_id=retry.lease_id, worker_id="worker-c", now=6, retryable=False)
        return {
            "inserted": inserted,
            "first": asdict(first),
            "committed": asdict(committed),
            "summary": queue.summary(),
            "event_chain": queue.event_chain(),
        }


def byzantine_demo() -> dict[str, Any]:
    return {key: asdict(value) for key, value in deterministic_fault_campaign(honest_workers=5, byzantine_workers=2, threshold=4).items()}


def calibration_demo() -> dict[str, Any]:
    runs = (
        CalibrationRun("run-0", "sha256:data0", "sha256:model0", 128, 0.18, 0.55, 0.08),
        CalibrationRun("run-1", "sha256:data1", "sha256:model1", 256, 0.14, 0.45, 0.05),
        CalibrationRun("run-2", "sha256:data2", "sha256:model2", 512, 0.15, 0.44, 0.06),
    )
    chain = build_chain(runs)
    valid, errors = verify_chain(chain)
    return {"valid": valid, "errors": errors, "receipts": [asdict(item) for item in chain]}


def registry_demo() -> dict[str, Any]:
    registry = ExperimentRegistry()
    digest_a = registry.register(ExperimentSpec("exp-a", {"x": 1.0}, "signal", "synthetic-owned", True, 0.1, 1.0))
    digest_b = registry.register(ExperimentSpec("exp-b", {"x": 2.0}, "signal", "synthetic-owned", True, 0.2, 1.5))
    registry.append_observation("exp-a", value=1.2, uncertainty=0.1, instrument_digest="sha256:instrument", timestamp_label="t0", source="fixture")
    registry.append_observation("exp-b", value=3.9, uncertainty=0.2, instrument_digest="sha256:instrument", timestamp_label="t1", source="fixture")
    return {"spec_digests": [digest_a, digest_b], "snapshot": [asdict(item) for item in registry.snapshot()], "audit": registry.audit()}


def transparency_demo() -> dict[str, Any]:
    log = TransparencyLog()
    log.append(kind="calibration", payload={"run": 0, "brier": 0.18}, provenance="fixture")
    first = log.checkpoint()
    log.append(kind="calibration", payload={"run": 1, "brier": 0.14}, provenance="fixture")
    log.append(kind="worker-audit", payload={"equivocations": 0}, provenance="fixture")
    second = log.checkpoint()
    entry, proof, checkpoint = log.prove(1)
    audit_valid, audit_errors = log.audit_checkpoints()
    return {
        "entries": [asdict(item) for item in log.entries],
        "first_checkpoint": asdict(first),
        "second_checkpoint": asdict(second),
        "proof": [asdict(item) for item in proof],
        "proof_valid": verify_inclusion(leaf_hash(asdict(entry)), proof, checkpoint.root_hash),
        "audit": {"valid": audit_valid, "errors": audit_errors},
    }


def campaign_demo() -> dict[str, Any]:
    steps, checkpoint = run_adaptive_campaign(
        (f"exp-{index}" for index in range(10)),
        budget=CampaignBudget(max_rounds=6, max_cost_units=5.0, max_failures=1, max_risk=0.3),
        cost=lambda experiment_id: 1.0,
        risk=lambda experiment_id: 0.1 if experiment_id != "exp-5" else 0.8,
        execute=lambda experiment_id: {"experiment_id": experiment_id, "success": experiment_id != "exp-3"},
        posterior_entropy=lambda sequence: 1.0 / (sequence + 1),
        novelty_mass=lambda sequence: min(1.0, 0.05 * sequence),
    )
    return {"steps": [asdict(item) for item in steps], "checkpoint": asdict(checkpoint)}


def all_demos() -> dict[str, Any]:
    return {
        "schema": "omega-re-r06-demo/1",
        "open_world_smc": smc_demo(),
        "nonlinear_design": design_demo(),
        "sqlite_leases": leases_demo(),
        "byzantine_simulation": byzantine_demo(),
        "calibration_chain": calibration_demo(),
        "experiment_registry": registry_demo(),
        "adaptive_campaign": campaign_demo(),
        "transparency_log": transparency_demo(),
        "optional_ed25519_backend_available": backend_available(),
        "boundaries": {
            "external_execution": False,
            "scientific_validation": False,
            "physical_experiment": False,
            "internal_identity_claimed": False,
            "byzantine_tolerance_certified": False,
            "permanent_total_cap": None,
        },
    }


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-re-r06")
    parser.add_argument("command", choices=("smc", "design", "leases", "byzantine", "calibration", "registry", "campaign", "transparency", "all"))
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    actions = {
        "smc": smc_demo,
        "design": design_demo,
        "leases": leases_demo,
        "byzantine": byzantine_demo,
        "calibration": calibration_demo,
        "registry": registry_demo,
        "campaign": campaign_demo,
        "transparency": transparency_demo,
        "all": all_demos,
    }
    _write(actions[args.command](), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
