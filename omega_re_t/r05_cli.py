"""Command line demonstrations for Ω-RE-T∞ R0.5."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .active_probabilistic_r05 import FiniteHypothesis, run_active_campaign
from .adversarial_workers_r05 import ExpectedLease, WorkerSubmission, audit_submissions
from .campaign_orchestrator_r05 import ResourceEnvelope, plan_shards, run_campaign
from .bounded_cfg_r05 import BoundedCFG
from .drift_monitor_r05 import CalibrationSnapshot, compare_snapshots
from .lease_workers_r05 import LeaseQueue, WorkItem
from .model_expansion_r05 import ModelClass, expand_model_classes
from .nonlinear_hybrid_r05 import HybridGuard, NonlinearHybridSystem, PolynomialDynamics
from .probabilistic_cfg_r05 import ProbabilisticCFG
from .protocol_negotiation_r05 import NegotiationPolicy, ProtocolVersion, negotiate
from .public_receipts_r05 import create_receipt, generate_keypair, verify_chain
from .re1024_calibration_r05 import calibrate, deterministic_re1024_fixture, progressive_windows


def probabilistic_demo() -> dict[str, Any]:
    experiments = ("probe-a", "probe-b", "probe-c")
    hypotheses = (
        FiniteHypothesis("left", {"probe-a": {"0": 0.9, "1": 0.1}, "probe-b": {"0": 0.5, "1": 0.5}, "probe-c": {"0": 0.2, "1": 0.8}}),
        FiniteHypothesis("right", {"probe-a": {"0": 0.1, "1": 0.9}, "probe-b": {"0": 0.5, "1": 0.5}, "probe-c": {"0": 0.8, "1": 0.2}}),
    )
    truth = {"probe-a": "0", "probe-b": "1", "probe-c": "1"}
    report = run_active_campaign(
        hypotheses,
        {"left": 0.5, "right": 0.5},
        experiments,
        lambda experiment: truth[experiment],
        authorized=experiments,
        max_rounds=3,
    )
    return asdict(report)


def expansion_demo() -> dict[str, Any]:
    root = ModelClass("linear", None, 1.0, -8.0, 0.6, "synthetic")

    def generator(parent: ModelClass):
        yield ModelClass("quadratic", parent.class_id, 2.0, -2.0, 0.1, "synthetic-generator")
        yield ModelClass("bad-parent", "other", 3.0, -1.0, 0.05, "synthetic-generator")

    return asdict(expand_model_classes((root,), generator, residual_threshold=0.2))


def grammar_demo() -> dict[str, Any]:
    grammar = BoundedCFG(
        start="S",
        terminal_rules={"N": ("id",), "EQ": ("=",), "V": ("1", "2")},
        binary_rules={"S": (("N", "R"),), "R": (("EQ", "V"),)},
    )
    generated = grammar.generate(max_tokens=3)
    return {
        "accepted": asdict(grammar.parse(("id", "=", "1"))),
        "rejected": asdict(grammar.parse(("id", "1", "="))),
        "generated": generated,
    }


def hybrid_demo() -> dict[str, Any]:
    low = PolynomialDynamics(((0.0, 1.0, -0.1),), degree=2)
    high = PolynomialDynamics(((-0.5, 0.2, 0.0),), degree=2)
    system = NonlinearHybridSystem(
        modes={"low": low, "high": high},
        guards=(HybridGuard("low", "high", lambda state: state[0] >= 1.0),),
    )
    trace = system.simulate(initial_mode="low", initial_state=(0.2,), dt=0.1, steps=20)
    return {"trace": [asdict(point) for point in trace], "claim": "bounded_euler_simulation_only"}


def lease_demo() -> dict[str, Any]:
    queue = LeaseQueue.from_items(WorkItem(f"item-{index}", {"value": index}) for index in range(4))
    first = queue.acquire(worker_id="worker-a", now=0, ttl=3)
    assert first is not None
    queue.commit(lease_id=first.lease_id, worker_id="worker-a", result={"value": 0}, now=1)
    stale = queue.acquire(worker_id="worker-b", now=1, ttl=1)
    assert stale is not None
    retry = queue.acquire(worker_id="worker-c", now=3, ttl=2)
    assert retry is not None
    queue.commit(lease_id=retry.lease_id, worker_id="worker-c", result={"value": 1}, now=4)
    return {"summary": queue.summary(now=4), "results": [asdict(item) for item in queue.results]}


def receipt_demo() -> dict[str, Any]:
    genesis = "sha256:" + "0" * 64
    receipts = []
    previous = genesis
    for sequence in range(3):
        key = generate_keypair(f"omega-re-r05-demo-key-{sequence:02d}".encode())
        receipt = create_receipt(
            domain="omega-re-r05-demo",
            sequence=sequence,
            previous_digest=previous,
            payload={"sequence": sequence, "software_only": True},
            private_key=key,
        )
        receipts.append(receipt)
        previous = receipt.receipt_digest
    valid, errors = verify_chain(receipts, genesis=genesis)
    return {
        "valid": valid,
        "errors": errors,
        "receipt_digests": [item.receipt_digest for item in receipts],
        "public_key_ids": [item.public_key.key_id for item in receipts],
        "claim": "public_integrity_receipt_only",
    }


def calibration_demo() -> dict[str, Any]:
    cases = deterministic_re1024_fixture()
    report = calibrate(cases, logical_cases=1024, materialized_cases=1024)
    windows = progressive_windows(cases, (64, 256, 1024))
    return {
        "report": asdict(report),
        "windows": [
            {
                "executed_cases": item.executed_cases,
                "brier_score": item.brier_score,
                "ece": item.expected_calibration_error,
                "digest": item.digest,
            }
            for item in windows
        ],
    }


def probabilistic_grammar_demo() -> dict[str, Any]:
    grammar = ProbabilisticCFG(
        start="S",
        terminal_rules={"N": {"id": 1.0}, "EQ": {"=": 1.0}, "V": {"1": 0.7, "2": 0.3}},
        binary_rules={"S": {("N", "R"): 1.0}, "R": {("EQ", "V"): 1.0}},
    )
    parsed = grammar.inside(("id", "=", "1"))
    return {
        "parse": asdict(parsed),
        "sample_7": grammar.sample(seed=7, max_tokens=3),
        "sample_8": grammar.sample(seed=8, max_tokens=3),
    }


def protocol_demo() -> dict[str, Any]:
    client = (
        ProtocolVersion(3, "3", frozenset({"auth", "compression", "receipts"})),
        ProtocolVersion(2, "2", frozenset({"auth", "compression"})),
    )
    server = (
        ProtocolVersion(3, "3", frozenset({"auth", "receipts"})),
        ProtocolVersion(2, "2", frozenset({"auth", "compression"})),
    )
    transcript = negotiate(
        client,
        server,
        policy=NegotiationPolicy(required_capabilities=frozenset({"auth", "receipts"}), prevent_downgrade_from_rank=3),
    )
    return asdict(transcript)


def drift_demo() -> dict[str, Any]:
    reference = CalibrationSnapshot("w0", {"low": 50, "high": 50}, 0.10, 0.02, 512)
    current = CalibrationSnapshot("w1", {"low": 25, "high": 75}, 0.14, 0.07, 512)
    return asdict(compare_snapshots(reference, current))


def worker_audit_demo() -> dict[str, Any]:
    leases = (ExpectedLease("a", "lease-a", "worker-a", "sha256:payload-a", 10),)
    submissions = (
        WorkerSubmission("a", "lease-a", "worker-a", "sha256:payload-a", "sha256:result-a", 5),
        WorkerSubmission("a", "lease-a", "worker-a", "sha256:payload-a", "sha256:result-b", 6),
    )
    return asdict(audit_submissions(leases, submissions))


def orchestrator_demo() -> dict[str, Any]:
    envelope = ResourceEnvelope(max_items=8, max_cost_units=10.0, max_failures=2)
    results, checkpoint = run_campaign(
        start_index=0,
        envelope=envelope,
        generator=lambda index: {"index": index, "value": index * index},
        evaluator=lambda item: (item["index"] % 5 != 4, {"score": item["value"] + 1}, 1.0),
    )
    return {
        "results": [asdict(item) for item in results],
        "checkpoint": asdict(checkpoint),
        "shards": plan_shards(start_index=checkpoint.next_index, count=17, shard_count=4),
    }


def all_demos() -> dict[str, Any]:
    return {
        "schema": "omega-re-r05-demo/1",
        "probabilistic": probabilistic_demo(),
        "model_expansion": expansion_demo(),
        "grammar": grammar_demo(),
        "hybrid": hybrid_demo(),
        "leases": lease_demo(),
        "public_receipts": receipt_demo(),
        "re1024_calibration": calibration_demo(),
        "probabilistic_cfg": probabilistic_grammar_demo(),
        "protocol_negotiation": protocol_demo(),
        "drift_monitor": drift_demo(),
        "worker_audit": worker_audit_demo(),
        "orchestrator": orchestrator_demo(),
        "boundaries": {
            "external_execution": False,
            "scientific_validation": False,
            "internal_identity_claimed": False,
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
    parser = argparse.ArgumentParser(prog="omega-re-r05")
    parser.add_argument(
        "command",
        choices=("probabilistic", "expand", "grammar", "hybrid", "leases", "receipts", "calibrate", "pcfg", "protocol", "drift", "worker-audit", "orchestrate", "all"),
    )
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    actions = {
        "probabilistic": probabilistic_demo,
        "expand": expansion_demo,
        "grammar": grammar_demo,
        "hybrid": hybrid_demo,
        "leases": lease_demo,
        "receipts": receipt_demo,
        "calibrate": calibration_demo,
        "pcfg": probabilistic_grammar_demo,
        "protocol": protocol_demo,
        "drift": drift_demo,
        "worker-audit": worker_audit_demo,
        "orchestrate": orchestrator_demo,
        "all": all_demos,
    }
    _write(actions[args.command](), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
