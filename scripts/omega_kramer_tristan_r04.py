#!/usr/bin/env python3
"""Omega-KRAMER-TRISTAN R0.4 — OAKBench, sparse structure, guarded algebra and mode flow.

R0.4 extends R0.1-R0.3 with:
- empirical-but-non-promotional timing/memory telemetry for exact determinant backends;
- intermediate rational bit-length tracking separate from symbolic circuit size;
- DM-inspired alternating-path decomposition and a min-fill elimination-width heuristic;
- exact multivariate factor cancellation with a preserved Domain Ledger;
- singular-safe rank-k update polynomials det(A+tUV) with exact degree bounds;
- exact characteristic-coefficient parameter derivatives by reverse AD;
- ROOTFLOW-compatible simple-mode velocities from the characteristic polynomial;
- bounded equality-class rewrite planning with CVCD agreement and M-minus refusal memory.

OAK boundary
------------
Timing and memory measurements are observations of one Python process, not
algorithmic truth. The DM layer is explicitly DM-inspired rather than a claim
of a full canonical Dulmage-Mendelsohn implementation. The min-fill width is an
elimination-order upper bound, not exact treewidth. Classical determinant,
characteristic-polynomial, implicit-root and low-rank identities are not
claimed as new mathematics.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import tracemalloc
from dataclasses import asdict, dataclass
from fractions import Fraction
from time import perf_counter_ns
from typing import Callable, Sequence

try:
    from scripts.omega_kramer_tristan import (
        Scalar,
        _matrix_q,
        _square_q,
        as_q,
        det_bareiss,
        matrix_rank,
        qstr,
    )
    from scripts.omega_kramer_tristan_r02 import (
        build_determinant_circuit,
        directional_determinantal_jet,
        interpolate_polynomial,
        structural_profile,
    )
    from scripts.omega_kramer_tristan_r03 import (
        _matadd,
        _matmul,
        _poly_eval_descending,
        build_berkowitz_circuit,
        rootflow_characteristic_bridge,
        schur_rewrite_audit,
    )
except ModuleNotFoundError:
    from omega_kramer_tristan import (  # type: ignore
        Scalar,
        _matrix_q,
        _square_q,
        as_q,
        det_bareiss,
        matrix_rank,
        qstr,
    )
    from omega_kramer_tristan_r02 import (  # type: ignore
        build_determinant_circuit,
        directional_determinantal_jet,
        interpolate_polynomial,
        structural_profile,
    )
    from omega_kramer_tristan_r03 import (  # type: ignore
        _matadd,
        _matmul,
        _poly_eval_descending,
        build_berkowitz_circuit,
        rootflow_characteristic_bridge,
        schur_rewrite_audit,
    )


def _fraction_bits(value: Fraction) -> int:
    return max(abs(value.numerator).bit_length(), value.denominator.bit_length())


def instrumented_bareiss(matrix: Sequence[Sequence[Scalar]]) -> dict:
    """Exact Bareiss determinant plus intermediate rational-size telemetry."""
    a = _square_q(matrix)
    n = len(a)
    if n == 0:
        return {
            "determinant": Fraction(1),
            "updates": 0,
            "row_swaps": 0,
            "max_intermediate_bits": 1,
        }
    if n == 1:
        return {
            "determinant": a[0][0],
            "updates": 0,
            "row_swaps": 0,
            "max_intermediate_bits": _fraction_bits(a[0][0]),
        }
    sign = Fraction(1)
    previous = Fraction(1)
    updates = 0
    swaps = 0
    max_bits = max((_fraction_bits(x) for row in a for x in row), default=1)
    for k in range(n - 1):
        pivot_row = next((r for r in range(k, n) if a[r][k] != 0), None)
        if pivot_row is None:
            return {
                "determinant": Fraction(0),
                "updates": updates,
                "row_swaps": swaps,
                "max_intermediate_bits": max_bits,
            }
        if pivot_row != k:
            a[k], a[pivot_row] = a[pivot_row], a[k]
            sign = -sign
            swaps += 1
        pivot = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * pivot - a[i][k] * a[k][j]) / previous
                updates += 1
                max_bits = max(max_bits, _fraction_bits(a[i][j]))
            a[i][k] = Fraction(0)
        previous = pivot
    determinant = sign * a[-1][-1]
    return {
        "determinant": determinant,
        "updates": updates,
        "row_swaps": swaps,
        "max_intermediate_bits": max(max_bits, _fraction_bits(determinant)),
    }


def _measure(callable_: Callable[[], Fraction], *, repeats: int = 3) -> dict:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    times: list[int] = []
    peaks: list[int] = []
    values: list[Fraction] = []
    for _ in range(repeats):
        tracemalloc.start()
        start = perf_counter_ns()
        value = callable_()
        elapsed = perf_counter_ns() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        values.append(value)
        times.append(elapsed)
        peaks.append(peak)
    return {
        "median_ns": int(statistics.median(times)),
        "min_ns": min(times),
        "max_ns": max(times),
        "peak_bytes_max": max(peaks),
        "values_identical": all(value == values[0] for value in values),
        "value": values[0],
        "observation_boundary": "process-local telemetry; never a deterministic performance gate",
    }


def _circuit_numeric_swell(compiled, matrix: Sequence[Sequence[Scalar]], output: int) -> dict:
    environment = compiled.environment(matrix)
    value, values = compiled.circuit.evaluate(output, environment)
    return {
        "value": value,
        "max_intermediate_bits": max((_fraction_bits(x) for x in values), default=1),
        "node_count": len(values),
        "operation_nodes": compiled.circuit.metrics()["operation_nodes"],
    }


def benchmark_matrix(matrix: Sequence[Sequence[Scalar]], *, repeats: int = 3) -> dict:
    """Compare exact backends without promoting noisy timings into truth."""
    a = _square_q(matrix)
    n = len(a)
    reference = det_bareiss(a)
    bareiss_stats = instrumented_bareiss(a)
    bareiss_obs = _measure(lambda: det_bareiss(a), repeats=repeats)

    berkowitz = build_berkowitz_circuit(n, max_n=max(24, n))
    berk_env = berkowitz.environment(a)
    berk_eval_obs = _measure(
        lambda: berkowitz.circuit.evaluate(berkowitz.determinant_output, berk_env)[0],
        repeats=repeats,
    )
    berk_one_shot = _measure(
        lambda: build_berkowitz_circuit(n, max_n=max(24, n)).evaluate(a)["determinant"],
        repeats=repeats,
    )
    berk_swell = _circuit_numeric_swell(berkowitz, a, berkowitz.determinant_output)

    subset_packet = None
    if n <= 8:
        subset = build_determinant_circuit(n, max_n=8)
        subset_env = subset.environment(a)
        subset_eval_obs = _measure(
            lambda: subset.circuit.evaluate(subset.output, subset_env)[0], repeats=repeats
        )
        subset_one_shot = _measure(
            lambda: (
                lambda compiled: compiled.circuit.evaluate(
                    compiled.output, compiled.environment(a)
                )[0]
            )(build_determinant_circuit(n, max_n=8)),
            repeats=repeats,
        )
        subset_swell = _circuit_numeric_swell(subset, a, subset.output)
        subset_packet = {
            "evaluation": subset_eval_obs,
            "one_shot_compile_plus_eval": subset_one_shot,
            "numeric_swell": subset_swell,
            "exact": subset_eval_obs["value"] == reference,
        }

    return {
        "n": n,
        "reference_determinant": reference,
        "bareiss": {
            "observation": bareiss_obs,
            "instrumentation": bareiss_stats,
            "exact": bareiss_obs["value"] == reference,
        },
        "berkowitz": {
            "evaluation": berk_eval_obs,
            "one_shot_compile_plus_eval": berk_one_shot,
            "numeric_swell": berk_swell,
            "exact": berk_eval_obs["value"] == reference,
        },
        "subset": subset_packet,
        "all_exact": (
            bareiss_obs["value"] == reference
            and berk_eval_obs["value"] == reference
            and (subset_packet is None or subset_packet["exact"])
        ),
        "oak": {
            "timing_order_claimed": False,
            "memory_order_claimed": False,
            "symbolic_expression_size_claimed_from_bitlength": False,
        },
    }


def oakbench_atlas(*, repeats: int = 3) -> dict:
    families = {
        "dense3": [[2, 1, 3], [1, 4, 2], [5, 0, 1]],
        "banded5": [
            [3, 1, 0, 0, 0],
            [1, 4, 1, 0, 0],
            [0, 1, 5, 1, 0],
            [0, 0, 1, 6, 1],
            [0, 0, 0, 1, 7],
        ],
        "block6": [
            [2, 1, 0, 0, 0, 0],
            [1, 3, 0, 0, 0, 0],
            [0, 0, 2, 1, 0, 0],
            [0, 0, 1, 4, 0, 0],
            [0, 0, 0, 0, 3, 1],
            [0, 0, 0, 0, 1, 5],
        ],
        "singular4": [[1, 2, 0, 0], [2, 4, 0, 0], [0, 0, 1, 1], [0, 0, 2, 2]],
        "vandermonde5": [[Fraction(i) ** j for j in range(5)] for i in range(1, 6)],
    }
    results = {name: benchmark_matrix(matrix, repeats=repeats) for name, matrix in families.items()}
    return {
        "families": results,
        "all_exact": all(packet["all_exact"] for packet in results.values()),
        "promotion_boundary": "telemetry is retained as evidence only; no runtime superiority gate",
    }


def _support(matrix: Sequence[Sequence[Scalar]]) -> list[list[int]]:
    a = _matrix_q(matrix)
    return [[j for j, value in enumerate(row) if value != 0] for row in a]


def _maximum_support_matching(matrix: Sequence[Sequence[Scalar]]) -> tuple[dict[int, int], dict[int, int]]:
    a = _matrix_q(matrix)
    rows = len(a)
    cols = len(a[0]) if a else 0
    adjacency = _support(a)
    col_to_row: dict[int, int] = {}

    def augment(row: int, seen: set[int]) -> bool:
        for col in adjacency[row]:
            if col in seen:
                continue
            seen.add(col)
            if col not in col_to_row or augment(col_to_row[col], seen):
                col_to_row[col] = row
                return True
        return False

    for row in range(rows):
        augment(row, set())
    row_to_col = {row: col for col, row in col_to_row.items()}
    return row_to_col, col_to_row


def _alternating_from_rows(
    matrix: Sequence[Sequence[Scalar]],
    starts: Sequence[int],
    row_to_col: dict[int, int],
    col_to_row: dict[int, int],
) -> tuple[set[int], set[int]]:
    adjacency = _support(matrix)
    rows_seen = set(starts)
    cols_seen: set[int] = set()
    queue = [("r", row) for row in starts]
    while queue:
        kind, index = queue.pop(0)
        if kind == "r":
            matched_col = row_to_col.get(index)
            for col in adjacency[index]:
                if col == matched_col:
                    continue
                if col not in cols_seen:
                    cols_seen.add(col)
                    queue.append(("c", col))
        else:
            matched_row = col_to_row.get(index)
            if matched_row is not None and matched_row not in rows_seen:
                rows_seen.add(matched_row)
                queue.append(("r", matched_row))
    return rows_seen, cols_seen


def _alternating_from_cols(
    matrix: Sequence[Sequence[Scalar]],
    starts: Sequence[int],
    row_to_col: dict[int, int],
    col_to_row: dict[int, int],
) -> tuple[set[int], set[int]]:
    a = _matrix_q(matrix)
    rows = len(a)
    cols_seen = set(starts)
    rows_seen: set[int] = set()
    queue = [("c", col) for col in starts]
    while queue:
        kind, index = queue.pop(0)
        if kind == "c":
            matched_row = col_to_row.get(index)
            for row in range(rows):
                if a[row][index] == 0 or row == matched_row:
                    continue
                if row not in rows_seen:
                    rows_seen.add(row)
                    queue.append(("r", row))
        else:
            matched_col = row_to_col.get(index)
            if matched_col is not None and matched_col not in cols_seen:
                cols_seen.add(matched_col)
                queue.append(("c", matched_col))
    return rows_seen, cols_seen


def dm_inspired_decomposition(matrix: Sequence[Sequence[Scalar]]) -> dict:
    """Alternating-path structural partition; explicitly not full canonical DM."""
    a = _matrix_q(matrix)
    rows = len(a)
    cols = len(a[0]) if a else 0
    row_to_col, col_to_row = _maximum_support_matching(a)
    unmatched_rows = [row for row in range(rows) if row not in row_to_col]
    unmatched_cols = [col for col in range(cols) if col not in col_to_row]
    under_rows, under_cols = _alternating_from_rows(
        a, unmatched_rows, row_to_col, col_to_row
    )
    over_rows, over_cols = _alternating_from_cols(
        a, unmatched_cols, row_to_col, col_to_row
    )
    overlap_rows = under_rows & over_rows
    overlap_cols = under_cols & over_cols
    well_rows = set(range(rows)) - under_rows - over_rows
    well_cols = set(range(cols)) - under_cols - over_cols
    return {
        "structural_rank": len(row_to_col),
        "exact_rank": matrix_rank(a),
        "matching_row_to_col": row_to_col,
        "unmatched_rows": unmatched_rows,
        "unmatched_cols": unmatched_cols,
        "under_region": {"rows": sorted(under_rows), "cols": sorted(under_cols)},
        "over_region": {"rows": sorted(over_rows), "cols": sorted(over_cols)},
        "well_region": {"rows": sorted(well_rows), "cols": sorted(well_cols)},
        "overlap": {"rows": sorted(overlap_rows), "cols": sorted(overlap_cols)},
        "partition_disjoint": not overlap_rows and not overlap_cols,
        "vertex_cover_exact": (
            under_rows | over_rows | well_rows == set(range(rows))
            and under_cols | over_cols | well_cols == set(range(cols))
        ),
        "boundary": "DM-inspired alternating-path partition; not a full canonical DM theorem implementation",
    }


def _row_intersection_graph(matrix: Sequence[Sequence[Scalar]]) -> dict[int, set[int]]:
    a = _matrix_q(matrix)
    rows = len(a)
    graph = {i: set() for i in range(rows)}
    for i in range(rows):
        support_i = {j for j, value in enumerate(a[i]) if value != 0}
        for k in range(i + 1, rows):
            if support_i & {j for j, value in enumerate(a[k]) if value != 0}:
                graph[i].add(k)
                graph[k].add(i)
    return graph


def min_fill_width_heuristic(matrix: Sequence[Sequence[Scalar]]) -> dict:
    graph = {v: set(neighbors) for v, neighbors in _row_intersection_graph(matrix).items()}
    order: list[int] = []
    width = 0
    fill_edges = 0
    while graph:
        scored = []
        for vertex, neighbors in graph.items():
            missing = 0
            nn = sorted(neighbors)
            for i, left in enumerate(nn):
                for right in nn[i + 1 :]:
                    if right not in graph[left]:
                        missing += 1
            scored.append((missing, len(neighbors), vertex))
        _, degree, vertex = min(scored)
        neighbors = list(graph[vertex])
        width = max(width, degree)
        for i, left in enumerate(neighbors):
            for right in neighbors[i + 1 :]:
                if right not in graph[left]:
                    graph[left].add(right)
                    graph[right].add(left)
                    fill_edges += 1
        for neighbor in neighbors:
            graph[neighbor].discard(vertex)
        del graph[vertex]
        order.append(vertex)
    return {
        "elimination_order": order,
        "elimination_width_upper_bound": width,
        "fill_edges_added": fill_edges,
        "boundary": "min-fill heuristic on row-intersection graph; not exact treewidth",
    }


def _mv_normalize(terms: dict[tuple[int, ...], Scalar], variables: Sequence[str]) -> dict[tuple[int, ...], Fraction]:
    dimension = len(variables)
    out: dict[tuple[int, ...], Fraction] = {}
    for exponent, coefficient in terms.items():
        if len(exponent) != dimension or any(power < 0 for power in exponent):
            raise ValueError("invalid multivariate exponent")
        q = as_q(coefficient)
        if q:
            out[tuple(exponent)] = out.get(tuple(exponent), Fraction(0)) + q
    return {exp: coeff for exp, coeff in out.items() if coeff}


def _mv_mul(
    left: dict[tuple[int, ...], Fraction], right: dict[tuple[int, ...], Fraction]
) -> dict[tuple[int, ...], Fraction]:
    out: dict[tuple[int, ...], Fraction] = {}
    for exp_a, coeff_a in left.items():
        for exp_b, coeff_b in right.items():
            exponent = tuple(a + b for a, b in zip(exp_a, exp_b))
            out[exponent] = out.get(exponent, Fraction(0)) + coeff_a * coeff_b
    return {exp: coeff for exp, coeff in out.items() if coeff}


def _mv_sub(
    left: dict[tuple[int, ...], Fraction], right: dict[tuple[int, ...], Fraction]
) -> dict[tuple[int, ...], Fraction]:
    out = dict(left)
    for exp, coeff in right.items():
        out[exp] = out.get(exp, Fraction(0)) - coeff
        if out[exp] == 0:
            del out[exp]
    return out


def _mv_lead(poly: dict[tuple[int, ...], Fraction]) -> tuple[tuple[int, ...], Fraction]:
    if not poly:
        raise ValueError("zero polynomial has no leading term")
    exponent = max(poly)
    return exponent, poly[exponent]


def _mv_divmod_single(
    dividend: dict[tuple[int, ...], Fraction], divisor: dict[tuple[int, ...], Fraction]
) -> tuple[dict[tuple[int, ...], Fraction], dict[tuple[int, ...], Fraction]]:
    if not divisor:
        raise ZeroDivisionError("zero multivariate divisor")
    remainder_work = dict(dividend)
    quotient: dict[tuple[int, ...], Fraction] = {}
    divisor_exp, divisor_coeff = _mv_lead(divisor)
    while remainder_work:
        lead_exp, lead_coeff = _mv_lead(remainder_work)
        if any(a < b for a, b in zip(lead_exp, divisor_exp)):
            break
        exponent = tuple(a - b for a, b in zip(lead_exp, divisor_exp))
        coefficient = lead_coeff / divisor_coeff
        quotient[exponent] = quotient.get(exponent, Fraction(0)) + coefficient
        term = {exponent: coefficient}
        remainder_work = _mv_sub(remainder_work, _mv_mul(term, divisor))
    return ({exp: coeff for exp, coeff in quotient.items() if coeff}, remainder_work)


def _mv_serial(poly: dict[tuple[int, ...], Fraction]) -> list[dict]:
    return [
        {"exponents": exponent, "coefficient": coefficient}
        for exponent, coefficient in sorted(poly.items(), reverse=True)
    ]


@dataclass(frozen=True)
class MultiDomainLedger:
    variables: tuple[str, ...]
    original_guard: str
    cancelled_factor: tuple[tuple[tuple[int, ...], Fraction], ...]
    exact_division: bool
    preserved: bool = True


def multivariate_guarded_cancel(
    numerator: dict[tuple[int, ...], Scalar],
    denominator: dict[tuple[int, ...], Scalar],
    factor: dict[tuple[int, ...], Scalar],
    *,
    variables: Sequence[str],
) -> dict:
    vars_tuple = tuple(variables)
    num = _mv_normalize(numerator, vars_tuple)
    den = _mv_normalize(denominator, vars_tuple)
    fac = _mv_normalize(factor, vars_tuple)
    if not den:
        raise ZeroDivisionError("zero denominator polynomial")
    if not fac:
        raise ZeroDivisionError("zero cancellation factor")
    num_q, num_r = _mv_divmod_single(num, fac)
    den_q, den_r = _mv_divmod_single(den, fac)
    exact = not num_r and not den_r
    ledger = MultiDomainLedger(
        vars_tuple,
        "original_denominator(variables) != 0",
        tuple(sorted(fac.items(), reverse=True)),
        exact,
    )
    return {
        "exact": exact,
        "reduced_numerator": _mv_serial(num_q) if exact else None,
        "reduced_denominator": _mv_serial(den_q) if exact else None,
        "numerator_remainder": _mv_serial(num_r),
        "denominator_remainder": _mv_serial(den_r),
        "ledger": ledger,
        "boundary": "exact single-factor multivariate division under lexicographic monomial order",
    }


def rank_k_update_polynomial(
    matrix: Sequence[Sequence[Scalar]],
    u: Sequence[Sequence[Scalar]],
    v: Sequence[Sequence[Scalar]],
) -> dict:
    """Exact polynomial det(A+tUV), valid whether or not A is singular."""
    a = _square_q(matrix)
    uu, vv = _matrix_q(u), _matrix_q(v)
    n = len(a)
    if len(uu) != n or not uu:
        raise ValueError("U must have n rows")
    rank_columns = len(uu[0])
    if any(len(row) != rank_columns for row in uu):
        raise ValueError("U rows must have equal length")
    if len(vv) != rank_columns or (vv and any(len(row) != n for row in vv)):
        raise ValueError("V must have shape r x n")
    update = _matmul(uu, vv)
    rank_bound = matrix_rank(update)
    jet = directional_determinantal_jet(a, update)
    coefficients = list(jet.coefficients)
    degree_bound_exact = all(
        coefficients[k] == 0 for k in range(rank_bound + 1, len(coefficients))
    )
    probes = []
    for t in (-2, -1, 0, 1, 2):
        shifted = _matadd(a, [[as_q(t) * value for value in row] for row in update])
        direct = det_bareiss(shifted)
        polynomial = sum(
            (coefficients[k] * (Fraction(t) ** k) for k in range(len(coefficients))),
            Fraction(0),
        )
        probes.append({"t": t, "direct": direct, "polynomial": polynomial, "residual": polynomial - direct})
    return {
        "base_rank": matrix_rank(a),
        "base_singular": det_bareiss(a) == 0,
        "update_rank": rank_bound,
        "coefficients_ascending_t": coefficients,
        "degree_bound_exact": degree_bound_exact,
        "probe_exact": all(probe["residual"] == 0 for probe in probes),
        "probes": probes,
        "boundary": "global polynomial update; no inverse and no det(A)!=0 guard",
    }


def characteristic_parameter_derivative(
    matrix: Sequence[Sequence[Scalar]], direction: Sequence[Sequence[Scalar]]
) -> dict:
    """Exact d/dtheta coefficients of det(lambda I-(A+theta H)) at theta=0."""
    a = _square_q(matrix)
    h = _square_q(direction)
    n = len(a)
    if len(h) != n:
        raise ValueError("direction must match matrix shape")
    compiled = build_berkowitz_circuit(n, max_n=max(24, n))
    env = compiled.environment(a)
    derivatives_desc: list[Fraction] = []
    for node in compiled.characteristic_coefficients:
        _, gradient = compiled.circuit.reverse_gradient(node, env)
        derivative = sum(
            (gradient[f"a_{i}_{j}"] * h[i][j] for i in range(n) for j in range(n)),
            Fraction(0),
        )
        derivatives_desc.append(derivative)
    base_desc = list(compiled.evaluate(a)["characteristic_coefficients_descending"])

    xs = list(range(n + 1))
    coefficient_samples = [[] for _ in range(n + 1)]
    for t in xs:
        shifted = _matadd(a, [[Fraction(t) * value for value in row] for row in h])
        char = compiled.evaluate(shifted)["characteristic_coefficients_descending"]
        for index, value in enumerate(char):
            coefficient_samples[index].append(value)
    interpolation_derivatives = []
    for samples in coefficient_samples:
        polynomial = interpolate_polynomial(xs, samples)
        interpolation_derivatives.append(polynomial[1] if len(polynomial) > 1 else Fraction(0))
    return {
        "base_coefficients_descending": base_desc,
        "base_coefficients_rootflow_ascending": list(reversed(base_desc)),
        "derivative_coefficients_descending": derivatives_desc,
        "derivative_coefficients_rootflow_ascending": list(reversed(derivatives_desc)),
        "interpolation_derivative_descending": interpolation_derivatives,
        "reverse_ad_crosscheck_exact": derivatives_desc == interpolation_derivatives,
        "boundary": "exact coefficient derivative for a linear matrix path A+theta H",
    }


def _poly_eval_ascending(coefficients: Sequence[Scalar], x: Scalar) -> Fraction:
    q = as_q(x)
    out = Fraction(0)
    power = Fraction(1)
    for coefficient in coefficients:
        out += as_q(coefficient) * power
        power *= q
    return out


def _poly_derivative_eval_ascending(coefficients: Sequence[Scalar], x: Scalar) -> Fraction:
    q = as_q(x)
    out = Fraction(0)
    power = Fraction(1)
    for k in range(1, len(coefficients)):
        out += k * as_q(coefficients[k]) * power
        power *= q
    return out


def mode_velocity_packet(
    matrix: Sequence[Sequence[Scalar]],
    direction: Sequence[Sequence[Scalar]],
    eigenvalue: Scalar,
) -> dict:
    """ROOTFLOW-compatible simple-root velocity from characteristic coefficients."""
    parameter = characteristic_parameter_derivative(matrix, direction)
    coefficients = parameter["base_coefficients_rootflow_ascending"]
    velocity_coefficients = parameter["derivative_coefficients_rootflow_ascending"]
    root = as_q(eigenvalue)
    root_residual = _poly_eval_ascending(coefficients, root)
    derivative_lambda = _poly_derivative_eval_ascending(coefficients, root)
    derivative_theta = _poly_eval_ascending(velocity_coefficients, root)
    if root_residual != 0:
        return {
            "accepted": False,
            "reason": "supplied eigenvalue is not an exact root of the characteristic polynomial",
            "root_residual": root_residual,
        }
    if derivative_lambda == 0:
        return {
            "accepted": False,
            "reason": "multiple/critical eigenvalue: simple-root ROOTFLOW coordinates are singular",
            "root_residual": root_residual,
            "dP_dlambda": derivative_lambda,
        }
    exact_velocity = -derivative_theta / derivative_lambda
    runtime_crosscheck = {"available": False, "reason": "optional numpy/ROOTFLOW runtime not imported"}
    try:
        import numpy as np  # type: ignore
        from omega_rootflow_t.core import root_velocity  # type: ignore

        runtime_value = root_velocity(
            np.asarray([complex(float(as_q(x))) for x in coefficients], dtype=np.complex128),
            np.asarray([complex(float(as_q(x))) for x in velocity_coefficients], dtype=np.complex128),
            np.asarray([complex(float(root))], dtype=np.complex128),
        )[0]
        runtime_crosscheck = {
            "available": True,
            "rootflow_velocity": runtime_value,
            "absolute_residual": abs(runtime_value - complex(float(exact_velocity))),
        }
    except Exception as exc:  # optional dependency/runtime surface
        runtime_crosscheck = {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
    return {
        "accepted": True,
        "eigenvalue": root,
        "dP_dlambda": derivative_lambda,
        "dP_dtheta": derivative_theta,
        "velocity_exact": exact_velocity,
        "coefficient_derivative_exact": parameter["reverse_ad_crosscheck_exact"],
        "rootflow_runtime_crosscheck": runtime_crosscheck,
        "formula": "lambda_dot = -P_theta/P_lambda",
        "boundary": "valid only for a supplied simple exact eigenvalue",
    }


@dataclass(frozen=True)
class RewriteCandidate:
    name: str
    value: Fraction | None
    exact: bool
    guard_satisfied: bool
    static_cost: int
    provenance: tuple[str, ...]


def bounded_rewrite_portfolio(matrix: Sequence[Sequence[Scalar]]) -> dict:
    """Enumerate a bounded equality class and choose by deterministic static cost."""
    a = _square_q(matrix)
    n = len(a)
    reference = det_bareiss(a)
    profile = structural_profile(a)
    candidates: list[RewriteCandidate] = [
        RewriteCandidate("bareiss", reference, True, True, max(1, n**3), ("direct exact oracle",))
    ]
    m_minus: list[dict] = []

    berk = build_berkowitz_circuit(n, max_n=max(24, n))
    berk_value = berk.evaluate(a)["determinant"]
    candidates.append(
        RewriteCandidate(
            "berkowitz-circuit",
            berk_value,
            berk_value == reference,
            True,
            berk.circuit.metrics()["operation_nodes"],
            ("division-free characteristic circuit",),
        )
    )

    if n <= 8:
        subset = build_determinant_circuit(n, max_n=8)
        subset_value = subset.circuit.evaluate(subset.output, subset.environment(a))[0]
        candidates.append(
            RewriteCandidate(
                "subset-circuit",
                subset_value,
                subset_value == reference,
                True,
                subset.circuit.metrics()["operation_nodes"],
                ("exact subset assignment circuit",),
            )
        )
    else:
        m_minus.append({"candidate": "subset-circuit", "reason": "bounded out for n>8"})

    if profile["diagonal"]:
        value = math.prod((a[i][i] for i in range(n)), start=Fraction(1))
        candidates.append(
            RewriteCandidate("diagonal-product", value, value == reference, True, max(1, n - 1), ("diagonal structure",))
        )
    elif profile["upper_triangular"] or profile["lower_triangular"]:
        value = math.prod((a[i][i] for i in range(n)), start=Fraction(1))
        candidates.append(
            RewriteCandidate("triangular-product", value, value == reference, True, max(1, n - 1), ("triangular structure",))
        )

    components = [
        component
        for component in profile["balanced_nonzero_blocks"]
        if component["rows"] and component["cols"]
    ]
    if len(components) > 1 and sum(len(c["rows"]) for c in components) == n:
        value = Fraction(1)
        cost = 0
        for component in components:
            rows = list(component["rows"])
            cols = list(component["cols"])
            block = [[a[i][j] for j in cols] for i in rows]
            value *= det_bareiss(block)
            cost += max(1, len(rows) ** 3)
        candidates.append(
            RewriteCandidate("support-block-product", value, value == reference, True, cost, ("disconnected bipartite support components",))
        )

    for split in range(1, n):
        schur = schur_rewrite_audit(a, split)
        if schur.exact and schur.rhs is not None:
            candidates.append(
                RewriteCandidate(
                    f"schur-split-{split}",
                    schur.rhs,
                    schur.rhs == reference,
                    schur.ledger.guard_satisfied,
                    max(1, split**3 + (n - split) ** 3 + n * n),
                    tuple(schur.ledger.provenance),
                )
            )
        else:
            m_minus.append(
                {
                    "candidate": f"schur-split-{split}",
                    "reason": schur.note,
                    "guard_satisfied": schur.ledger.guard_satisfied,
                }
            )

    eligible = [candidate for candidate in candidates if candidate.exact and candidate.guard_satisfied]
    selected = min(eligible, key=lambda candidate: (candidate.static_cost, candidate.name))
    return {
        "reference": reference,
        "candidates": candidates,
        "selected": selected,
        "cvcd_agreement_exact": all(
            candidate.value == reference for candidate in eligible if candidate.value is not None
        ),
        "m_minus": m_minus,
        "selection_boundary": "deterministic static-cost portfolio; empirical timing is telemetry, not selector truth",
    }


def compiler_packet(matrix: Sequence[Sequence[Scalar]]) -> dict:
    a = _square_q(matrix)
    return {
        "structure": structural_profile(a),
        "dm_inspired": dm_inspired_decomposition(a),
        "min_fill": min_fill_width_heuristic(a),
        "rewrite_portfolio": bounded_rewrite_portfolio(a),
        "rootflow_bridge": rootflow_characteristic_bridge(a),
        "oak": {
            "status": "D-MVP candidate",
            "theorem_claimed": False,
            "performance_superiority_claimed": False,
            "dm_canonical_claimed": False,
            "exact_treewidth_claimed": False,
        },
    }


def _jsonify(value):
    if isinstance(value, Fraction):
        return qstr(value)
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, (MultiDomainLedger, RewriteCandidate)):
        return _jsonify(asdict(value))
    if isinstance(value, tuple):
        return [_jsonify(item) for item in value]
    if isinstance(value, list):
        return [_jsonify(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify(item) for key, item in value.items()}
    return value


def _parse_matrix(text: str) -> list[list[Scalar]]:
    value = json.loads(text)
    if not isinstance(value, list) or any(not isinstance(row, list) for row in value):
        raise ValueError("matrix must be a JSON list of rows")
    return value


def demo_packet() -> dict:
    a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
    singular = [[1, 2, 3], [2, 4, 6], [0, 1, 1]]
    u = [[1, 0], [0, 1], [1, 1]]
    v = [[1, 2, 0], [0, -1, 1]]
    diagonal = [[2, 0, 0], [0, 3, 0], [0, 0, 5]]
    direction = [[5, 0, 0], [0, -1, 0], [0, 0, 2]]
    factor = {(1, 0): 1, (0, 1): 1}
    reduced_num = {(1, 0): 1, (0, 0): 1}
    reduced_den = {(0, 1): 1, (0, 0): 1}
    numerator = _mv_mul(_mv_normalize(factor, ("x", "y")), _mv_normalize(reduced_num, ("x", "y")))
    denominator = _mv_mul(_mv_normalize(factor, ("x", "y")), _mv_normalize(reduced_den, ("x", "y")))
    packet = compiler_packet(a)
    packet["oakbench_small"] = benchmark_matrix(a, repeats=2)
    packet["rank_k_update"] = rank_k_update_polynomial(singular, u, v)
    packet["characteristic_parameter_derivative"] = characteristic_parameter_derivative(diagonal, direction)
    packet["mode_velocity"] = mode_velocity_packet(diagonal, direction, 2)
    packet["multivariate_guarded_cancel"] = multivariate_guarded_cancel(
        numerator, denominator, factor, variables=("x", "y")
    )
    return packet


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Omega-KRAMER-TRISTAN R0.4 OAKBench and mode-flow compiler")
    sub = parser.add_subparsers(dest="command", required=False)

    bench = sub.add_parser("oakbench", help="emit bounded exact backend telemetry atlas")
    bench.add_argument("--repeats", type=int, default=3)

    structure = sub.add_parser("structure", help="emit DM-inspired/min-fill/rewrite packet")
    structure.add_argument("--matrix", required=True)

    velocity = sub.add_parser("mode-velocity", help="emit exact simple eigenvalue velocity packet")
    velocity.add_argument("--matrix", required=True)
    velocity.add_argument("--direction", required=True)
    velocity.add_argument("--eigenvalue", required=True)

    sub.add_parser("demo", help="emit deterministic R0.4 evidence packet plus observational telemetry")

    args = parser.parse_args(argv)
    if args.command in (None, "demo"):
        payload = demo_packet()
    elif args.command == "oakbench":
        payload = oakbench_atlas(repeats=args.repeats)
    elif args.command == "structure":
        payload = compiler_packet(_parse_matrix(args.matrix))
    elif args.command == "mode-velocity":
        payload = mode_velocity_packet(
            _parse_matrix(args.matrix), _parse_matrix(args.direction), args.eigenvalue
        )
    else:  # pragma: no cover
        parser.error("unknown command")
        return 2

    print(json.dumps(_jsonify(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
