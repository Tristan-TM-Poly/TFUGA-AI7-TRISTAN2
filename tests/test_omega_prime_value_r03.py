from __future__ import annotations

import copy
import json
import os
import sqlite3
from pathlib import Path

import pytest

from omega_prime_value_t.r03.benchmark import BIG_PROTH_PRIME, build_benchmark
from omega_prime_value_t.r03.kernel_ref import convolution, kernel_vectors, mod_pow, ntt
from omega_prime_value_t.r03.lease import LeaseStore
from omega_prime_value_t.r03.merkle import MerkleTree, verify_merkle_proof
from omega_prime_value_t.r03.pocklington import (
    compile_pocklington_certificate,
    verify_pocklington_certificate,
)
from omega_prime_value_t.r03.precedence import SourceSnapshot, check_precedence
from omega_prime_value_t.r03.probable import (
    deterministic_bases,
    is_prime_u64,
    probable_prime_receipt,
)


@pytest.mark.parametrize(
    "value",
    [2, 3, 5, 7, 11, 13, 17, 97, 193, 65537, 998244353, 18446744073709551557],
)
def test_u64_primes(value: int) -> None:
    assert is_prime_u64(value)


@pytest.mark.parametrize(
    "value",
    [0, 1, 4, 6, 9, 15, 21, 25, 341, 561, 1105, 1729, 18446744073709551615],
)
def test_u64_composites(value: int) -> None:
    assert not is_prime_u64(value)


def test_u64_domain_is_enforced() -> None:
    with pytest.raises(ValueError):
        is_prime_u64(2**64)


def test_probable_prime_bases_are_deterministic() -> None:
    n = (1 << 127) - 1
    assert deterministic_bases(n, 16) == deterministic_bases(n, 16)
    assert len(set(deterministic_bases(n, 16))) == 16


def test_probable_prime_receipt_marks_large_domain_as_probabilistic() -> None:
    receipt = probable_prime_receipt((1 << 127) - 1, rounds=12)
    assert receipt.probable_prime
    assert receipt.deterministic_domain is None
    assert receipt.rounds == 12


def test_pocklington_compiles_and_verifies_large_prime() -> None:
    certificate = compile_pocklington_certificate(BIG_PROTH_PRIME, {2: 65}, max_witness=100)
    valid, errors = verify_pocklington_certificate(certificate)
    assert valid
    assert errors == []
    assert certificate.n > 2**64
    assert certificate.known_factor_product == 2**65
    assert certificate.cofactor == 9
    assert certificate.factors[0].witness == 19


def test_pocklington_is_deterministic() -> None:
    first = compile_pocklington_certificate(BIG_PROTH_PRIME, {2: 65}, max_witness=100)
    second = compile_pocklington_certificate(BIG_PROTH_PRIME, {2: 65}, max_witness=100)
    assert first.to_dict() == second.to_dict()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.__setitem__("n", payload["n"] + 2),
        lambda payload: payload.__setitem__("known_factor_product", 2**64),
        lambda payload: payload["factors"][0].__setitem__("witness", 2),
        lambda payload: payload["oak"].__setitem__("novelty_claimed", True),
        lambda payload: payload.__setitem__("sha256", "0" * 64),
    ],
)
def test_pocklington_tampering_is_rejected(mutation) -> None:
    payload = compile_pocklington_certificate(BIG_PROTH_PRIME, {2: 65}, max_witness=100).to_dict()
    mutation(payload)
    valid, errors = verify_pocklington_certificate(payload)
    assert not valid
    assert errors


def test_pocklington_rejects_insufficient_known_product() -> None:
    with pytest.raises(ValueError, match="F > sqrt"):
        compile_pocklington_certificate(BIG_PROTH_PRIME, {2: 32})


def test_pocklington_rejects_unknown_composite_factor() -> None:
    with pytest.raises(ValueError, match="lacks a valid primality proof"):
        compile_pocklington_certificate(31, {15: 1})


def test_pocklington_rejects_non_divisor_factorization() -> None:
    with pytest.raises(ValueError, match="must divide"):
        compile_pocklington_certificate(97, {5: 1})


def test_pocklington_rejects_even_candidate() -> None:
    with pytest.raises(ValueError, match="odd integer"):
        compile_pocklington_certificate(100, {3: 2})


@pytest.mark.parametrize("leaf_count", [1, 2, 3, 4, 5, 8, 9, 17])
def test_merkle_proofs_cover_all_leaves(leaf_count: int) -> None:
    payloads = [{"index": index, "value": index * index + 1} for index in range(leaf_count)]
    tree = MerkleTree(payloads)
    assert tree.leaf_count == leaf_count
    assert len(tree.root) == 64
    for index, payload in enumerate(payloads):
        assert verify_merkle_proof(payload, tree.proof(index))


def test_merkle_tampering_is_rejected() -> None:
    payloads = [{"index": index} for index in range(5)]
    tree = MerkleTree(payloads)
    proof = tree.proof(3).to_dict()
    assert not verify_merkle_proof({"index": 99}, proof)
    proof["steps"][0]["sibling"] = "0" * 64
    assert not verify_merkle_proof(payloads[3], proof)


def test_merkle_requires_a_leaf() -> None:
    with pytest.raises(ValueError):
        MerkleTree([])


def test_lease_store_distributes_without_overlap(tmp_path: Path) -> None:
    store = LeaseStore(tmp_path / "leases.sqlite3")
    assert store.add_tasks([(f"t{index}", {"i": index}) for index in range(6)], now=100) == 6
    assert store.add_tasks([("t0", {"i": 0})], now=100) == 0
    alpha = store.claim("alpha", limit=3, lease_seconds=10, now=101)
    beta = store.claim("beta", limit=3, lease_seconds=10, now=102)
    assert {task.task_id for task in alpha}.isdisjoint({task.task_id for task in beta})
    assert len(alpha) == len(beta) == 3
    assert store.stats()["leased"] == 6


def test_lease_wrong_owner_cannot_finish(tmp_path: Path) -> None:
    store = LeaseStore(tmp_path / "leases.sqlite3")
    store.add_tasks([("task", {})], now=100)
    store.claim("owner", now=101)
    assert not store.complete("task", "other", {}, now=102)
    assert store.task("task").state == "leased"


def test_lease_renewal_and_completion(tmp_path: Path) -> None:
    store = LeaseStore(tmp_path / "leases.sqlite3")
    store.add_tasks([("task", {})], now=100)
    task = store.claim("owner", lease_seconds=5, now=101)[0]
    assert task.lease_until == 106
    assert store.renew("task", "owner", lease_seconds=20, now=104)
    assert store.complete("task", "owner", {"ok": True}, now=110)
    assert store.task("task").state == "completed"


def test_expired_lease_is_requeued_and_reclaimed(tmp_path: Path) -> None:
    store = LeaseStore(tmp_path / "leases.sqlite3")
    store.add_tasks([("task", {})], now=100)
    store.claim("alpha", lease_seconds=5, now=101)
    assert store.requeue_expired(now=107) == 1
    reclaimed = store.claim("beta", now=108)
    assert [task.task_id for task in reclaimed] == ["task"]
    assert reclaimed[0].attempts == 2


def test_lease_database_integrity_and_events(tmp_path: Path) -> None:
    store = LeaseStore(tmp_path / "leases.sqlite3")
    store.add_tasks([("a", {}), ("b", {})], now=100)
    for task in store.claim("worker", limit=2, now=101):
        store.complete(task.task_id, "worker", {"done": True}, now=102)
    stats = store.stats()
    assert stats["completed"] == 2
    assert stats["integrity_check"] is True
    assert stats["events"] == 6
    assert [event["event_type"] for event in store.events()] == [
        "created", "created", "claimed", "claimed", "completed", "completed"
    ]


def test_lease_sqlite_wal_is_enabled(tmp_path: Path) -> None:
    path = tmp_path / "leases.sqlite3"
    LeaseStore(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def _snapshots(coverage: str = "finite-fixture") -> tuple[SourceSnapshot, SourceSnapshot]:
    return (
        SourceSnapshot("a", "authoritative", "2026-08-03", coverage, (17, 97, 193)),
        SourceSnapshot("b", "authoritative", "2026-08-03", coverage, (17, 257, 65537)),
    )


def test_precedence_known_value() -> None:
    receipt = check_precedence(17, _snapshots())
    assert receipt.status == "known-in-snapshot"
    assert set(receipt.matching_sources) == {"a", "b"}
    assert not receipt.global_novelty_claim_allowed


def test_precedence_absent_value_stays_globally_unproven() -> None:
    receipt = check_precedence(BIG_PROTH_PRIME, _snapshots())
    assert receipt.status == "not-found-in-snapshots"
    assert not receipt.scoped_absence_claim_allowed
    assert not receipt.global_novelty_claim_allowed
    assert "snapshot coverage does not establish global absence" in receipt.limitations


def test_precedence_exact_complete_allows_only_scoped_absence() -> None:
    receipt = check_precedence(99991, _snapshots("exact-complete"))
    assert receipt.scoped_absence_claim_allowed
    assert not receipt.global_novelty_claim_allowed


def test_precedence_without_sources_is_unchecked() -> None:
    receipt = check_precedence(17, ())
    assert receipt.status == "unchecked"
    assert "no source snapshots supplied" in receipt.limitations


def test_kernel_reference_vectors() -> None:
    vectors = kernel_vectors()
    assert vectors["primality"]["998244353"] is True
    assert vectors["primality"]["561"] is False
    assert vectors["convolution"] == [7, 25, 56, 87, 118, 107, 65]
    assert vectors["mod_pow"] == pow(123456789, 12345, 998244353)


def test_ntt_round_trip() -> None:
    values = [1, 2, 3, 4, 5, 6, 7, 8]
    assert ntt(ntt(values), invert=True) == values


def test_convolution_matches_naive() -> None:
    left = [1, 2, 3, 4, 5]
    right = [7, 11, 13]
    expected = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            expected[i + j] += a * b
    assert convolution(left, right) == expected


def test_mod_pow_validation() -> None:
    with pytest.raises(ValueError):
        mod_pow(2, -1, 7)
    with pytest.raises(ValueError):
        mod_pow(2, 3, 0)


def test_benchmark_is_deterministic_without_compiled_kernels() -> None:
    first = build_benchmark()
    second = build_benchmark()
    assert first == second
    assert first["pocklington"]["verified"] is True
    assert first["merkle"]["all_proofs_verified"] is True
    assert first["leases"]["stats"]["completed"] == 8
    assert first["precedence"]["absent"]["global_novelty_claim_allowed"] is False
    assert all(value is False for value in first["claims"].values())


def test_cpp_kernel_parity_when_available() -> None:
    kernel = os.environ.get("OMEGA_PRIME_CPP_KERNEL")
    if not kernel:
        pytest.skip("C++ kernel not compiled in this environment")
    payload = build_benchmark(cpp_kernel=kernel)
    assert payload["kernels"]["cpp"] == payload["kernels"]["python"]
    assert payload["kernels"]["parity"] is True


def test_rust_kernel_parity_when_available() -> None:
    kernel = os.environ.get("OMEGA_PRIME_RUST_KERNEL")
    if not kernel:
        pytest.skip("Rust kernel not compiled in this environment")
    payload = build_benchmark(rust_kernel=kernel)
    assert payload["kernels"]["rust"] == payload["kernels"]["python"]
    assert payload["kernels"]["parity"] is True
