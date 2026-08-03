from pathlib import Path
import pytest

from omega_re_t.sqlite_leases_r06 import SQLiteLeaseQueue


def queue(tmp_path: Path) -> SQLiteLeaseQueue:
    return SQLiteLeaseQueue(tmp_path / "queue.db")


def test_enqueue_is_idempotent(tmp_path):
    q = queue(tmp_path)
    assert q.enqueue((("a", {"x": 1}), ("b", {"x": 2}))) == 2
    assert q.enqueue((("a", {"x": 1}),)) == 0
    assert q.summary()["pending"] == 2


def test_acquire_commit_and_duplicate_same_result(tmp_path):
    q = queue(tmp_path)
    q.enqueue((("a", {"x": 1}),))
    lease = q.acquire(worker_id="w", now=0, ttl=5)
    assert lease is not None
    result = q.commit(lease_id=lease.lease_id, worker_id="w", result={"y": 2}, now=1)
    again = q.commit(lease_id=lease.lease_id, worker_id="w", result={"y": 2}, now=2)
    assert result.result_digest == again.result_digest
    assert q.summary()["committed"] == 1


def test_equivocating_duplicate_rejected(tmp_path):
    q = queue(tmp_path)
    q.enqueue((("a", {"x": 1}),))
    lease = q.acquire(worker_id="w", now=0, ttl=5)
    q.commit(lease_id=lease.lease_id, worker_id="w", result={"y": 2}, now=1)
    with pytest.raises(ValueError):
        q.commit(lease_id=lease.lease_id, worker_id="w", result={"y": 3}, now=2)


def test_expired_lease_reassigned(tmp_path):
    q = queue(tmp_path)
    q.enqueue((("a", {"x": 1}),))
    first = q.acquire(worker_id="w1", now=0, ttl=1)
    second = q.acquire(worker_id="w2", now=2, ttl=2)
    assert second is not None and second.attempt == 2
    with pytest.raises(ValueError):
        q.commit(lease_id=first.lease_id, worker_id="w1", result={"x": 1}, now=2)


def test_heartbeat_extends_lease(tmp_path):
    q = queue(tmp_path)
    q.enqueue((("a", {"x": 1}),))
    lease = q.acquire(worker_id="w", now=0, ttl=2)
    extended = q.heartbeat(lease_id=lease.lease_id, worker_id="w", now=1, ttl=5)
    assert extended.expires_at == 6
    q.commit(lease_id=lease.lease_id, worker_id="w", result={"ok": True}, now=5)


def test_fail_retryable_and_terminal(tmp_path):
    q = queue(tmp_path)
    q.enqueue((("a", {}), ("b", {})))
    first = q.acquire(worker_id="w", now=0, ttl=2)
    q.fail(lease_id=first.lease_id, worker_id="w", now=1, retryable=True)
    retry = q.acquire(worker_id="w2", now=1, ttl=2)
    assert retry.item_id == "a"
    q.fail(lease_id=retry.lease_id, worker_id="w2", now=2, retryable=False)
    assert q.summary()["failed"] == 1


def test_event_chain_deterministic(tmp_path):
    q = queue(tmp_path)
    q.enqueue((("a", {}),))
    lease = q.acquire(worker_id="w", now=0, ttl=2)
    q.commit(lease_id=lease.lease_id, worker_id="w", result={"ok": True}, now=1)
    chain = q.event_chain()
    assert len(chain) == 2
    assert all(item.startswith("sha256:") for item in chain)


def test_queue_survives_reopen(tmp_path):
    path = tmp_path / "queue.db"
    first = SQLiteLeaseQueue(path)
    first.enqueue((("a", {"x": 1}),))
    lease = first.acquire(worker_id="w", now=0, ttl=4)
    second = SQLiteLeaseQueue(path)
    second.commit(lease_id=lease.lease_id, worker_id="w", result={"ok": True}, now=1)
    assert second.summary()["committed"] == 1


def test_wrong_worker_cannot_heartbeat(tmp_path):
    q = queue(tmp_path)
    q.enqueue((("a", {}),))
    lease = q.acquire(worker_id="w1", now=0, ttl=3)
    with pytest.raises(ValueError):
        q.heartbeat(lease_id=lease.lease_id, worker_id="w2", now=1, ttl=2)
