#!/usr/bin/env python3
"""Ω-DET-ADJ-KRAMER-COMPILER-T∞ R0.2.

Exact stdlib-only extension of R0.1 with:
- a hash-consed, division-free arithmetic-circuit IR for det(A);
- reverse AD of the same circuit for the cofactor gradient / adjugate;
- exact directional determinantal jets det(A+tH);
- generalized higher cofactor ("open-index") tensors;
- singularity ladder from exact rank and complementary minors;
- bipartite structural profiling and a bounded backend router;
- proof-carrying univariate rational-polynomial simplification with a
  domain ledger preserving cancelled denominator factors;
- deterministic compression / shared-computation metrics and benchmark atlas.

OAK boundary:
These are executable combinations of established determinant, cofactor,
compound-matrix, polynomial and graph ideas. R0.2 makes no theorem claim and
no universal speed claim. The hash-consed subset circuit remains exponential.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from fractions import Fraction
from itertools import combinations
from typing import Sequence

try:
    from scripts.omega_kramer_tristan import (
        Scalar,
        _matrix_q,
        _square_q,
        as_q,
        cofactor_adjugate,
        det_bareiss,
        determinant_adjugate_dag,
        matrix_rank,
        qstr,
        transpose,
    )
except ModuleNotFoundError:
    from omega_kramer_tristan import (  # type: ignore
        Scalar,
        _matrix_q,
        _square_q,
        as_q,
        cofactor_adjugate,
        det_bareiss,
        determinant_adjugate_dag,
        matrix_rank,
        qstr,
        transpose,
    )


@dataclass(frozen=True)
class CircuitNode:
    op: str
    args: tuple[int, ...] = ()
    value: Fraction | None = None
    name: str | None = None


class ArithmeticCircuit:
    """Hash-consed straight-line arithmetic circuit over Q."""

    def __init__(self) -> None:
        self.nodes: list[CircuitNode] = []
        self._interned: dict[tuple, int] = {}
        self.zero = self.const(0)
        self.one = self.const(1)
        self.minus_one = self.const(-1)

    def _intern(self, key: tuple, node: CircuitNode) -> int:
        if key in self._interned:
            return self._interned[key]
        idx = len(self.nodes)
        self.nodes.append(node)
        self._interned[key] = idx
        return idx

    def const(self, value: Scalar) -> int:
        q = as_q(value)
        return self._intern(("const", q), CircuitNode("const", value=q))

    def var(self, name: str) -> int:
        return self._intern(("var", name), CircuitNode("var", name=name))

    def add(self, left: int, right: int) -> int:
        if left == self.zero:
            return right
        if right == self.zero:
            return left
        if right < left:
            left, right = right, left
        return self._intern(("add", left, right), CircuitNode("add", (left, right)))

    def mul(self, left: int, right: int) -> int:
        if left == self.zero or right == self.zero:
            return self.zero
        if left == self.one:
            return right
        if right == self.one:
            return left
        if right < left:
            left, right = right, left
        return self._intern(("mul", left, right), CircuitNode("mul", (left, right)))

    def neg(self, node: int) -> int:
        return self.mul(self.minus_one, node)

    def evaluate(self, output: int, environment: dict[str, Scalar]) -> tuple[Fraction, list[Fraction]]:
        values = [Fraction(0)] * len(self.nodes)
        for idx, node in enumerate(self.nodes):
            if node.op == "const":
                assert node.value is not None
                values[idx] = node.value
            elif node.op == "var":
                assert node.name is not None
                values[idx] = as_q(environment[node.name])
            elif node.op == "add":
                values[idx] = values[node.args[0]] + values[node.args[1]]
            elif node.op == "mul":
                values[idx] = values[node.args[0]] * values[node.args[1]]
            else:  # pragma: no cover
                raise ValueError(f"unknown circuit op: {node.op}")
        return values[output], values

    def reverse_gradient(
        self,
        output: int,
        environment: dict[str, Scalar],
    ) -> tuple[Fraction, dict[str, Fraction]]:
        result, values = self.evaluate(output, environment)
        bars = [Fraction(0)] * len(self.nodes)
        bars[output] = Fraction(1)
        for idx in range(len(self.nodes) - 1, -1, -1):
            bar = bars[idx]
            if bar == 0:
                continue
            node = self.nodes[idx]
            if node.op == "add":
                left, right = node.args
                bars[left] += bar
                bars[right] += bar
            elif node.op == "mul":
                left, right = node.args
                bars[left] += bar * values[right]
                bars[right] += bar * values[left]
        gradient: dict[str, Fraction] = {}
        for idx, node in enumerate(self.nodes):
            if node.op == "var":
                assert node.name is not None
                gradient[node.name] = bars[idx]
        return result, gradient

    def metrics(self) -> dict[str, int]:
        counts = {"const": 0, "var": 0, "add": 0, "mul": 0}
        for node in self.nodes:
            counts[node.op] += 1
        return {
            "nodes": len(self.nodes),
            "operation_nodes": counts["add"] + counts["mul"],
            **{f"{name}_nodes": count for name, count in counts.items()},
        }


@dataclass(frozen=True)
class DeterminantCircuit:
    n: int
    circuit: ArithmeticCircuit
    output: int
    variables: tuple[tuple[int, ...], ...]
    transitions: int

    def environment(self, matrix: Sequence[Sequence[Scalar]]) -> dict[str, Fraction]:
        a = _square_q(matrix)
        if len(a) != self.n:
            raise ValueError(f"matrix must have shape {self.n}x{self.n}")
        return {f"a_{i}_{j}": a[i][j] for i in range(self.n) for j in range(self.n)}

    def determinant_and_adjugate(self, matrix: Sequence[Sequence[Scalar]]) -> dict:
        env = self.environment(matrix)
        determinant, gradient = self.circuit.reverse_gradient(self.output, env)
        cofactor = [[gradient[f"a_{i}_{j}"] for j in range(self.n)] for i in range(self.n)]
        return {
            "determinant": determinant,
            "cofactor_matrix": cofactor,
            "adjugate": transpose(cofactor),
            "circuit_metrics": self.circuit.metrics(),
            "transitions": self.transitions,
        }


def build_determinant_circuit(n: int, *, max_n: int = 12) -> DeterminantCircuit:
    """Build a division-free hash-consed subset circuit for the generic determinant."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    if n > max_n:
        raise ValueError(f"R0.2 subset circuit is exponential; n={n} exceeds max_n={max_n}")
    circuit = ArithmeticCircuit()
    variables = tuple(tuple(circuit.var(f"a_{i}_{j}") for j in range(n)) for i in range(n))
    dp: dict[int, int] = {0: circuit.one}
    transitions = 0
    for i in range(n):
        nxt: dict[int, int] = {}
        for mask, partial in dp.items():
            for j in range(n):
                bit = 1 << j
                if mask & bit:
                    continue
                term = circuit.mul(partial, variables[i][j])
                if (mask >> (j + 1)).bit_count() & 1:
                    term = circuit.neg(term)
                new_mask = mask | bit
                nxt[new_mask] = term if new_mask not in nxt else circuit.add(nxt[new_mask], term)
                transitions += 1
        dp = nxt
    output = dp[(1 << n) - 1] if n else circuit.one
    return DeterminantCircuit(n, circuit, output, variables, transitions)


def division_free_packet(matrix: Sequence[Sequence[Scalar]], *, max_n: int = 12) -> dict:
    a = _square_q(matrix)
    compiled = build_determinant_circuit(len(a), max_n=max_n)
    result = compiled.determinant_and_adjugate(a)
    bareiss = det_bareiss(a)
    direct_adj = cofactor_adjugate(a)
    r01 = determinant_adjugate_dag(a, max_n=max_n)
    n = len(a)
    explicit_leaf_baseline = math.factorial(n) + n * n * math.factorial(max(n - 1, 0))
    op_nodes = result["circuit_metrics"]["operation_nodes"]
    return {
        **result,
        "bareiss_crosscheck": bareiss,
        "bareiss_exact": result["determinant"] == bareiss,
        "cofactor_crosscheck_exact": result["adjugate"] == direct_adj,
        "r01_subset_crosscheck_exact": result["adjugate"] == [list(row) for row in r01.adjugate],
        "shared_metrics": {
            "explicit_leibniz_leaf_baseline": explicit_leaf_baseline,
            "circuit_operation_nodes": op_nodes,
            "symbolic_compression_ratio_vs_leaf_baseline": explicit_leaf_baseline / max(op_nodes, 1),
            "shared_computation_gain_vs_leaf_baseline": 1.0 - op_nodes / max(explicit_leaf_baseline, 1),
            "metric_boundary": "combinatorial baseline only; not a runtime-speedup claim",
        },
    }


def _poly_trim(poly: Sequence[Scalar]) -> list[Fraction]:
    out = [as_q(x) for x in poly]
    if not out:
        return [Fraction(0)]
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def _poly_zero(poly: Sequence[Scalar]) -> bool:
    return all(x == 0 for x in _poly_trim(poly))


def poly_add(left: Sequence[Scalar], right: Sequence[Scalar]) -> list[Fraction]:
    a, b = _poly_trim(left), _poly_trim(right)
    out = [Fraction(0)] * max(len(a), len(b))
    for i in range(len(out)):
        out[i] = (a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0)
    return _poly_trim(out)


def poly_mul(left: Sequence[Scalar], right: Sequence[Scalar]) -> list[Fraction]:
    a, b = _poly_trim(left), _poly_trim(right)
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return _poly_trim(out)


def poly_scale(poly: Sequence[Scalar], scalar: Scalar) -> list[Fraction]:
    q = as_q(scalar)
    return _poly_trim([q * x for x in _poly_trim(poly)])


def poly_eval(poly: Sequence[Scalar], x: Scalar) -> Fraction:
    q = as_q(x)
    out = Fraction(0)
    for coefficient in reversed(_poly_trim(poly)):
        out = out * q + coefficient
    return out


def poly_divmod(
    numerator: Sequence[Scalar],
    denominator: Sequence[Scalar],
) -> tuple[list[Fraction], list[Fraction]]:
    a = _poly_trim(numerator)
    b = _poly_trim(denominator)
    if _poly_zero(b):
        raise ZeroDivisionError("zero polynomial denominator")
    quotient = [Fraction(0)] * max(1, len(a) - len(b) + 1)
    remainder = a[:]
    while not _poly_zero(remainder) and len(remainder) >= len(b):
        degree = len(remainder) - len(b)
        scale = remainder[-1] / b[-1]
        quotient[degree] = scale
        for j, coefficient in enumerate(b):
            remainder[degree + j] -= scale * coefficient
        remainder = _poly_trim(remainder)
    return _poly_trim(quotient), _poly_trim(remainder)


def poly_gcd(left: Sequence[Scalar], right: Sequence[Scalar]) -> list[Fraction]:
    a, b = _poly_trim(left), _poly_trim(right)
    while not _poly_zero(b):
        _, remainder = poly_divmod(a, b)
        a, b = b, remainder
    if _poly_zero(a):
        return [Fraction(0)]
    lead = a[-1]
    return [x / lead for x in a]


@dataclass(frozen=True)
class DomainLedger:
    variable: str
    original_denominator: tuple[Fraction, ...]
    cancelled_factor: tuple[Fraction, ...]
    reduced_denominator: tuple[Fraction, ...]
    original_guard: str
    cancellation_preserved: bool = True


@dataclass(frozen=True)
class GuardedExpression:
    numerator: tuple[Fraction, ...]
    denominator: tuple[Fraction, ...]
    ledger: DomainLedger


def simplify_rational_polynomials(
    numerator: Sequence[Scalar],
    denominator: Sequence[Scalar],
    *,
    variable: str = "t",
) -> GuardedExpression:
    num, den = _poly_trim(numerator), _poly_trim(denominator)
    if _poly_zero(den):
        raise ZeroDivisionError("zero polynomial denominator")
    gcd = poly_gcd(num, den)
    red_num, rem_num = poly_divmod(num, gcd)
    red_den, rem_den = poly_divmod(den, gcd)
    if not _poly_zero(rem_num) or not _poly_zero(rem_den):  # pragma: no cover
        raise ArithmeticError("internal polynomial gcd division failed")
    ledger = DomainLedger(
        variable=variable,
        original_denominator=tuple(den),
        cancelled_factor=tuple(gcd),
        reduced_denominator=tuple(red_den),
        original_guard=f"original_denominator({variable}) != 0",
    )
    return GuardedExpression(tuple(red_num), tuple(red_den), ledger)


def interpolate_polynomial(xs: Sequence[Scalar], ys: Sequence[Scalar]) -> list[Fraction]:
    if len(xs) != len(ys) or not xs:
        raise ValueError("xs and ys must have equal nonzero length")
    xq, yq = [as_q(x) for x in xs], [as_q(y) for y in ys]
    if len(set(xq)) != len(xq):
        raise ValueError("interpolation abscissas must be distinct")
    out = [Fraction(0)]
    for i, xi in enumerate(xq):
        basis = [Fraction(1)]
        denom = Fraction(1)
        for j, xj in enumerate(xq):
            if i == j:
                continue
            basis = poly_mul(basis, [-xj, 1])
            denom *= xi - xj
        out = poly_add(out, poly_scale(basis, yq[i] / denom))
    return _poly_trim(out)


@dataclass(frozen=True)
class DirectionalDeterminantalJet:
    coefficients: tuple[Fraction, ...]
    derivatives_at_zero: tuple[Fraction, ...]
    validation_residual: Fraction


def directional_determinantal_jet(
    matrix: Sequence[Sequence[Scalar]],
    direction: Sequence[Sequence[Scalar]],
) -> DirectionalDeterminantalJet:
    """Exact coefficients of det(A+tH), recovered from n+1 exact evaluations."""
    a = _square_q(matrix)
    h = _square_q(direction)
    n = len(a)
    if len(h) != n:
        raise ValueError("direction must have the same shape as matrix")

    def shifted(t: Scalar) -> list[list[Fraction]]:
        q = as_q(t)
        return [[a[i][j] + q * h[i][j] for j in range(n)] for i in range(n)]

    xs = list(range(n + 1))
    ys = [det_bareiss(shifted(t)) for t in xs]
    coefficients = interpolate_polynomial(xs, ys)
    coefficients += [Fraction(0)] * (n + 1 - len(coefficients))
    derivatives = [coefficients[k] * math.factorial(k) for k in range(n + 1)]
    probe = Fraction(n + 2)
    residual = poly_eval(coefficients, probe) - det_bareiss(shifted(probe))
    return DirectionalDeterminantalJet(tuple(coefficients), tuple(derivatives), residual)


def _complement(n: int, subset: Sequence[int]) -> tuple[int, ...]:
    selected = set(subset)
    return tuple(i for i in range(n) if i not in selected)


def _submatrix(
    matrix: Sequence[Sequence[Scalar]],
    rows: Sequence[int],
    cols: Sequence[int],
) -> list[list[Fraction]]:
    a = _matrix_q(matrix)
    return [[a[i][j] for j in cols] for i in rows]


def generalized_cofactors(matrix: Sequence[Sequence[Scalar]], order: int) -> dict:
    """Open ``order`` row/column indices; entries are signed complementary minors."""
    a = _square_q(matrix)
    n = len(a)
    if not 0 <= order <= n:
        raise ValueError("order must lie in [0,n]")
    index_sets = list(combinations(range(n), order))
    values: list[list[Fraction]] = []
    for rows_open in index_sets:
        row_out: list[Fraction] = []
        rows_closed = _complement(n, rows_open)
        for cols_open in index_sets:
            cols_closed = _complement(n, cols_open)
            sign = Fraction(-1 if (sum(rows_open) + sum(cols_open)) & 1 else 1)
            row_out.append(sign * det_bareiss(_submatrix(a, rows_closed, cols_closed)))
        values.append(row_out)
    return {
        "order": order,
        "open_row_sets": index_sets,
        "open_col_sets": index_sets,
        "values": values,
    }


def singularity_ladder(matrix: Sequence[Sequence[Scalar]]) -> dict:
    a = _square_q(matrix)
    n = len(a)
    rank = matrix_rank(a)
    nullity = n - rank
    first_nonzero_order = None
    witness = None
    for order in range(n + 1):
        tensor = generalized_cofactors(a, order)
        for i, row in enumerate(tensor["values"]):
            for j, value in enumerate(row):
                if value != 0:
                    first_nonzero_order = order
                    witness = {
                        "open_rows": tensor["open_row_sets"][i],
                        "open_cols": tensor["open_col_sets"][j],
                        "value": value,
                    }
                    break
            if witness is not None:
                break
        if witness is not None:
            break
    return {
        "n": n,
        "rank": rank,
        "nullity": nullity,
        "first_nonzero_higher_cofactor_order": first_nonzero_order,
        "expected_order_from_rank": nullity,
        "rank_order_identity_exact": first_nonzero_order == nullity,
        "witness": witness,
        "adjugate_nonzero": (
            any(value != 0 for row in generalized_cofactors(a, 1)["values"] for value in row)
            if n >= 1 else False
        ),
    }


def structural_profile(matrix: Sequence[Sequence[Scalar]]) -> dict:
    a = _matrix_q(matrix)
    rows = len(a)
    cols = len(a[0]) if a else 0
    nnz = sum(value != 0 for row in a for value in row)
    density = nnz / (rows * cols) if rows and cols else 0.0
    square = rows == cols
    diagonal = square and all(a[i][j] == 0 for i in range(rows) for j in range(cols) if i != j)
    upper = square and all(a[i][j] == 0 for i in range(rows) for j in range(i))
    lower = square and all(a[i][j] == 0 for i in range(rows) for j in range(i + 1, cols))
    symmetric = square and all(a[i][j] == a[j][i] for i in range(rows) for j in range(cols))
    zero_rows = [i for i, row in enumerate(a) if all(value == 0 for value in row)]
    zero_cols = [j for j in range(cols) if all(a[i][j] == 0 for i in range(rows))]

    adjacency: dict[tuple[str, int], list[tuple[str, int]]] = {
        **{("r", i): [] for i in range(rows)},
        **{("c", j): [] for j in range(cols)},
    }
    for i in range(rows):
        for j in range(cols):
            if a[i][j] != 0:
                adjacency[("r", i)].append(("c", j))
                adjacency[("c", j)].append(("r", i))

    seen: set[tuple[str, int]] = set()
    components: list[dict[str, tuple[int, ...]]] = []
    for vertex in adjacency:
        if vertex in seen:
            continue
        stack = [vertex]
        seen.add(vertex)
        rs: list[int] = []
        cs: list[int] = []
        while stack:
            current = stack.pop()
            (rs if current[0] == "r" else cs).append(current[1])
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append({"rows": tuple(sorted(rs)), "cols": tuple(sorted(cs))})

    match_col: dict[int, int] = {}

    def augment(row: int, visited: set[int]) -> bool:
        for col in range(cols):
            if a[row][col] == 0 or col in visited:
                continue
            visited.add(col)
            if col not in match_col or augment(match_col[col], visited):
                match_col[col] = row
                return True
        return False

    structural_rank = sum(1 for row in range(rows) if augment(row, set()))
    exact_rank = matrix_rank(a)
    balanced_blocks = [
        comp for comp in components if comp["rows"] and len(comp["rows"]) == len(comp["cols"])
    ]
    return {
        "rows": rows,
        "cols": cols,
        "nnz": nnz,
        "density": density,
        "square": square,
        "diagonal": diagonal,
        "upper_triangular": upper,
        "lower_triangular": lower,
        "symmetric": symmetric,
        "zero_rows": zero_rows,
        "zero_cols": zero_cols,
        "structural_rank": structural_rank,
        "exact_rank": exact_rank,
        "connected_components": components,
        "balanced_nonzero_blocks": balanced_blocks,
    }


def route_backend(matrix: Sequence[Sequence[Scalar]]) -> dict:
    profile = structural_profile(matrix)
    rows, cols = profile["rows"], profile["cols"]
    if rows != cols:
        backend = "rectangular-compound-rank"
        reason = "ordinary determinant is not the primary invariant for a rectangular matrix"
    elif profile["exact_rank"] < rows:
        backend = "singularity-ladder"
        reason = "exact rank deficiency detected; avoid Cramer division"
    elif profile["diagonal"]:
        backend = "diagonal-closed-form"
        reason = "determinant and solve factor entrywise"
    elif profile["upper_triangular"] or profile["lower_triangular"]:
        backend = "triangular-closed-form"
        reason = "determinant is product of diagonal entries"
    elif len(profile["balanced_nonzero_blocks"]) > 1:
        backend = "block-decomposition"
        reason = "bipartite support graph splits into balanced components"
    elif rows <= 7:
        backend = "subset-circuit-reverse-ad"
        reason = "small exact system fits the transparent shared-circuit backend"
    elif profile["density"] <= 0.20:
        backend = "sparse-fraction-free-candidate"
        reason = "low density favors sparse structure exploitation before expansion"
    else:
        backend = "bareiss-or-berkowitz-candidate"
        reason = "larger dense exact system should prefer polynomial-time elimination/circuit backends"
    return {
        "backend": backend,
        "reason": reason,
        "profile": profile,
        "oak": "heuristic router; performance choice requires family-specific benchmarks",
    }


def deterministic_benchmark_atlas() -> dict:
    families = {
        "dense3": [[2, 1, 3], [1, 4, 2], [5, 0, 1]],
        "diagonal6": [[(i + 2) if i == j else 0 for j in range(6)] for i in range(6)],
        "block6": [
            [2, 1, 0, 0, 0, 0],
            [1, 3, 0, 0, 0, 0],
            [0, 0, 2, 1, 0, 0],
            [0, 0, 1, 4, 0, 0],
            [0, 0, 0, 0, 3, 1],
            [0, 0, 0, 0, 1, 5],
        ],
        "rank_deficient4": [[1, 2, 0, 0], [2, 4, 0, 0], [0, 0, 1, 1], [0, 0, 2, 2]],
        "vandermonde5": [[Fraction(i) ** j for j in range(5)] for i in range(1, 6)],
    }
    out = {}
    for name, matrix in families.items():
        route = route_backend(matrix)
        n = len(matrix)
        circuit = build_determinant_circuit(n, max_n=8)
        det_value, _ = circuit.circuit.evaluate(circuit.output, circuit.environment(matrix))
        out[name] = {
            "n": n,
            "determinant": det_value,
            "route": route["backend"],
            "density": route["profile"]["density"],
            "exact_rank": route["profile"]["exact_rank"],
            "circuit_metrics": circuit.circuit.metrics(),
            "transitions": circuit.transitions,
        }
    return {
        "families": out,
        "timing_claimed": False,
        "purpose": "deterministic structural/circuit baseline before empirical timing campaigns",
    }


def _jsonify(value):
    if isinstance(value, Fraction):
        return qstr(value)
    if isinstance(value, (DomainLedger, GuardedExpression, DirectionalDeterminantalJet)):
        return _jsonify(asdict(value))
    if isinstance(value, tuple):
        return [_jsonify(x) for x in value]
    if isinstance(value, list):
        return [_jsonify(x) for x in value]
    if isinstance(value, dict):
        return {key: _jsonify(item) for key, item in value.items()}
    return value


def demo_packet() -> dict:
    matrix = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
    direction = [[1, 0, 1], [0, -1, 0], [1, 0, 2]]
    singular = [[1, 2, 3], [2, 4, 6], [0, 1, 1]]
    simplified = simplify_rational_polynomials([-2, 1, 1], [-3, 2, 1])
    return {
        "division_free": division_free_packet(matrix),
        "directional_jet": directional_determinantal_jet(matrix, direction),
        "higher_cofactor_order_2": generalized_cofactors(matrix, 2),
        "singularity_ladder": singularity_ladder(singular),
        "guarded_simplification": simplified,
        "route": route_backend(matrix),
        "benchmark_atlas": deterministic_benchmark_atlas(),
        "oak": {
            "status": "D-MVP candidate",
            "theorem_claimed": False,
            "universal_speed_claimed": False,
            "division_free_circuit_is_polynomial_time_claimed": False,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ω-KRAMER-TRISTAN R0.2 circuit/jet/structure compiler")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="emit the deterministic R0.2 evidence packet")
    sub.add_parser("benchmark", help="emit deterministic structural benchmark atlas")
    args = parser.parse_args(argv)
    if args.command in (None, "demo"):
        payload = demo_packet()
    elif args.command == "benchmark":
        payload = deterministic_benchmark_atlas()
    else:  # pragma: no cover
        parser.error("unknown command")
        return 2
    print(json.dumps(_jsonify(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
