#!/usr/bin/env python3
"""Ω-DET-ADJ-KRAMER-COMPILER-T∞ R0.1.

Exact, stdlib-only research prototype for a shared determinant DAG,
reverse-mode adjugate extraction, bordered Kramer generators, exact
certificates, singular-system classification, multiple right-hand sides,
and compound-matrix probes.

OAK boundary
------------
Established identities are used as identities, not claimed as new:
* d det(A) / d a_ij = cofactor_ij(A)
* A adj(A) = det(A) I
* det([[A,b],[z^T,alpha]]) = alpha det(A) - z^T adj(A) b
* Cramer's rule when det(A) != 0
* k-minors are entries of compound/exterior-power representations

The Tristan contribution in this prototype is architectural: compile the
Leibniz assignment space into a subset-DAG, run reverse AD on the same DAG,
reuse the resulting adjugate across solves, keep exact certificates, and
expose cost metrics. No superiority claim is made without benchmarks.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Sequence


Scalar = int | float | str | Fraction


def as_q(value: Scalar) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(str(value))
    return Fraction(value)


def qstr(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _matrix_q(matrix: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    rows = [[as_q(x) for x in row] for row in matrix]
    if rows and any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("matrix rows must have equal length")
    return rows


def _square_q(matrix: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    rows = _matrix_q(matrix)
    if any(len(row) != len(rows) for row in rows):
        raise ValueError("matrix must be square")
    return rows


def _vector_q(vector: Sequence[Scalar], n: int | None = None) -> list[Fraction]:
    out = [as_q(x) for x in vector]
    if n is not None and len(out) != n:
        raise ValueError(f"vector length must be {n}")
    return out


def identity(n: int) -> list[list[Fraction]]:
    return [[Fraction(i == j) for j in range(n)] for i in range(n)]


def transpose(matrix: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    rows = _matrix_q(matrix)
    if not rows:
        return []
    return [[rows[i][j] for i in range(len(rows))] for j in range(len(rows[0]))]


def matvec(matrix: Sequence[Sequence[Scalar]], vector: Sequence[Scalar]) -> list[Fraction]:
    rows = _matrix_q(matrix)
    if not rows:
        return []
    v = _vector_q(vector, len(rows[0]))
    return [sum((row[j] * v[j] for j in range(len(v))), Fraction(0)) for row in rows]


def matmul(left: Sequence[Sequence[Scalar]], right: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    a = _matrix_q(left)
    b = _matrix_q(right)
    if not a or not b:
        return []
    if len(a[0]) != len(b):
        raise ValueError("incompatible matrix dimensions")
    bt = transpose(b)
    return [
        [sum((x * y for x, y in zip(row, col)), Fraction(0)) for col in bt]
        for row in a
    ]


def det_bareiss(matrix: Sequence[Sequence[Scalar]]) -> Fraction:
    """Exact Bareiss determinant over rational inputs."""
    a = _square_q(matrix)
    n = len(a)
    if n == 0:
        return Fraction(1)
    if n == 1:
        return a[0][0]

    sign = Fraction(1)
    previous_pivot = Fraction(1)

    for k in range(n - 1):
        pivot_row = next((r for r in range(k, n) if a[r][k] != 0), None)
        if pivot_row is None:
            return Fraction(0)
        if pivot_row != k:
            a[k], a[pivot_row] = a[pivot_row], a[k]
            sign = -sign

        pivot = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * pivot - a[i][k] * a[k][j]) / previous_pivot
            a[i][k] = Fraction(0)
        previous_pivot = pivot

    return sign * a[n - 1][n - 1]


def minor_matrix(matrix: Sequence[Sequence[Scalar]], row: int, col: int) -> list[list[Fraction]]:
    a = _square_q(matrix)
    return [[a[i][j] for j in range(len(a)) if j != col] for i in range(len(a)) if i != row]


def cofactor_adjugate(matrix: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    """Independent cofactor oracle used for validation, not the fast path."""
    a = _square_q(matrix)
    n = len(a)
    if n == 0:
        return []
    cof = [
        [
            (Fraction(-1) if (i + j) % 2 else Fraction(1)) * det_bareiss(minor_matrix(a, i, j))
            for j in range(n)
        ]
        for i in range(n)
    ]
    return transpose(cof)


@dataclass(frozen=True)
class DAGMetrics:
    n: int
    stored_states: int
    transitions: int
    leibniz_terms: int

    @property
    def term_to_transition_ratio(self) -> float:
        if self.transitions == 0:
            return 1.0
        return self.leibniz_terms / self.transitions


@dataclass(frozen=True)
class DeterminantDAGResult:
    determinant: Fraction
    gradient: tuple[tuple[Fraction, ...], ...]
    adjugate: tuple[tuple[Fraction, ...], ...]
    metrics: DAGMetrics


def determinant_adjugate_dag(
    matrix: Sequence[Sequence[Scalar]],
    *,
    max_n: int = 16,
) -> DeterminantDAGResult:
    """Compile det(A) into a subset DAG and reverse-AD it.

    Forward state:
        dp_i[mask] = signed sum of assignments of rows 0..i-1
        to the columns selected in ``mask``.

    A transition that appends column j contributes the inversion parity
    created against previously selected columns. This compresses n! explicit
    permutation leaves into 2^n subset states and n*2^(n-1) transitions.

    Reverse mode differentiates the same DAG. The gradient w.r.t. A is the
    cofactor matrix; transposing it gives adj(A).
    """
    a = _square_q(matrix)
    n = len(a)
    if n > max_n:
        raise ValueError(
            f"subset determinant DAG is exponential; n={n} exceeds max_n={max_n}. "
            "Use a polynomial-time numeric/symbolic backend for larger dense systems."
        )
    if n == 0:
        return DeterminantDAGResult(
            determinant=Fraction(1),
            gradient=tuple(),
            adjugate=tuple(),
            metrics=DAGMetrics(0, 1, 0, 1),
        )

    layers: list[dict[int, Fraction]] = [{0: Fraction(1)}]
    transitions = 0

    for i in range(n):
        current = layers[-1]
        nxt: dict[int, Fraction] = {}
        for mask, value in current.items():
            for j in range(n):
                bit = 1 << j
                if mask & bit:
                    continue
                inversions_added = (mask >> (j + 1)).bit_count()
                sign = Fraction(-1 if inversions_added & 1 else 1)
                new_mask = mask | bit
                nxt[new_mask] = nxt.get(new_mask, Fraction(0)) + value * sign * a[i][j]
                transitions += 1
        layers.append(nxt)

    full = (1 << n) - 1
    determinant = layers[n].get(full, Fraction(0))

    bars: list[dict[int, Fraction]] = [dict() for _ in range(n + 1)]
    bars[n][full] = Fraction(1)
    gradient = [[Fraction(0) for _ in range(n)] for _ in range(n)]

    for i in range(n - 1, -1, -1):
        current = layers[i]
        current_bars = bars[i]
        next_bars = bars[i + 1]
        for mask, value in current.items():
            accumulated = Fraction(0)
            for j in range(n):
                bit = 1 << j
                if mask & bit:
                    continue
                new_mask = mask | bit
                bar = next_bars.get(new_mask, Fraction(0))
                if bar == 0:
                    continue
                inversions_added = (mask >> (j + 1)).bit_count()
                sign = Fraction(-1 if inversions_added & 1 else 1)
                weight = sign * a[i][j]
                accumulated += bar * weight
                gradient[i][j] += bar * value * sign
            if accumulated:
                current_bars[mask] = current_bars.get(mask, Fraction(0)) + accumulated

    adjugate = transpose(gradient)
    metrics = DAGMetrics(
        n=n,
        stored_states=sum(len(layer) for layer in layers),
        transitions=transitions,
        leibniz_terms=math.factorial(n),
    )
    return DeterminantDAGResult(
        determinant=determinant,
        gradient=tuple(tuple(row) for row in gradient),
        adjugate=tuple(tuple(row) for row in adjugate),
        metrics=metrics,
    )


def matrix_rank(matrix: Sequence[Sequence[Scalar]]) -> int:
    a = _matrix_q(matrix)
    if not a:
        return 0
    rows, cols = len(a), len(a[0])
    rank = 0
    for col in range(cols):
        pivot = next((r for r in range(rank, rows) if a[r][col] != 0), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        p = a[rank][col]
        a[rank] = [x / p for x in a[rank]]
        for r in range(rows):
            if r != rank and a[r][col] != 0:
                factor = a[r][col]
                a[r] = [a[r][c] - factor * a[rank][c] for c in range(cols)]
        rank += 1
        if rank == rows:
            break
    return rank


def gaussian_solve(matrix: Sequence[Sequence[Scalar]], rhs: Sequence[Scalar]) -> list[Fraction]:
    a = _square_q(matrix)
    n = len(a)
    b = _vector_q(rhs, n)
    rows = [a[i] + [b[i]] for i in range(n)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if rows[r][col] != 0), None)
        if pivot is None:
            raise ValueError("system does not have a unique solution")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        p = rows[col][col]
        rows[col] = [x / p for x in rows[col]]
        for r in range(n):
            if r != col and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [rows[r][c] - factor * rows[col][c] for c in range(n + 1)]
    return [rows[i][-1] for i in range(n)]


def _augment(matrix: Sequence[Sequence[Scalar]], rhs: Sequence[Scalar]) -> list[list[Fraction]]:
    a = _square_q(matrix)
    b = _vector_q(rhs, len(a))
    return [row + [b[i]] for i, row in enumerate(a)]


def classify_system(matrix: Sequence[Sequence[Scalar]], rhs: Sequence[Scalar]) -> dict[str, int | str]:
    a = _square_q(matrix)
    rank_a = matrix_rank(a)
    rank_aug = matrix_rank(_augment(a, rhs))
    n = len(a)
    if rank_a < rank_aug:
        kind = "inconsistent"
    elif rank_a < n:
        kind = "infinitely_many"
    else:
        kind = "unique"
    return {"classification": kind, "rank_a": rank_a, "rank_augmented": rank_aug}


def kramer_packet(
    matrix: Sequence[Sequence[Scalar]],
    rhs: Sequence[Scalar],
    *,
    max_n: int = 16,
) -> dict:
    a = _square_q(matrix)
    n = len(a)
    b = _vector_q(rhs, n)
    dag = determinant_adjugate_dag(a, max_n=max_n)
    adj = [list(row) for row in dag.adjugate]
    numerator = matvec(adj, b)
    d = dag.determinant
    lhs = matvec(a, numerator)
    db = [d * x for x in b]
    certificate = [lhs[i] - db[i] for i in range(n)]
    classification = classify_system(a, b)

    solution = None if d == 0 else [x / d for x in numerator]
    gaussian_crosscheck = None
    if d != 0:
        gaussian_crosscheck = gaussian_solve(a, b)

    return {
        "determinant": d,
        "numerator": numerator,
        "solution": solution,
        "adjugate": adj,
        "certificate": certificate,
        "certificate_exact": all(x == 0 for x in certificate),
        "classification": classification,
        "gaussian_crosscheck": gaussian_crosscheck,
        "crosscheck_exact": solution == gaussian_crosscheck if solution is not None else None,
        "domain_ledger": {
            "original_condition_for_cramer_division": "det(A) != 0",
            "division_performed": d != 0,
            "singularity_preserved": True,
        },
        "dag_metrics": dag.metrics,
        "oak": {
            "status": "D-MVP candidate",
            "theorem_claimed": False,
            "performance_superiority_claimed": False,
            "notes": [
                "subset-DAG backend is exponential and intended for exact small/medium structured experiments",
                "Bareiss/Gaussian and cofactor paths are independent validation oracles",
            ],
        },
    }


def bordered_generator_value(
    matrix: Sequence[Sequence[Scalar]],
    rhs: Sequence[Scalar],
    z: Sequence[Scalar],
    alpha: Scalar,
) -> Fraction:
    a = _square_q(matrix)
    n = len(a)
    b = _vector_q(rhs, n)
    zz = _vector_q(z, n)
    bordered = [a[i] + [b[i]] for i in range(n)]
    bordered.append(zz + [as_q(alpha)])
    return det_bareiss(bordered)


def bordered_identity_residual(
    matrix: Sequence[Sequence[Scalar]],
    rhs: Sequence[Scalar],
    z: Sequence[Scalar],
    alpha: Scalar,
    *,
    max_n: int = 16,
) -> Fraction:
    packet = kramer_packet(matrix, rhs, max_n=max_n)
    zz = _vector_q(z, len(packet["numerator"]))
    expected = as_q(alpha) * packet["determinant"] - sum(
        (zz[i] * packet["numerator"][i] for i in range(len(zz))),
        Fraction(0),
    )
    return bordered_generator_value(matrix, rhs, zz, alpha) - expected


def multi_rhs_packet(
    matrix: Sequence[Sequence[Scalar]],
    rhs_matrix: Sequence[Sequence[Scalar]],
    *,
    max_n: int = 16,
) -> dict:
    a = _square_q(matrix)
    b = _matrix_q(rhs_matrix)
    n = len(a)
    if len(b) != n:
        raise ValueError(f"rhs matrix must have {n} rows")
    m = len(b[0]) if b else 0
    if any(len(row) != m for row in b):
        raise ValueError("rhs matrix rows must have equal length")

    dag = determinant_adjugate_dag(a, max_n=max_n)
    adj = [list(row) for row in dag.adjugate]
    numerators = matmul(adj, b) if b else [[] for _ in range(n)]
    solutions = None
    if dag.determinant != 0:
        solutions = [[x / dag.determinant for x in row] for row in numerators]
    certificate = matmul(a, numerators) if b else [[] for _ in range(n)]
    target = [[dag.determinant * b[i][j] for j in range(m)] for i in range(n)]
    residual = [
        [certificate[i][j] - target[i][j] for j in range(m)]
        for i in range(n)
    ]
    return {
        "determinant": dag.determinant,
        "numerators": numerators,
        "solutions": solutions,
        "certificate": residual,
        "certificate_exact": all(x == 0 for row in residual for x in row),
        "dag_metrics": dag.metrics,
    }


def compound_matrix(matrix: Sequence[Sequence[Scalar]], k: int) -> dict:
    """Return the k-th compound matrix (all k x k minors)."""
    a = _matrix_q(matrix)
    rows = len(a)
    cols = len(a[0]) if a else 0
    if not 0 <= k <= min(rows, cols):
        raise ValueError("k must lie between 0 and min(rows, cols)")
    row_sets = list(combinations(range(rows), k))
    col_sets = list(combinations(range(cols), k))
    if k == 0:
        values = [[Fraction(1)]]
    else:
        values = []
        for rs in row_sets:
            out_row = []
            for cs in col_sets:
                sub = [[a[i][j] for j in cs] for i in rs]
                out_row.append(det_bareiss(sub))
            values.append(out_row)
    return {"k": k, "row_sets": row_sets, "col_sets": col_sets, "values": values}


def _jsonify(value):
    if isinstance(value, Fraction):
        return qstr(value)
    if isinstance(value, DAGMetrics):
        return {
            "n": value.n,
            "stored_states": value.stored_states,
            "transitions": value.transitions,
            "leibniz_terms": value.leibniz_terms,
            "term_to_transition_ratio": value.term_to_transition_ratio,
        }
    if isinstance(value, tuple):
        return [_jsonify(x) for x in value]
    if isinstance(value, list):
        return [_jsonify(x) for x in value]
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    return value


def _parse_json_matrix(text: str) -> list[list[Scalar]]:
    value = json.loads(text)
    if not isinstance(value, list) or any(not isinstance(row, list) for row in value):
        raise ValueError("matrix must be a JSON list of rows")
    return value


def _parse_json_vector(text: str) -> list[Scalar]:
    value = json.loads(text)
    if not isinstance(value, list) or any(isinstance(x, list) for x in value):
        raise ValueError("vector must be a flat JSON list")
    return value


def demo_packet() -> dict:
    a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
    b = [1, 2, 3]
    packet = kramer_packet(a, b)
    packet["bordered_probe_residual"] = bordered_identity_residual(a, b, [2, -1, 3], 5)
    packet["compound_2"] = compound_matrix(a, 2)
    return packet


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ω-KRAMER-TRISTAN R0.1 exact determinant/adjugate compiler")
    sub = parser.add_subparsers(dest="command", required=False)

    solve = sub.add_parser("solve", help="solve Ax=b and emit an exact OAK packet")
    solve.add_argument("--matrix", required=True, help='JSON matrix, e.g. "[[2,1],[1,3]]"')
    solve.add_argument("--rhs", required=True, help='JSON vector, e.g. "[1,2]"')

    sub.add_parser("demo", help="emit a deterministic exact demonstration packet")

    args = parser.parse_args(argv)
    if args.command in (None, "demo"):
        payload = demo_packet()
    elif args.command == "solve":
        payload = kramer_packet(_parse_json_matrix(args.matrix), _parse_json_vector(args.rhs))
    else:
        parser.error("unknown command")
        return 2

    print(json.dumps(_jsonify(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
