from dataclasses import replace
import pytest

from omega_re_t.lease_workers_r05 import LeaseQueue, WorkItem
from omega_re_t.public_receipts_r05 import (
    create_receipt,
    generate_keypair,
    sign,
    verify,
    verify_chain,
    verify_receipt,
)


def queue():
    return LeaseQueue.from_items(
        (WorkItem("a", {"value": 1}), WorkItem("b", {"value": 2}))
    )


def test_lease_acquisition_is_deterministic():
    lease = queue().acquire(worker_id="w", now=0, ttl=10)
    assert lease is not None
    assert lease.item_id == "a"


def test_expired_lease_is_reissued_with_incremented_attempt():
    work = queue()
    first = work.acquire(worker_id="w1", now=0, ttl=1)
    assert first is not None
    second = work.acquire(worker_id="w2", now=1, ttl=1)
    assert second is not None
    assert second.item_id == first.item_id
    assert second.attempt == 2
    assert second.lease_id != first.lease_id


def test_worker_mismatch_is_blocked():
    work = queue()
    lease = work.acquire(worker_id="w1", now=0, ttl=5)
    assert lease is not None
    with pytest.raises(PermissionError):
        work.commit(lease_id=lease.lease_id, worker_id="w2", result={}, now=1)


def test_commit_is_exactly_once_accepted():
    work = queue()
    lease = work.acquire(worker_id="w", now=0, ttl=5)
    assert lease is not None
    result = work.commit(lease_id=lease.lease_id, worker_id="w", result={"ok": True}, now=1)
    assert result.item_id == "a"
    with pytest.raises(KeyError):
        work.commit(lease_id=lease.lease_id, worker_id="w", result={"ok": True}, now=2)


def test_heartbeat_extends_lease():
    work = queue()
    lease = work.acquire(worker_id="w", now=0, ttl=2)
    assert lease is not None
    updated = work.heartbeat(lease_id=lease.lease_id, worker_id="w", now=1, ttl=5)
    assert updated.expires_at == 6
    assert work.summary(now=3)["active_leases"] == 1


def test_lamport_sign_and_verify():
    private = generate_keypair(b"0123456789abcdef-seed")
    signature = sign(b"message", private)
    assert verify(b"message", signature, private.public_key)
    assert not verify(b"different", signature, private.public_key)


def test_public_receipt_verifies():
    private = generate_keypair(b"0123456789abcdef-receipt")
    receipt = create_receipt(
        domain="test",
        sequence=0,
        previous_digest="sha256:" + "0" * 64,
        payload={"x": 1},
        private_key=private,
    )
    assert verify_receipt(receipt)
    assert not verify_receipt(replace(receipt, payload_digest="sha256:" + "f" * 64))


def test_chain_detects_key_reuse_and_reordering():
    genesis = "sha256:" + "0" * 64
    key = generate_keypair(b"0123456789abcdef-shared")
    first = create_receipt(domain="test", sequence=0, previous_digest=genesis, payload={"x": 1}, private_key=key)
    second = create_receipt(domain="test", sequence=1, previous_digest=first.receipt_digest, payload={"x": 2}, private_key=key)
    valid, errors = verify_chain((first, second), genesis=genesis)
    assert not valid
    assert "one_time_key_reuse:1" in errors
    valid, errors = verify_chain((second, first), genesis=genesis)
    assert not valid
    assert errors
