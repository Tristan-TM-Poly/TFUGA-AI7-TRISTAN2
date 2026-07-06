import pytest

from tools.task_queue_mesh import QueueItem, QueueState, TaskQueueMesh


def test_next_ready_returns_highest_score():
    mesh = TaskQueueMesh()
    mesh.add(QueueItem("a", "A", "Q0", score=1))
    mesh.add(QueueItem("b", "B", "Q1", score=5))
    assert mesh.next_ready().item_id == "b"


def test_queue_priority_breaks_ties_toward_lower_queue_id():
    mesh = TaskQueueMesh()
    mesh.add(QueueItem("q3", "Q3 item", "Q3", score=5))
    mesh.add(QueueItem("q1", "Q1 item", "Q1", score=5))
    assert mesh.next_ready().item_id == "q1"


def test_waiting_items_are_listed():
    mesh = TaskQueueMesh()
    mesh.add(QueueItem("a", "A", "Q0", QueueState.WAITING))
    assert mesh.waiting_items()[0].item_id == "a"


def test_duplicate_item_rejected():
    mesh = TaskQueueMesh()
    item = QueueItem("a", "A", "Q0")
    mesh.add(item)
    with pytest.raises(ValueError):
        mesh.add(item)


def test_unknown_queue_rejected():
    mesh = TaskQueueMesh()
    with pytest.raises(ValueError):
        mesh.add(QueueItem("bad", "Bad", "Q99"))


def test_blocked_task_can_be_converted_to_safe_alternative():
    mesh = TaskQueueMesh()
    mesh.add(QueueItem("x", "Blocked", "Q2", QueueState.BLOCKED, score=0, risk=9, reversible=False))
    converted = mesh.convert_blocked("x", "create review packet")
    assert converted.state == QueueState.READY
    assert converted.safe_alternative == "create review packet"
    assert mesh.next_ready().item_id == "x"


def test_fallback_when_no_ready_item_exists():
    mesh = TaskQueueMesh()
    mesh.add(QueueItem("w", "Waiting", "Q1", QueueState.WAITING))
    fallback = mesh.next_or_useful_work()
    assert fallback.item_id == "infinite_useful_work.next_action_note"
    assert fallback.reversible is True
