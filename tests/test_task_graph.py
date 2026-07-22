import pytest

from tools.task_graph import TaskGraph, TaskNode, TaskStatus


def test_add_node_and_link():
    graph = TaskGraph()
    graph.add_node(TaskNode("goal", "Goal"))
    graph.add_node(TaskNode("test", "Test"))
    graph.link("goal", "test")
    assert graph.edges["goal"] == ("test",)


def test_duplicate_node_rejected():
    graph = TaskGraph()
    node = TaskNode("goal", "Goal")
    graph.add_node(node)
    with pytest.raises(ValueError):
        graph.add_node(node)


def test_blocked_converts_to_safe_alternative():
    graph = TaskGraph()
    graph.add_node(TaskNode("blocked", "Blocked", TaskStatus.BLOCKED))
    converted = graph.convert_blocked("blocked", "create test skeleton")
    assert converted.status == TaskStatus.SAFE_ALTERNATIVE
    assert converted.safe_alternative == "create test skeleton"
