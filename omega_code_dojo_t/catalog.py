from __future__ import annotations

from collections import deque
from typing import Iterable

from .models import KataTask, TaskCase


def sum_even_squares(values: Iterable[int]) -> int:
    return sum(value * value for value in values if value % 2 == 0)


def balanced_brackets(text: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    opening = set(pairs.values())
    stack: list[str] = []
    for char in text:
        if char in opening:
            stack.append(char)
        elif char in pairs:
            if not stack or stack.pop() != pairs[char]:
                return False
    return not stack


def run_length_encode(text: str) -> list[tuple[str, int]]:
    if not text:
        return []
    encoded: list[tuple[str, int]] = []
    current = text[0]
    count = 1
    for char in text[1:]:
        if char == current:
            count += 1
        else:
            encoded.append((current, count))
            current = char
            count = 1
    encoded.append((current, count))
    return encoded


def shortest_path_unweighted(
    graph: dict[str, tuple[str, ...]], start: str, goal: str
) -> list[str] | None:
    if start == goal:
        return [start]
    queue: deque[tuple[str, list[str]]] = deque([(start, [start])])
    visited = {start}
    while queue:
        node, path = queue.popleft()
        for neighbor in graph.get(node, ()):  # deterministic fixture order
            if neighbor in visited:
                continue
            next_path = [*path, neighbor]
            if neighbor == goal:
                return next_path
            visited.add(neighbor)
            queue.append((neighbor, next_path))
    return None


def original_catalog() -> tuple[KataTask, ...]:
    graph = {
        "A": ("B", "C"),
        "B": ("D",),
        "C": ("D", "E"),
        "D": ("F",),
        "E": (),
        "F": (),
    }
    return (
        KataTask(
            task_id="omega.sum-even-squares.v1",
            title="Sum of even squares",
            function_name="sum_even_squares",
            difficulty=8,
            tags=("arrays", "arithmetic", "filtering"),
            cases=(
                TaskCase("empty", ([],), 0),
                TaskCase("mixed", ([1, 2, 3, 4],), 20),
                TaskCase("negative", ([-4, -3, -2, -1],), 20),
                TaskCase("odd-only", ([1, 3, 5],), 0),
            ),
        ),
        KataTask(
            task_id="omega.balanced-brackets.v1",
            title="Balanced brackets",
            function_name="balanced_brackets",
            difficulty=7,
            tags=("stack", "parsing", "strings"),
            cases=(
                TaskCase("empty", ("",), True),
                TaskCase("nested", ("([]{})",), True),
                TaskCase("crossed", ("([)]",), False),
                TaskCase("premature-close", ("]",), False),
                TaskCase("text", ("a{b[c](d)}e",), True),
            ),
        ),
        KataTask(
            task_id="omega.run-length-encode.v1",
            title="Run-length encoding",
            function_name="run_length_encode",
            difficulty=7,
            tags=("compression", "strings", "state-machine"),
            cases=(
                TaskCase("empty", ("",), []),
                TaskCase("single", ("x",), [("x", 1)]),
                TaskCase("runs", ("aaabbc",), [("a", 3), ("b", 2), ("c", 1)]),
                TaskCase(
                    "alternating",
                    ("abab",),
                    [("a", 1), ("b", 1), ("a", 1), ("b", 1)],
                ),
            ),
        ),
        KataTask(
            task_id="omega.shortest-path-unweighted.v1",
            title="Shortest path in an unweighted graph",
            function_name="shortest_path_unweighted",
            difficulty=6,
            tags=("graphs", "breadth-first-search", "paths"),
            cases=(
                TaskCase("identity", (graph, "A", "A"), ["A"]),
                TaskCase("shortest", (graph, "A", "D"), ["A", "B", "D"]),
                TaskCase("deeper", (graph, "A", "F"), ["A", "B", "D", "F"]),
                TaskCase("unreachable", (graph, "E", "A"), None),
            ),
        ),
    )


REFERENCE_SOLVERS = {
    "omega.sum-even-squares.v1": sum_even_squares,
    "omega.balanced-brackets.v1": balanced_brackets,
    "omega.run-length-encode.v1": run_length_encode,
    "omega.shortest-path-unweighted.v1": shortest_path_unweighted,
}
