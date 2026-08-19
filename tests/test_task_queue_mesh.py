import pytest

from tools.task_queue_mesh import QueueItem, QueueState, TaskQueueMesh


def test_next_ready_returns_highest_score():
    mesh = TaskQueueMesh()
    mesh.add(QueueItem("a", "A", "Q0", score=1))
    mesh.add(QueueItem("b", "B", "Q1", score=5))
    assert mesh.next_ready().item_id == "b"


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
