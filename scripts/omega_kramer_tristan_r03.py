#!/usr/bin/env python3
"""Omega-KRAMER-TRISTAN R0.3 — polynomial circuit, mixed jet and rewrite compiler.

R0.3 extends R0.1/R0.2 with:
- a Berkowitz-style polynomial-time, division-free characteristic-polynomial circuit;
- reverse AD of the determinant output -> cofactor gradient / adjugate;
- exact multilinear determinantal derivatives by polarization of directional jets;
- a normalized mixed-discriminant probe;
- higher-adjugate / complementary-compound duality audits;
- proof-carrying rank-one, Sylvester, Kronecker and guarded Schur rewrites;
- an exact characteristic-polynomial bridge for Omega-ROOTFLOW-T∞;
- a deterministic circuit-complexity atlas comparing subset and Berkowitz backends.

OAK boundary
------------
All determinant, adjugate, Berkowitz, polarization, mixed-discriminant,
Sylvester, Kronecker, Schur and compound identities used here are established
mathematics. The Tristan contribution is the integrated compiler architecture,
cross-representation audit surface, domain/guard preservation and routing
workflow. Operation-node counts are representation metrics, not wall-clock
speed claims.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Sequence

try:
    from scripts.omega_kramer_tristan import (
        Scalar,
        _matrix_q,
        _square_q,
        as_q,
        cofactor_adjugate,
        compound_matrix,
        det_bareiss,
        gaussian_solve,
        matrix_rank,
        qstr,
        transpose,
    )
    from scripts.omega_kramer_tristan_r02 import (
        ArithmeticCircuit,
        build_determinant_circuit,
        directional_determinantal_jet,
        generalized_cofactors,
        singularity_ladder,
        structural_profile,
    )
except ModuleNotFoundError:
    from omega_kramer_tristan import (  # type: ignore
        Scalar,
        _matrix_q,
        _square_q,
        as_q,
        cofactor_adjugate,
        compound_matrix,
        det_bareiss,
        gaussian_solve,
        matrix_rank,
        qstr,
        transpose,
    )
    from omega_kramer_tristan_r02 import (  # type: ignore
        ArithmeticCircuit,
        build_determinant_circuit,
        directional_determinantal_jet,
        generalized_cofactors,
        singularity_ladder,
        structural_profile,
    )


def _circuit_sum(circuit: ArithmeticCircuit, nodes: Sequence[int]) -> int:
    out = circuit.zero
    for node in nodes:
        out = circuit.add(out, node)
    return out


def _circuit_dot(circuit: ArithmeticCircuit, left: Sequence[int], right: Sequence[int]) -> int:
    return _circuit_sum(circuit, [circuit.mul(a, b) for a, b in zip(left, right)])


@dataclass(frozen=True)
class BerkowitzCircuit:
    n: int
    circuit: ArithmeticCircuit
    characteristic_coefficients: tuple[int, ...]
    determinant_output: int
    variables: tuple[tuple[int, ...], ...]

    def environment(self, matrix: Sequence[Sequence[Scalar]]) -> dict[str, Fraction]:
        a = _square_q(matrix)
        if len(a) != self.n:
            raise ValueError(f"matrix must have shape {self.n}x{self.n}")
        return {f"a_{i}_{j}": a[i][j] for i in range(self.n) for j in range(self.n)}

    def evaluate(self, matrix: Sequence[Sequence[Scalar]]) -> dict:
        env = self.environment(matrix)
        characteristic = tuple(
            self.circuit.evaluate(node, env)[0] for node in self.characteristic_coefficients
        )
        determinant, gradient = self.circuit.reverse_gradient(self.determinant_output, env)
        cofactor = [
            [gradient[f"a_{i}_{j}"] for j in range(self.n)]
            for i in range(self.n)
        ]
        return {
            "characteristic_coefficients_descending": characteristic,
            "rootflow_coefficients_ascending": tuple(reversed(characteristic)),
            "determinant": determinant,
            "cofactor_matrix": cofactor,
            "adjugate": transpose(cofactor),
            "circuit_metrics": self.circuit.metrics(),
        }


def build_berkowitz_circuit(n: int, *, max_n: int = 24) -> BerkowitzCircuit:
    """Build a generic division-free Berkowitz-style characteristic circuit.

    Coefficients are stored as [1,c1,...,cn] for
        det(lambda I-A)=lambda^n+c1 lambda^(n-1)+...+cn.

    The recursive Toeplitz transform uses only + and * circuit nodes. With the
    straightforward matrix-vector implementation below the construction is
    polynomial (bounded by O(n^4) arithmetic work), unlike the R0.1/R0.2
    subset backend's exponential state growth.
    """
    if n < 0:
        raise ValueError("n must be nonnegative")
    if n > max_n:
        raise ValueError(f"n={n} exceeds conservative R0.3 build bound max_n={max_n}")

    circuit = ArithmeticCircuit()
    variables = tuple(
        tuple(circuit.var(f"a_{i}_{j}") for j in range(n)) for i in range(n)
    )

    def recurse(matrix_nodes: list[list[int]]) -> list[int]:
        m = len(matrix_nodes)
        if m == 0:
            return [circuit.one]
        a00 = matrix_nodes[0][0]
        if m == 1:
            return [circuit.one, circuit.neg(a00)]

        trailing = [row[1:] for row in matrix_nodes[1:]]
        row = matrix_nodes[0][1:]
        column = [r[0] for r in matrix_nodes[1:]]
        old = recurse(trailing)

        # moments s_p = R M^(p-1) C, p=1,...,m-1
        vector = column[:]
        moments: list[int] = []
        for p in range(1, m):
            moments.append(_circuit_dot(circuit, row, vector))
            if p < m - 1:
                vector = [
                    _circuit_dot(circuit, trailing[i], vector)
                    for i in range(m - 1)
                ]

        # Lower-Toeplitz Berkowitz transform.
        weights: list[int | None] = [None, circuit.neg(a00)]
        weights.extend(circuit.neg(value) for value in moments)
        new: list[int] = []
        for i in range(m + 1):
            terms: list[int] = []
            for j in range(min(i, m - 1) + 1):
                difference = i - j
                weight = circuit.one if difference == 0 else weights[difference]
                assert weight is not None
                terms.append(circuit.mul(weight, old[j]))
            new.append(_circuit_sum(circuit, terms))
        return new

    characteristic = tuple(recurse([list(row) for row in variables]))
    constant_term = characteristic[-1]
    determinant_output = constant_term if n % 2 == 0 else circuit.neg(constant_term)
    return BerkowitzCircuit(n, circuit, characteristic, determinant_output, variables)


def _identity(n: int) -> list[list[Fraction]]:
    return [[Fraction(i == j) for j in range(n)] for i in range(n)]


def _matmul(left: Sequence[Sequence[Scalar]], right: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    a, b = _matrix_q(left), _matrix_q(right)
    if not a or not b:
        return []
    if len(a[0]) != len(b):
        raise ValueError("incompatible matrix dimensions")
    return [
        [sum((a[i][k] * b[k][j] for k in range(len(b))), Fraction(0)) for j in range(len(b[0]))]
        for i in range(len(a))
    ]


def _matadd(left: Sequence[Sequence[Scalar]], right: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    a, b = _matrix_q(left), _matrix_q(right)
    if len(a) != len(b) or (a and len(a[0]) != len(b[0])):
        raise ValueError("matrix shapes must agree")
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _matsub(left: Sequence[Sequence[Scalar]], right: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    a, b = _matrix_q(left), _matrix_q(right)
    if len(a) != len(b) or (a and len(a[0]) != len(b[0])):
        raise ValueError("matrix shapes must agree")
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _zero_matrix(n: int) -> list[list[Fraction]]:
    return [[Fraction(0) for _ in range(n)] for _ in range(n)]


def _direction_sum(directions: Sequence[Sequence[Sequence[Scalar]]], mask: int, n: int) -> list[list[Fraction]]:
    out = _zero_matrix(n)
    for r, direction in enumerate(directions):
        if mask & (1 << r):
            out = _matadd(out, direction)
    return out


def _poly_eval_descending(coefficients: Sequence[Scalar], x: Scalar) -> Fraction:
    q = as_q(x)
    out = Fraction(0)
    for coefficient in coefficients:
        out = out * q + as_q(coefficient)
    return out


def berkowitz_packet(matrix: Sequence[Sequence[Scalar]], *, max_n: int = 24) -> dict:
    a = _square_q(matrix)
    compiled = build_berkowitz_circuit(len(a), max_n=max_n)
    result = compiled.evaluate(a)
    bareiss = det_bareiss(a)
    direct_adj = cofactor_adjugate(a)
    probes = {}
    for lam in (-2, -1, 0, 1, 2):
        shifted = [
            [Fraction(lam if i == j else 0) - a[i][j] for j in range(len(a))]
            for i in range(len(a))
        ]
        polynomial_value = _poly_eval_descending(
            result["characteristic_coefficients_descending"], lam
        )
        direct = det_bareiss(shifted)
        probes[str(lam)] = {
            "polynomial": polynomial_value,
            "direct": direct,
            "residual": polynomial_value - direct,
        }
    return {
        **result,
        "bareiss_crosscheck": bareiss,
        "determinant_exact": result["determinant"] == bareiss,
        "adjugate_exact": result["adjugate"] == direct_adj,
        "characteristic_probe_audit": probes,
        "characteristic_probe_exact": all(item["residual"] == 0 for item in probes.values()),
        "oak": {
            "division_free": True,
            "polynomial_growth_backend": True,
            "wall_clock_superiority_claimed": False,
        },
    }


def mixed_determinant_derivative(
    matrix: Sequence[Sequence[Scalar]],
    directions: Sequence[Sequence[Sequence[Scalar]]],
    *,
    max_order: int = 8,
) -> Fraction:
    """Exact symmetric multilinear derivative D^k det(A)[H1,...,Hk].

    R0.2 provides Q_k(H), the t^k coefficient of det(A+tH), so
        Q_k(H) = D^k det(A)[H,...,H] / k!.
    Möbius polarization over direction subsets extracts the mixed multilinear
    coefficient exactly.
    """
    a = _square_q(matrix)
    n = len(a)
    k = len(directions)
    if k == 0:
        return det_bareiss(a)
    if k > n:
        return Fraction(0)
    if k > max_order:
        raise ValueError(f"mixed derivative order {k} exceeds max_order={max_order}")
    checked = [_square_q(direction) for direction in directions]
    if any(len(direction) != n for direction in checked):
        raise ValueError("all directions must match the matrix shape")

    total = Fraction(0)
    for mask in range(1 << k):
        bits = mask.bit_count()
        summed = _direction_sum(checked, mask, n)
        jet = directional_determinantal_jet(a, summed)
        homogeneous_coefficient = jet.coefficients[k]
        total += (Fraction(-1) if (k - bits) & 1 else Fraction(1)) * homogeneous_coefficient
    return total


def multilinear_jet_packet(
    matrix: Sequence[Sequence[Scalar]],
    directions: Sequence[Sequence[Sequence[Scalar]]],
) -> dict:
    values = {}
    for order in range(len(directions) + 1):
        if order == 0:
            values["0"] = det_bareiss(matrix)
            continue
        # All ordered prefixes plus an order-reversal symmetry cross-check.
        prefix = list(directions[:order])
        direct = mixed_determinant_derivative(matrix, prefix)
        reverse = mixed_determinant_derivative(matrix, list(reversed(prefix)))
        values[str(order)] = {
            "derivative": direct,
            "reverse_order_derivative": reverse,
            "symmetric_exact": direct == reverse,
        }
    return {
        "orders": values,
        "oak": "exact finite multilinear probes; not yet a compressed full tensor materialization",
    }


def mixed_discriminant(matrices: Sequence[Sequence[Sequence[Scalar]]]) -> Fraction:
    """Normalized mixed discriminant with D(A,...,A)=det(A).

    Convention:
        D(A1,...,An) = (1/n!) * d^n/dt1...dtn det(sum ti Ai)|_{t=0}.
    """
    n = len(matrices)
    if n == 0:
        return Fraction(1)
    checked = [_square_q(matrix) for matrix in matrices]
    if any(len(matrix) != n for matrix in checked):
        raise ValueError("mixed discriminant requires exactly n matrices of shape nxn")
    derivative = mixed_determinant_derivative(_zero_matrix(n), checked, max_order=max(8, n))
    return derivative / math.factorial(n)


def higher_adjugate_duality_audit(matrix: Sequence[Sequence[Scalar]], order: int) -> dict:
    """Audit signed complementary-minor duality against the compound matrix."""
    a = _square_q(matrix)
    n = len(a)
    if not 0 <= order <= n:
        raise ValueError("order must lie in [0,n]")
    higher = generalized_cofactors(a, order)
    closed_order = n - order
    compound = compound_matrix(a, closed_order)
    lookup = {
        (tuple(compound["row_sets"][i]), tuple(compound["col_sets"][j])): compound["values"][i][j]
        for i in range(len(compound["row_sets"]))
        for j in range(len(compound["col_sets"]))
    }
    residuals: list[list[Fraction]] = []
    for i, open_rows in enumerate(higher["open_row_sets"]):
        row_residuals = []
        closed_rows = tuple(index for index in range(n) if index not in set(open_rows))
        for j, open_cols in enumerate(higher["open_col_sets"]):
            closed_cols = tuple(index for index in range(n) if index not in set(open_cols))
            sign = Fraction(-1 if (sum(open_rows) + sum(open_cols)) & 1 else 1)
            expected = sign * lookup[(closed_rows, closed_cols)]
            row_residuals.append(higher["values"][i][j] - expected)
        residuals.append(row_residuals)
    return {
        "order": order,
        "closed_compound_order": closed_order,
        "higher_adjugate": higher,
        "residuals": residuals,
        "duality_exact": all(value == 0 for row in residuals for value in row),
    }


def higher_adjugate_tower_audit(matrix: Sequence[Sequence[Scalar]]) -> dict:
    a = _square_q(matrix)
    audits = [higher_adjugate_duality_audit(a, order) for order in range(len(a) + 1)]
    ladder = singularity_ladder(a)
    return {
        "orders": audits,
        "all_dualities_exact": all(audit["duality_exact"] for audit in audits),
        "singularity_ladder": ladder,
        "first_nonzero_order_matches_nullity": ladder["rank_order_identity_exact"],
    }


@dataclass(frozen=True)
class GuardLedger:
    variables: tuple[str, ...]
    guards: tuple[str, ...]
    guard_satisfied: bool
    provenance: tuple[str, ...]
    preserved: bool = True


@dataclass(frozen=True)
class RewriteCertificate:
    name: str
    lhs: Fraction
    rhs: Fraction | None
    residual: Fraction | None
    exact: bool
    globally_valid: bool
    ledger: GuardLedger
    note: str


def _rank_one_matrix(u: Sequence[Scalar], v: Sequence[Scalar]) -> list[list[Fraction]]:
    uq, vq = [as_q(x) for x in u], [as_q(x) for x in v]
    return [[x * y for y in vq] for x in uq]


def rank_one_update_audit(
    matrix: Sequence[Sequence[Scalar]], u: Sequence[Scalar], v: Sequence[Scalar]
) -> RewriteCertificate:
    a = _square_q(matrix)
    n = len(a)
    uq, vq = [as_q(x) for x in u], [as_q(x) for x in v]
    if len(uq) != n or len(vq) != n:
        raise ValueError("u and v must match matrix dimension")
    update = _rank_one_matrix(uq, vq)
    lhs = det_bareiss(_matadd(a, update))
    adj = cofactor_adjugate(a)
    adj_u = [sum((adj[i][j] * uq[j] for j in range(n)), Fraction(0)) for i in range(n)]
    rhs = det_bareiss(a) + sum((vq[i] * adj_u[i] for i in range(n)), Fraction(0))
    residual = lhs - rhs
    return RewriteCertificate(
        "rank-one-polynomial-update",
        lhs,
        rhs,
        residual,
        residual == 0,
        True,
        GuardLedger((), (), True, ("det(A+uv^T)=det(A)+v^T adj(A)u",)),
        "global polynomial identity; no inverse or det(A)!=0 guard required",
    )


def sylvester_rewrite_audit(
    u: Sequence[Sequence[Scalar]], v: Sequence[Sequence[Scalar]]
) -> RewriteCertificate:
    uu, vv = _matrix_q(u), _matrix_q(v)
    if not uu or not vv:
        raise ValueError("U and V must be nonempty")
    n, k = len(uu), len(uu[0])
    if len(vv) != k or len(vv[0]) != n:
        raise ValueError("expected U shape n x k and V shape k x n")
    left = _matadd(_identity(n), _matmul(uu, vv))
    right = _matadd(_identity(k), _matmul(vv, uu))
    lhs, rhs = det_bareiss(left), det_bareiss(right)
    residual = lhs - rhs
    return RewriteCertificate(
        "sylvester-dimension-reduction",
        lhs,
        rhs,
        residual,
        residual == 0,
        True,
        GuardLedger((), (), True, ("det(I_n+UV)=det(I_k+VU)",)),
        f"exact dimension rewrite {n}x{n} -> {k}x{k}; usefulness depends on k relative to n",
    )


def _kronecker(left: Sequence[Sequence[Scalar]], right: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    a, b = _matrix_q(left), _matrix_q(right)
    return [
        [a[i][j] * b[p][q] for j in range(len(a[0])) for q in range(len(b[0]))]
        for i in range(len(a))
        for p in range(len(b))
    ]


def kronecker_rewrite_audit(
    left: Sequence[Sequence[Scalar]], right: Sequence[Sequence[Scalar]]
) -> RewriteCertificate:
    a, b = _square_q(left), _square_q(right)
    n, m = len(a), len(b)
    lhs = det_bareiss(_kronecker(a, b))
    rhs = det_bareiss(a) ** m * det_bareiss(b) ** n
    residual = lhs - rhs
    return RewriteCertificate(
        "kronecker-determinant-factorization",
        lhs,
        rhs,
        residual,
        residual == 0,
        True,
        GuardLedger((), (), True, ("det(A tensor B)=det(A)^m det(B)^n",)),
        "global square-matrix identity",
    )


def _inverse_exact(matrix: Sequence[Sequence[Scalar]]) -> list[list[Fraction]]:
    a = _square_q(matrix)
    n = len(a)
    columns = [gaussian_solve(a, [Fraction(i == j) for i in range(n)]) for j in range(n)]
    return transpose(columns)


def schur_rewrite_audit(matrix: Sequence[Sequence[Scalar]], split: int) -> RewriteCertificate:
    m = _square_q(matrix)
    n = len(m)
    if not 0 < split < n:
        raise ValueError("split must lie strictly between 0 and n")
    a = [row[:split] for row in m[:split]]
    b = [row[split:] for row in m[:split]]
    c = [row[:split] for row in m[split:]]
    d = [row[split:] for row in m[split:]]
    det_a = det_bareiss(a)
    guard = det_a != 0
    ledger = GuardLedger(
        ("A11",),
        ("det(A11) != 0",),
        guard,
        ("Schur complement D-C A11^{-1} B",),
    )
    lhs = det_bareiss(m)
    if not guard:
        return RewriteCertificate(
            "schur-complement",
            lhs,
            None,
            None,
            False,
            False,
            ledger,
            "rewrite refused because the pivot-block invertibility guard is false",
        )
    schur = _matsub(d, _matmul(_matmul(c, _inverse_exact(a)), b))
    rhs = det_a * det_bareiss(schur)
    residual = lhs - rhs
    return RewriteCertificate(
        "schur-complement",
        lhs,
        rhs,
        residual,
        residual == 0,
        False,
        ledger,
        "local rational rewrite; original invertibility guard is retained",
    )


def rootflow_characteristic_bridge(matrix: Sequence[Sequence[Scalar]]) -> dict:
    """Exact det(lambda I-A) packet in ROOTFLOW ascending coefficient convention."""
    a = _square_q(matrix)
    result = build_berkowitz_circuit(len(a)).evaluate(a)
    descending = result["characteristic_coefficients_descending"]
    ascending = result["rootflow_coefficients_ascending"]
    probes = []
    for lam in (-3, -1, 0, 2, 4):
        shifted = [
            [Fraction(lam if i == j else 0) - a[i][j] for j in range(len(a))]
            for i in range(len(a))
        ]
        direct = det_bareiss(shifted)
        polynomial = _poly_eval_descending(descending, lam)
        probes.append({"lambda": lam, "direct": direct, "polynomial": polynomial, "residual": polynomial - direct})
    return {
        "coefficient_convention": "ascending [a0,a1,...,an] for ROOTFLOW",
        "coefficients_ascending": ascending,
        "coefficients_descending": descending,
        "probe_audit": probes,
        "probe_exact": all(item["residual"] == 0 for item in probes),
        "rootflow_ready": len(ascending) >= 2 and ascending[-1] == 1,
        "note": "coefficient bridge is exact; numerical root tracking remains the responsibility of ROOTFLOW",
    }


def backend_complexity_atlas(max_n: int = 10) -> dict:
    if not 1 <= max_n <= 12:
        raise ValueError("max_n must lie in [1,12] for the subset comparison")
    rows = []
    first_berkowitz_not_larger = None
    for n in range(1, max_n + 1):
        subset = build_determinant_circuit(n, max_n=max_n)
        berkowitz = build_berkowitz_circuit(n, max_n=max_n)
        subset_ops = subset.circuit.metrics()["operation_nodes"]
        berkowitz_ops = berkowitz.circuit.metrics()["operation_nodes"]
        if first_berkowitz_not_larger is None and berkowitz_ops <= subset_ops:
            first_berkowitz_not_larger = n
        rows.append(
            {
                "n": n,
                "subset_operation_nodes": subset_ops,
                "berkowitz_operation_nodes": berkowitz_ops,
                "berkowitz_to_subset_ratio": berkowitz_ops / max(subset_ops, 1),
                "subset_transitions": subset.transitions,
            }
        )
    return {
        "rows": rows,
        "first_n_berkowitz_operation_nodes_not_larger": first_berkowitz_not_larger,
        "metric_boundary": "static hash-consed operation-node counts only; no runtime superiority claim",
    }


def compiler_packet(matrix: Sequence[Sequence[Scalar]]) -> dict:
    a = _square_q(matrix)
    berk = berkowitz_packet(a)
    tower = higher_adjugate_tower_audit(a)
    bridge = rootflow_characteristic_bridge(a)
    return {
        "berkowitz": berk,
        "higher_adjugate_tower": tower,
        "structural_profile": structural_profile(a),
        "rootflow_bridge": bridge,
        "oak": {
            "status": "D-MVP candidate",
            "theorem_claimed": False,
            "universal_speed_claimed": False,
            "domain_guards_preserved": True,
            "notes": [
                "Berkowitz-style circuit is division-free and polynomial-growth in this implementation",
                "mixed-jet probes are exact but exponentially expensive in derivative order due to polarization",
                "ROOTFLOW bridge certifies coefficients, not numerical eigenvalue continuation",
            ],
        },
    }


def _jsonify(value):
    if isinstance(value, Fraction):
        return qstr(value)
    if isinstance(value, (GuardLedger, RewriteCertificate)):
        return _jsonify(asdict(value))
    if isinstance(value, tuple):
        return [_jsonify(item) for item in value]
    if isinstance(value, list):
        return [_jsonify(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonify(item) for key, item in value.items()}
    return value


def _parse_matrix(text: str) -> list[list[Scalar]]:
    value = json.loads(text)
    if not isinstance(value, list) or any(not isinstance(row, list) for row in value):
        raise ValueError("matrix must be a JSON list of rows")
    return value


def demo_packet() -> dict:
    a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
    h1 = [[1, 0, 0], [0, 0, 0], [0, 0, -1]]
    h2 = [[0, 1, 0], [1, 0, 0], [0, 0, 0]]
    singular = [[1, 2, 3], [2, 4, 6], [0, 1, 1]]
    packet = compiler_packet(a)
    packet["mixed_derivative_2"] = mixed_determinant_derivative(a, [h1, h2])
    packet["mixed_symmetry_exact"] = (
        packet["mixed_derivative_2"] == mixed_determinant_derivative(a, [h2, h1])
    )
    packet["singular_rank_one_update"] = rank_one_update_audit(singular, [1, 0, 1], [2, -1, 1])
    packet["sylvester"] = sylvester_rewrite_audit([[1, 2], [0, 1], [2, -1]], [[1, 0, 1], [2, 1, 0]])
    packet["kronecker"] = kronecker_rewrite_audit([[1, 2], [3, 5]], [[2, 1], [0, 3]])
    packet["schur"] = schur_rewrite_audit([[2, 1, 1], [1, 3, 0], [2, 0, 4]], 2)
    packet["complexity_atlas"] = backend_complexity_atlas(8)
    return packet


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Omega-KRAMER-TRISTAN R0.3 matrix-expression compiler")
    sub = parser.add_subparsers(dest="command", required=False)

    charpoly = sub.add_parser("charpoly", help="emit division-free characteristic/determinant/adjugate packet")
    charpoly.add_argument("--matrix", required=True)

    bridge = sub.add_parser("rootflow-bridge", help="emit exact characteristic coefficients for ROOTFLOW")
    bridge.add_argument("--matrix", required=True)

    atlas = sub.add_parser("complexity-atlas", help="compare static subset/Berkowitz circuit sizes")
    atlas.add_argument("--max-n", type=int, default=10)

    sub.add_parser("demo", help="emit deterministic R0.3 evidence packet")

    args = parser.parse_args(argv)
    if args.command in (None, "demo"):
        payload = demo_packet()
    elif args.command == "charpoly":
        payload = compiler_packet(_parse_matrix(args.matrix))
    elif args.command == "rootflow-bridge":
        payload = rootflow_characteristic_bridge(_parse_matrix(args.matrix))
    elif args.command == "complexity-atlas":
        payload = backend_complexity_atlas(args.max_n)
    else:  # pragma: no cover
        parser.error("unknown command")
        return 2

    print(json.dumps(_jsonify(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
