from __future__ import annotations

import tempfile
from pathlib import Path

from ..r03.pocklington import compile_pocklington_certificate
from .budget import BudgetLedger, ComputeBudgetPolicy, ComputeObservation, rank_work_items
from .external import import_external_artifact
from .proof_dag import build_proof_graph, verify_proof_graph
from .residue import compile_proth_residue_program, filter_receipt, verify_residue_program
from .transparency import TransparencyLog, verify_checkpoint

CHILD_PRIME = 332041393326771929089  # 9*2^65 + 1
ROOT_PRIME = 29219642612755929759833  # 88*CHILD_PRIME + 1


def build_recursive_fixture() -> tuple[dict[str, object], dict[str, object]]:
    child = compile_pocklington_certificate(CHILD_PRIME, {2: 65})
    root = compile_pocklington_certificate(
        ROOT_PRIME,
        {2: 3, 11: 1, CHILD_PRIME: 1},
        child_certificates={CHILD_PRIME: child.to_dict()},
        max_witness=100_000,
    )
    return child.to_dict(), root.to_dict()


def deterministic_benchmark() -> dict[str, object]:
    child_certificate, root_certificate = build_recursive_fixture()
    graph = build_proof_graph(root_certificate)
    graph_valid, graph_errors = verify_proof_graph(graph)

    program = compile_proth_residue_program(8, 12, prime_bound=97)
    program_valid, program_errors = verify_residue_program(program)
    residue_receipt = filter_receipt(program, 12, 1, 2047, segment_size=113)

    policy = ComputeBudgetPolicy(
        max_cpu_seconds=1000.0,
        max_candidates=100_000,
        max_energy_kwh=5.0,
        max_cost_cad=50.0,
        reserve_fraction=0.1,
        max_concurrent_leases=4,
    )
    budget = BudgetLedger(policy)
    budget.record(ComputeObservation("sieve", "product", 20.0, 20_000, 0.02, 0.10, 15.0))
    budget.record(ComputeObservation("proof", "research", 35.0, 1, 0.04, 0.20, 40.0))
    budget.record(ComputeObservation("precedence", "prestige", 5.0, 1, 0.005, 0.05, 8.0))
    budget_report = budget.report()
    ranked = rank_work_items(
        [
            {"work_id": "mersenne", "expected_evidence": 8.0, "expected_cpu_seconds": 1000.0, "expected_energy_kwh": 0.4, "expected_cost_cad": 2.0},
            {"work_id": "ntt", "expected_evidence": 20.0, "expected_cpu_seconds": 50.0, "expected_energy_kwh": 0.02, "expected_cost_cad": 0.2},
            {"work_id": "certificate", "expected_evidence": 14.0, "expected_cpu_seconds": 10.0, "expected_energy_kwh": 0.01, "expected_cost_cad": 0.1},
        ]
    )

    external = import_external_artifact(
        b"PRIMO/ECPP fixture metadata only; no theorem claim.",
        format="primo",
        source_label="deterministic-r04-fixture",
    )

    with tempfile.TemporaryDirectory(prefix="omega-prime-r04-") as directory:
        with TransparencyLog(Path(directory) / "transparency.sqlite3") as log:
            log.append("recursive-proof-graph", graph.to_dict())
            log.append("residue-program", program.to_dict())
            log.append("budget-report", budget_report)
            log.append("external-artifact-import", external.to_dict())
            chain_valid, chain_errors = log.verify_chain()
            checkpoint = log.checkpoint(created_at_utc="2026-08-03T00:00:00+00:00")
            checkpoint_valid, checkpoint_errors = verify_checkpoint(checkpoint, log.entries())
            entries = [entry.to_dict() for entry in log.entries()]

    return {
        "status": "CERTIFIED_RECURSIVE_PROOF_TRANSPARENCY_BUDGET_FIXTURES_R0_4",
        "recursive_proof": {
            "child_prime": CHILD_PRIME,
            "root_prime": ROOT_PRIME,
            "root_bits": ROOT_PRIME.bit_length(),
            "child_certificate": child_certificate,
            "graph": graph.to_dict(),
            "valid": graph_valid,
            "errors": graph_errors,
        },
        "residue_compiler": {
            "program": program.to_dict(),
            "valid": program_valid,
            "errors": program_errors,
            "receipt": residue_receipt,
        },
        "transparency": {
            "entries": entries,
            "chain_valid": chain_valid,
            "chain_errors": chain_errors,
            "checkpoint": checkpoint.to_dict(),
            "checkpoint_valid": checkpoint_valid,
            "checkpoint_errors": checkpoint_errors,
        },
        "external_adapter": external.to_dict(),
        "budget": budget_report,
        "ranked_work": ranked,
        "claims": {
            "new_prime_discovered": False,
            "record_prime_claimed": False,
            "global_novelty_claimed": False,
            "external_artifact_verified": False,
            "financial_return_guaranteed": False,
            "unbounded_physical_compute_claimed": False,
            "production_cryptography_claimed": False,
        },
    }
