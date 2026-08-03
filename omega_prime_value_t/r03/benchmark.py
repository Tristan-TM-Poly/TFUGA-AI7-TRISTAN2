from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .canonical import sha256_hex
from .kernel_ref import kernel_vectors
from .lease import LeaseStore
from .merkle import MerkleTree, verify_merkle_proof
from .pocklington import compile_pocklington_certificate, verify_pocklington_certificate
from .precedence import SourceSnapshot, check_precedence

BIG_PROTH_PRIME = 332041393326771929089  # 9 * 2^65 + 1


def _run_kernel(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    completed = subprocess.run([path], check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def build_benchmark(*, cpp_kernel: str | None = None, rust_kernel: str | None = None) -> dict[str, Any]:
    certificate = compile_pocklington_certificate(BIG_PROTH_PRIME, {2: 65}, max_witness=100)
    certificate_ok, certificate_errors = verify_pocklington_certificate(certificate)

    receipts = [
        {"kind": "candidate", "value": BIG_PROTH_PRIME, "expression": "9*2^65+1"},
        {"kind": "proof", "sha256": certificate.sha256, "method": "Pocklington"},
        {"kind": "verification", "valid": certificate_ok, "errors": certificate_errors},
        {"kind": "oak", "novelty_claimed": False, "record_claimed": False},
    ]
    tree = MerkleTree(receipts)
    proofs = [tree.proof(index) for index in range(len(receipts))]
    merkle_verified = all(verify_merkle_proof(payload, proof) for payload, proof in zip(receipts, proofs))

    with tempfile.TemporaryDirectory(prefix="omega-prime-r03-") as directory:
        database = Path(directory) / "leases.sqlite3"
        store = LeaseStore(database)
        inserted = store.add_tasks(
            [(f"task-{index:03d}", {"candidate": BIG_PROTH_PRIME + 2 * index}) for index in range(8)],
            now=1_700_000_000,
        )
        alpha = store.claim("worker-alpha", limit=3, lease_seconds=10, now=1_700_000_001)
        beta = store.claim("worker-beta", limit=3, lease_seconds=10, now=1_700_000_002)
        for task in alpha:
            store.complete(task.task_id, "worker-alpha", {"status": "screened"}, now=1_700_000_003)
        store.complete(beta[0].task_id, "worker-beta", {"status": "screened"}, now=1_700_000_004)
        expired = store.requeue_expired(now=1_700_000_020)
        gamma = store.claim("worker-gamma", limit=10, lease_seconds=10, now=1_700_000_021)
        for task in gamma:
            store.complete(task.task_id, "worker-gamma", {"status": "screened"}, now=1_700_000_022)
        lease_stats = store.stats()
        lease_events = store.events()

    snapshots = (
        SourceSnapshot(
            source_id="fixture-authority-a",
            authority="authoritative",
            captured_on="2026-08-03",
            coverage="finite-fixture",
            records=(17, 97, 998244353),
        ),
        SourceSnapshot(
            source_id="fixture-authority-b",
            authority="authoritative",
            captured_on="2026-08-03",
            coverage="finite-fixture",
            records=(17, 193, 998244353),
        ),
    )
    known_receipt = check_precedence(998244353, snapshots)
    absent_receipt = check_precedence(BIG_PROTH_PRIME, snapshots)

    python_vectors = kernel_vectors()
    cpp_vectors = _run_kernel(cpp_kernel or os.environ.get("OMEGA_PRIME_CPP_KERNEL"))
    rust_vectors = _run_kernel(rust_kernel or os.environ.get("OMEGA_PRIME_RUST_KERNEL"))
    available = [item for item in (cpp_vectors, rust_vectors) if item is not None]
    kernel_parity = all(item == python_vectors for item in available)

    payload: dict[str, Any] = {
        "status": "CERTIFIED_POCKLINGTON_MERKLE_LEASE_KERNEL_FIXTURES_R0_3",
        "pocklington": {
            "candidate": BIG_PROTH_PRIME,
            "bit_length": BIG_PROTH_PRIME.bit_length(),
            "certificate": certificate.to_dict(),
            "verified": certificate_ok,
            "errors": certificate_errors,
        },
        "merkle": {
            "root": tree.root,
            "leaf_count": tree.leaf_count,
            "all_proofs_verified": merkle_verified,
            "proofs": [proof.to_dict() for proof in proofs],
        },
        "leases": {
            "inserted": inserted,
            "alpha_claimed": len(alpha),
            "beta_claimed": len(beta),
            "expired_requeued": expired,
            "gamma_claimed": len(gamma),
            "stats": lease_stats,
            "event_count": len(lease_events),
            "event_digest": sha256_hex(lease_events),
        },
        "precedence": {
            "known": known_receipt.to_dict(),
            "absent": absent_receipt.to_dict(),
            "source_snapshots": [snapshot.to_dict() for snapshot in snapshots],
        },
        "kernels": {
            "python": python_vectors,
            "cpp": cpp_vectors,
            "rust": rust_vectors,
            "compiled_kernels_available": len(available),
            "parity": kernel_parity,
        },
        "claims": {
            "world_record_claimed": False,
            "global_novelty_claimed": False,
            "economic_value_guaranteed": False,
            "cryptographic_secret_generated": False,
            "distributed_consensus_claimed": False,
            "constant_time_claimed": False,
        },
    }
    payload["sha256"] = sha256_hex(payload)
    return payload
