from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import gcd
import random
from typing import Any, Callable, Iterable, Mapping

from .hashing import stable_id
from .models import ProblemInstance, StrategySpec

Payload = Mapping[str, Any]
Solver = Callable[[Payload], Any]
Generator = Callable[[random.Random, int], dict[str, Any]]
Oracle = Callable[[Payload], Any]


@dataclass(frozen=True)
class ProblemFamily:
    family_id: str
    domain: str
    title: str
    generate_payload: Generator
    oracle: Oracle
    strategies: tuple[StrategySpec, ...]
    invariants: tuple[str, ...]

    def generate(self, seed: int, difficulty: int) -> ProblemInstance:
        rng = random.Random((seed << 8) ^ difficulty ^ _stable_family_seed(self.family_id))
        payload = self.generate_payload(rng, difficulty)
        expected = self.oracle(payload)
        problem_id = stable_id(
            "problem",
            {
                "family_id": self.family_id,
                "difficulty": difficulty,
                "seed": seed,
                "input": payload,
            },
            length=24,
        )
        return ProblemInstance(
            problem_id=problem_id,
            family_id=self.family_id,
            domain=self.domain,
            difficulty=difficulty,
            seed=seed,
            input_payload=payload,
            expected_output=expected,
            invariants=self.invariants,
        )


def _stable_family_seed(value: str) -> int:
    return sum((index + 1) * ord(char) for index, char in enumerate(value))


def _strategy(
    family_id: str,
    suffix: str,
    name: str,
    *,
    exact: bool,
    complexity: str,
    assumptions: Iterable[str] = (),
) -> StrategySpec:
    return StrategySpec(
        strategy_id=f"strategy.{family_id}.{suffix}",
        family_id=family_id,
        name=name,
        exact=exact,
        claimed_complexity=complexity,
        assumptions=tuple(assumptions),
    )


def _array_payload(rng: random.Random, difficulty: int) -> dict[str, Any]:
    size = 3 + difficulty * 2
    values = [rng.randint(-4 * difficulty, 5 * difficulty + 3) for _ in range(size)]
    if difficulty % 3 == 0:
        values[0] = 0
    return {"values": values}


def _gen_parentheses(rng: random.Random, difficulty: int) -> dict[str, Any]:
    pairs = 1 + difficulty
    chars: list[str] = []
    depth = 0
    for _ in range(pairs * 2):
        if depth == 0 or (depth < pairs and rng.random() < 0.55):
            chars.append("(")
            depth += 1
        else:
            chars.append(")")
            depth -= 1
    chars.extend(")" for _ in range(depth))
    if difficulty % 2 == 0 and len(chars) >= 2:
        chars[0], chars[-1] = chars[-1], chars[0]
    return {"text": "".join(chars)}


def _balanced_oracle(payload: Payload) -> bool:
    depth = 0
    for char in payload["text"]:
        depth += 1 if char == "(" else -1
        if depth < 0:
            return False
    return depth == 0


def _gen_gcd(rng: random.Random, difficulty: int) -> dict[str, Any]:
    factor = rng.randint(1, 3 + difficulty)
    a = factor * rng.randint(2, 20 + difficulty * 3)
    b = factor * rng.randint(2, 20 + difficulty * 3)
    if difficulty % 4 == 0:
        a = 0
    return {"a": a, "b": b}


def _gen_prime_count(rng: random.Random, difficulty: int) -> dict[str, Any]:
    return {"n": 10 + difficulty * 12 + rng.randint(0, 11)}


def _prime_count(payload: Payload) -> int:
    n = int(payload["n"])
    if n < 2:
        return 0
    sieve = [True] * (n + 1)
    sieve[0:2] = [False, False]
    limit = int(n**0.5)
    for value in range(2, limit + 1):
        if sieve[value]:
            start = value * value
            sieve[start : n + 1 : value] = [False] * (((n - start) // value) + 1)
    return sum(sieve)


def _gen_graph(rng: random.Random, difficulty: int) -> dict[str, Any]:
    nodes = 4 + difficulty
    edges: set[tuple[int, int]] = set()
    for node in range(nodes - 1):
        edges.add((node, node + 1))
    extra = difficulty + rng.randint(0, difficulty + 1)
    for _ in range(extra):
        a, b = rng.randrange(nodes), rng.randrange(nodes)
        if a != b:
            edges.add((min(a, b), max(a, b)))
    if difficulty % 3 == 0 and nodes > 5:
        edges = {edge for edge in edges if edge[0] < nodes - 2 and edge[1] < nodes - 2}
    return {
        "nodes": nodes,
        "edges": [list(edge) for edge in sorted(edges)],
        "source": 0,
        "target": nodes - 1,
    }


def _adjacency(payload: Payload) -> list[list[int]]:
    nodes = int(payload["nodes"])
    graph = [[] for _ in range(nodes)]
    for raw_a, raw_b in payload["edges"]:
        a, b = int(raw_a), int(raw_b)
        graph[a].append(b)
        graph[b].append(a)
    for neighbors in graph:
        neighbors.sort()
    return graph


def _shortest_path(payload: Payload) -> int | None:
    graph = _adjacency(payload)
    source, target = int(payload["source"]), int(payload["target"])
    queue = deque([(source, 0)])
    seen = {source}
    while queue:
        node, distance = queue.popleft()
        if node == target:
            return distance
        for neighbor in graph[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, distance + 1))
    return None


def _connected_components(payload: Payload) -> int:
    graph = _adjacency(payload)
    seen: set[int] = set()
    count = 0
    for start in range(len(graph)):
        if start in seen:
            continue
        count += 1
        stack = [start]
        seen.add(start)
        while stack:
            node = stack.pop()
            for neighbor in graph[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
    return count


def _gen_intervals(rng: random.Random, difficulty: int) -> dict[str, Any]:
    intervals: list[list[int]] = []
    for _ in range(3 + difficulty):
        start = rng.randint(-difficulty, 4 * difficulty + 2)
        length = rng.randint(0, difficulty + 3)
        intervals.append([start, start + length])
    rng.shuffle(intervals)
    return {"intervals": intervals}


def _merge_intervals(payload: Payload) -> list[list[int]]:
    items = sorted([list(map(int, item)) for item in payload["intervals"]])
    merged: list[list[int]] = []
    for start, end in items:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def _gen_two_sum(rng: random.Random, difficulty: int) -> dict[str, Any]:
    size = 4 + difficulty * 2
    values = [rng.randint(-3 * difficulty, 4 * difficulty + 4) for _ in range(size)]
    if difficulty % 2:
        i, j = rng.sample(range(size), 2)
        target = values[i] + values[j]
    else:
        target = 10 * difficulty + 101
    return {"values": values, "target": target}


def _two_sum(payload: Payload) -> bool:
    target = int(payload["target"])
    seen: set[int] = set()
    for raw in payload["values"]:
        value = int(raw)
        if target - value in seen:
            return True
        seen.add(value)
    return False


def _max_subarray(payload: Payload) -> int:
    values = [int(value) for value in payload["values"]]
    best = current = values[0]
    for value in values[1:]:
        current = max(value, current + value)
        best = max(best, current)
    return best


def _lis_length(payload: Payload) -> int:
    values = [int(value) for value in payload["values"]]
    tails: list[int] = []
    for value in values:
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < value:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(value)
        else:
            tails[lo] = value
    return len(tails)


def _gen_coin_change(rng: random.Random, difficulty: int) -> dict[str, Any]:
    coins = sorted(set([1, 3, 4, 5 + difficulty % 3, rng.randint(2, 7 + difficulty)]))
    amount = 6 + difficulty * 3 + rng.randint(0, 5)
    return {"coins": coins, "amount": amount}


def _coin_change(payload: Payload) -> int | None:
    amount = int(payload["amount"])
    coins = [int(value) for value in payload["coins"]]
    inf = amount + 1
    dp = [0] + [inf] * amount
    for value in range(1, amount + 1):
        dp[value] = min((dp[value - coin] + 1 for coin in coins if coin <= value), default=inf)
    return None if dp[amount] == inf else dp[amount]


def _gen_dag(rng: random.Random, difficulty: int) -> dict[str, Any]:
    nodes = 4 + difficulty
    edges: set[tuple[int, int]] = set()
    for a in range(nodes):
        for b in range(a + 1, nodes):
            if rng.random() < min(0.15 + difficulty * 0.02, 0.45):
                edges.add((a, b))
    if difficulty % 3 == 0 and nodes >= 3:
        edges.update({(0, 1), (1, 2), (2, 0)})
    return {"nodes": nodes, "edges": [list(edge) for edge in sorted(edges)]}


def _dag_possible(payload: Payload) -> bool:
    nodes = int(payload["nodes"])
    graph = [[] for _ in range(nodes)]
    indegree = [0] * nodes
    for raw_a, raw_b in payload["edges"]:
        a, b = int(raw_a), int(raw_b)
        graph[a].append(b)
        indegree[b] += 1
    queue = deque(node for node, degree in enumerate(indegree) if degree == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    return visited == nodes


def _gen_strings(rng: random.Random, difficulty: int) -> dict[str, Any]:
    alphabet = "abcde"
    length_a = 2 + difficulty
    length_b = 2 + difficulty + (difficulty % 2)
    a = "".join(rng.choice(alphabet) for _ in range(length_a))
    b = "".join(rng.choice(alphabet) for _ in range(length_b))
    if difficulty % 4 == 0:
        b = a
    return {"a": a, "b": b}


def _edit_distance(payload: Payload) -> int:
    a, b = str(payload["a"]), str(payload["b"])
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (char_a != char_b),
                )
            )
        previous = current
    return previous[-1]


def _gen_binary_search(rng: random.Random, difficulty: int) -> dict[str, Any]:
    size = 5 + difficulty * 2
    values = sorted(rng.randint(0, difficulty * 4 + 7) for _ in range(size))
    target = values[rng.randrange(size)] if difficulty % 2 else difficulty * 10 + 99
    return {"values": values, "target": target}


def _binary_first(payload: Payload) -> int:
    values = [int(value) for value in payload["values"]]
    target = int(payload["target"])
    lo, hi = 0, len(values)
    while lo < hi:
        mid = (lo + hi) // 2
        if values[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo if lo < len(values) and values[lo] == target else -1


def _gen_knapsack(rng: random.Random, difficulty: int) -> dict[str, Any]:
    count = 3 + difficulty
    weights = [rng.randint(1, 4 + difficulty) for _ in range(count)]
    values = [rng.randint(1, 8 + difficulty * 2) for _ in range(count)]
    capacity = max(2, sum(weights) // 2)
    return {"weights": weights, "values": values, "capacity": capacity}


def _knapsack(payload: Payload) -> int:
    weights = [int(value) for value in payload["weights"]]
    values = [int(value) for value in payload["values"]]
    capacity = int(payload["capacity"])
    dp = [0] * (capacity + 1)
    for weight, value in zip(weights, values):
        for cap in range(capacity, weight - 1, -1):
            dp[cap] = max(dp[cap], dp[cap - weight] + value)
    return dp[capacity]


def _gen_grid(rng: random.Random, difficulty: int) -> dict[str, Any]:
    rows = 2 + min(difficulty, 6)
    cols = 2 + min(difficulty + 1, 7)
    grid = [[rng.randint(-3, 9) for _ in range(cols)] for _ in range(rows)]
    return {"grid": grid}


def _grid_path(payload: Payload) -> int:
    grid = [[int(value) for value in row] for row in payload["grid"]]
    rows, cols = len(grid), len(grid[0])
    dp = [[0] * cols for _ in range(rows)]
    dp[0][0] = grid[0][0]
    for row in range(rows):
        for col in range(cols):
            if row == 0 and col == 0:
                continue
            candidates = []
            if row:
                candidates.append(dp[row - 1][col])
            if col:
                candidates.append(dp[row][col - 1])
            dp[row][col] = max(candidates) + grid[row][col]
    return dp[-1][-1]


FAMILIES: tuple[ProblemFamily, ...] = (
    ProblemFamily("sum_array", "arrays", "Sum an integer array", _array_payload, lambda p: sum(int(v) for v in p["values"]), (_strategy("sum_array", "positive_only", "Positive-only accumulation", exact=False, complexity="O(n)", assumptions=("all values non-negative",)), _strategy("sum_array", "exact", "Exact accumulation", exact=True, complexity="O(n)")), ("result equals additive fold",)),
    ProblemFamily("count_even", "arrays", "Count even integers", _array_payload, lambda p: sum(int(v) % 2 == 0 for v in p["values"]), (_strategy("count_even", "positive_only", "Count positive evens", exact=False, complexity="O(n)", assumptions=("zero and negatives absent",)), _strategy("count_even", "exact", "Parity count", exact=True, complexity="O(n)")), ("count is between zero and input length",)),
    ProblemFamily("balanced_parentheses", "strings", "Validate parentheses", _gen_parentheses, _balanced_oracle, (_strategy("balanced_parentheses", "count_only", "Equal-count heuristic", exact=False, complexity="O(n)", assumptions=("prefixes are valid",)), _strategy("balanced_parentheses", "stack", "Prefix-depth validation", exact=True, complexity="O(n)")), ("no prefix has negative balance", "final balance is zero")),
    ProblemFamily("gcd_pair", "number_theory", "Greatest common divisor", _gen_gcd, lambda p: gcd(int(p["a"]), int(p["b"])), (_strategy("gcd_pair", "min_divisor", "Minimum-value divisor heuristic", exact=False, complexity="O(1)", assumptions=("one value divides the other",)), _strategy("gcd_pair", "euclid", "Euclidean algorithm", exact=True, complexity="O(log n)")), ("result divides both inputs",)),
    ProblemFamily("prime_count", "number_theory", "Count primes up to n", _gen_prime_count, _prime_count, (_strategy("prime_count", "odd_count", "Odd-number heuristic", exact=False, complexity="O(1)", assumptions=("all odds are prime",)), _strategy("prime_count", "sieve", "Sieve of Eratosthenes", exact=True, complexity="O(n log log n)")), ("count is monotone in n",)),
    ProblemFamily("shortest_path", "graphs", "Unweighted shortest path", _gen_graph, _shortest_path, (_strategy("shortest_path", "dfs_first", "First DFS route", exact=False, complexity="O(V+E)", assumptions=("first route is shortest",)), _strategy("shortest_path", "bfs", "Breadth-first search", exact=True, complexity="O(V+E)")), ("distance is non-negative or unreachable",)),
    ProblemFamily("connected_components", "graphs", "Count connected components", _gen_graph, _connected_components, (_strategy("connected_components", "edge_formula", "Edges-to-components heuristic", exact=False, complexity="O(1)", assumptions=("graph is a forest",)), _strategy("connected_components", "search", "Graph traversal", exact=True, complexity="O(V+E)")), ("component count lies in [1,V]",)),
    ProblemFamily("merge_intervals", "intervals", "Merge overlapping intervals", _gen_intervals, _merge_intervals, (_strategy("merge_intervals", "input_order", "Merge in input order", exact=False, complexity="O(n)", assumptions=("input is sorted",)), _strategy("merge_intervals", "sorted", "Sort then merge", exact=True, complexity="O(n log n)")), ("output intervals are sorted and disjoint",)),
    ProblemFamily("two_sum_exists", "arrays", "Detect a two-sum pair", _gen_two_sum, _two_sum, (_strategy("two_sum_exists", "adjacent", "Adjacent-pair heuristic", exact=False, complexity="O(n)", assumptions=("solution is adjacent",)), _strategy("two_sum_exists", "hash", "Hash complement search", exact=True, complexity="O(n)")), ("two distinct positions are required",)),
    ProblemFamily("max_subarray", "dynamic_programming", "Maximum contiguous subarray sum", _array_payload, _max_subarray, (_strategy("max_subarray", "positive_sum", "Sum positive entries", exact=False, complexity="O(n)", assumptions=("all positive entries are contiguous",)), _strategy("max_subarray", "kadane", "Kadane recurrence", exact=True, complexity="O(n)")), ("selected elements form one contiguous interval",)),
    ProblemFamily("lis_length", "dynamic_programming", "Longest increasing subsequence length", _array_payload, _lis_length, (_strategy("lis_length", "longest_run", "Longest increasing run", exact=False, complexity="O(n)", assumptions=("optimal subsequence is contiguous",)), _strategy("lis_length", "tails", "Patience tails", exact=True, complexity="O(n log n)")), ("subsequence preserves original order",)),
    ProblemFamily("coin_change_min", "dynamic_programming", "Minimum coin count", _gen_coin_change, _coin_change, (_strategy("coin_change_min", "greedy", "Largest-coin greedy", exact=False, complexity="O(k log k)", assumptions=("coin system is canonical",)), _strategy("coin_change_min", "dp", "Dynamic programming", exact=True, complexity="O(amount*k)")), ("coins may be reused",)),
    ProblemFamily("dag_possible", "graphs", "Detect whether a directed graph is acyclic", _gen_dag, _dag_possible, (_strategy("dag_possible", "edge_count", "Sparse-edge heuristic", exact=False, complexity="O(1)", assumptions=("E<V implies acyclic",)), _strategy("dag_possible", "kahn", "Kahn topological test", exact=True, complexity="O(V+E)")), ("all vertices must be removable by zero indegree",)),
    ProblemFamily("edit_distance", "strings", "Levenshtein edit distance", _gen_strings, _edit_distance, (_strategy("edit_distance", "mismatch", "Aligned mismatch count", exact=False, complexity="O(n)", assumptions=("no insertions or deletions",)), _strategy("edit_distance", "dp", "Levenshtein dynamic program", exact=True, complexity="O(nm)")), ("insert, delete and substitute each cost one",)),
    ProblemFamily("binary_search_first", "search", "First occurrence in a sorted array", _gen_binary_search, _binary_first, (_strategy("binary_search_first", "any", "Any matching occurrence", exact=False, complexity="O(log n)", assumptions=("duplicates absent",)), _strategy("binary_search_first", "lower_bound", "Lower-bound search", exact=True, complexity="O(log n)")), ("return the smallest matching index",)),
    ProblemFamily("knapsack_01", "optimization", "0/1 knapsack value", _gen_knapsack, _knapsack, (_strategy("knapsack_01", "ratio", "Greedy value/weight ratio", exact=False, complexity="O(n log n)", assumptions=("fractional choices allowed",)), _strategy("knapsack_01", "dp", "Capacity dynamic program", exact=True, complexity="O(nC)")), ("each item is selected at most once",)),
    ProblemFamily("grid_max_path", "dynamic_programming", "Maximum right/down grid path", _gen_grid, _grid_path, (_strategy("grid_max_path", "row_greedy", "Locally best next cell", exact=False, complexity="O(r+c)", assumptions=("local optimum is global",)), _strategy("grid_max_path", "dp", "Grid dynamic program", exact=True, complexity="O(rc)")), ("moves are restricted to right and down",)),
)

FAMILY_BY_ID = {family.family_id: family for family in FAMILIES}


def family_catalog() -> tuple[ProblemFamily, ...]:
    return FAMILIES


def solve(strategy_id: str, payload: Payload) -> Any:
    return _SOLVERS[strategy_id](payload)


def _dfs_first(payload: Payload) -> int | None:
    graph = _adjacency(payload)
    source, target = int(payload["source"]), int(payload["target"])
    seen: set[int] = set()

    def visit(node: int, distance: int) -> int | None:
        if node == target:
            return distance
        seen.add(node)
        for neighbor in graph[node]:
            if neighbor not in seen:
                result = visit(neighbor, distance + 1)
                if result is not None:
                    return result
        return None

    return visit(source, 0)


def _input_order_merge(payload: Payload) -> list[list[int]]:
    merged: list[list[int]] = []
    for raw_start, raw_end in payload["intervals"]:
        start, end = int(raw_start), int(raw_end)
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def _coin_greedy(payload: Payload) -> int | None:
    amount = int(payload["amount"])
    count = 0
    for coin in sorted((int(v) for v in payload["coins"]), reverse=True):
        used, amount = divmod(amount, coin)
        count += used
    return count if amount == 0 else None


def _any_binary(payload: Payload) -> int:
    values = [int(v) for v in payload["values"]]
    target = int(payload["target"])
    lo, hi = 0, len(values) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if values[mid] == target:
            return mid
        if values[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def _knapsack_ratio(payload: Payload) -> int:
    items = sorted(zip(payload["weights"], payload["values"]), key=lambda item: int(item[1]) / int(item[0]), reverse=True)
    capacity = int(payload["capacity"])
    total = 0
    for raw_weight, raw_value in items:
        weight, value = int(raw_weight), int(raw_value)
        if weight <= capacity:
            capacity -= weight
            total += value
    return total


def _grid_greedy(payload: Payload) -> int:
    grid = [[int(value) for value in row] for row in payload["grid"]]
    row = col = 0
    total = grid[0][0]
    while row < len(grid) - 1 or col < len(grid[0]) - 1:
        down = grid[row + 1][col] if row + 1 < len(grid) else None
        right = grid[row][col + 1] if col + 1 < len(grid[0]) else None
        if down is None or (right is not None and right >= down):
            col += 1
        else:
            row += 1
        total += grid[row][col]
    return total


def _longest_run(values: list[int]) -> int:
    if not values:
        return 0
    best = current = 1
    for previous, value in zip(values, values[1:]):
        current = current + 1 if previous < value else 1
        best = max(best, current)
    return best


_SOLVERS: dict[str, Solver] = {
    "strategy.sum_array.positive_only": lambda p: sum(max(0, int(v)) for v in p["values"]),
    "strategy.sum_array.exact": lambda p: sum(int(v) for v in p["values"]),
    "strategy.count_even.positive_only": lambda p: sum(int(v) > 0 and int(v) % 2 == 0 for v in p["values"]),
    "strategy.count_even.exact": lambda p: sum(int(v) % 2 == 0 for v in p["values"]),
    "strategy.balanced_parentheses.count_only": lambda p: str(p["text"]).count("(") == str(p["text"]).count(")"),
    "strategy.balanced_parentheses.stack": _balanced_oracle,
    "strategy.gcd_pair.min_divisor": lambda p: min(abs(int(p["a"])), abs(int(p["b"]))),
    "strategy.gcd_pair.euclid": lambda p: gcd(int(p["a"]), int(p["b"])),
    "strategy.prime_count.odd_count": lambda p: 0 if int(p["n"]) < 2 else 1 + max(0, (int(p["n"]) - 1) // 2),
    "strategy.prime_count.sieve": _prime_count,
    "strategy.shortest_path.dfs_first": _dfs_first,
    "strategy.shortest_path.bfs": _shortest_path,
    "strategy.connected_components.edge_formula": lambda p: max(1, int(p["nodes"]) - len(p["edges"])),
    "strategy.connected_components.search": _connected_components,
    "strategy.merge_intervals.input_order": _input_order_merge,
    "strategy.merge_intervals.sorted": _merge_intervals,
    "strategy.two_sum_exists.adjacent": lambda p: any(int(a) + int(b) == int(p["target"]) for a, b in zip(p["values"], p["values"][1:])),
    "strategy.two_sum_exists.hash": _two_sum,
    "strategy.max_subarray.positive_sum": lambda p: sum(v for v in map(int, p["values"]) if v > 0),
    "strategy.max_subarray.kadane": _max_subarray,
    "strategy.lis_length.longest_run": lambda p: _longest_run([int(v) for v in p["values"]]),
    "strategy.lis_length.tails": _lis_length,
    "strategy.coin_change_min.greedy": _coin_greedy,
    "strategy.coin_change_min.dp": _coin_change,
    "strategy.dag_possible.edge_count": lambda p: len(p["edges"]) < int(p["nodes"]),
    "strategy.dag_possible.kahn": _dag_possible,
    "strategy.edit_distance.mismatch": lambda p: abs(len(str(p["a"])) - len(str(p["b"]))) + sum(a != b for a, b in zip(str(p["a"]), str(p["b"]))),
    "strategy.edit_distance.dp": _edit_distance,
    "strategy.binary_search_first.any": _any_binary,
    "strategy.binary_search_first.lower_bound": _binary_first,
    "strategy.knapsack_01.ratio": _knapsack_ratio,
    "strategy.knapsack_01.dp": _knapsack,
    "strategy.grid_max_path.row_greedy": _grid_greedy,
    "strategy.grid_max_path.dp": _grid_path,
}
