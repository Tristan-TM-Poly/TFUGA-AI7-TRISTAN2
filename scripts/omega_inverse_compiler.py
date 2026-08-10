#!/usr/bin/env python3
"""Omega-INVERSE-T∞ v0.1: local inverse-series compiler.

Stdlib-only research prototype for regular Taylor reversion and Puiseux
branches of a supplied truncated local series.

Input convention:
    F(h) = f(x0 + h) - f(x0) = sum(a[n] h**n), with a[0] = 0.

OAK boundary:
- exact rational arithmetic is used for regular formal-series operations;
- algebraic/rational/ratio recognition is a candidate generator, not proof;
- critical-point radius estimates use the supplied truncated polynomial only;
- Puiseux coefficients are numeric complex approximations for that polynomial;
- global invertibility is never inferred from local reversion.
"""

from __future__ import annotations

import argparse
import cmath
import json
import math
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Sequence


def as_q(value: int | float | str | Fraction) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(str(value))
    return Fraction(value)


def qstr(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def cdict(value: complex, tol: float = 1e-13) -> dict[str, float]:
    re = 0.0 if abs(value.real) < tol else float(value.real)
    im = 0.0 if abs(value.imag) < tol else float(value.imag)
    return {"re": re, "im": im}


def pad(coeffs: Sequence, order: int) -> list[Fraction]:
    data = [as_q(x) for x in coeffs]
    if len(data) < order + 1:
        data += [Fraction(0)] * (order + 1 - len(data))
    return data[: order + 1]


def series_add(a: Sequence, b: Sequence, order: int) -> list[Fraction]:
    aa, bb = pad(a, order), pad(b, order)
    return [aa[i] + bb[i] for i in range(order + 1)]


def series_sub(a: Sequence, b: Sequence, order: int) -> list[Fraction]:
    aa, bb = pad(a, order), pad(b, order)
    return [aa[i] - bb[i] for i in range(order + 1)]


def series_mul(a: Sequence, b: Sequence, order: int) -> list[Fraction]:
    aa, bb = pad(a, order), pad(b, order)
    out = [Fraction(0)] * (order + 1)
    for i, ai in enumerate(aa):
        if ai == 0:
            continue
        for j in range(order + 1 - i):
            if bb[j] != 0:
                out[i + j] += ai * bb[j]
    return out


def series_pow(a: Sequence, exponent: int, order: int) -> list[Fraction]:
    if exponent < 0:
        raise ValueError("series_pow requires a nonnegative exponent")
    out = [Fraction(1)] + [Fraction(0)] * order
    base = pad(a, order)
    k = exponent
    while k:
        if k & 1:
            out = series_mul(out, base, order)
        base = series_mul(base, base, order)
        k //= 2
    return out


def series_compose(f: Sequence, g: Sequence, order: int) -> list[Fraction]:
    """Return f(g(z)) modulo z**(order+1), using Horner composition."""
    ff, gg = pad(f, order), pad(g, order)
    out = [Fraction(0)] * (order + 1)
    for coefficient in reversed(ff):
        out = series_mul(out, gg, order)
        out[0] += coefficient
    return out


def series_derivative(a: Sequence) -> list[Fraction]:
    aa = [as_q(x) for x in a]
    return [Fraction(i) * aa[i] for i in range(1, len(aa))]


def series_reciprocal(a: Sequence, order: int) -> list[Fraction]:
    aa = pad(a, order)
    if aa[0] == 0:
        raise ValueError("series reciprocal requires nonzero constant term")
    out = [Fraction(0)] * (order + 1)
    out[0] = 1 / aa[0]
    for n in range(1, order + 1):
        out[n] = -sum(aa[j] * out[n - j] for j in range(1, n + 1)) / aa[0]
    return out


def first_nonzero_degree(coeffs: Sequence) -> int | None:
    for degree, value in enumerate(coeffs):
        if degree > 0 and as_q(value) != 0:
            return degree
    return None


def classify_invertibility(coeffs: Sequence) -> tuple[str, int | None]:
    aa = [as_q(x) for x in coeffs]
    if not aa or aa[0] != 0:
        raise ValueError("local series must be shifted so a[0] = 0")
    multiplicity = first_nonzero_degree(aa)
    if multiplicity is None:
        return "degenerate", None
    if multiplicity == 1:
        return "regular", 1
    return "critical", multiplicity


def revert_series(coeffs: Sequence, order: int) -> list[Fraction]:
    """Exact triangular formal reversion for F(0)=0 and F'(0)!=0."""
    a = pad(coeffs, order)
    status, _ = classify_invertibility(a)
    if status != "regular":
        raise ValueError("ordinary Taylor reversion requires a[1] != 0")
    h = [Fraction(0)] * (order + 1)
    h[1] = 1 / a[1]
    for n in range(2, order + 1):
        residual = Fraction(0)
        for k in range(2, n + 1):
            if a[k] != 0:
                residual += a[k] * series_pow(h, k, n)[n]
        h[n] = -residual / a[1]
    return h


def revert_series_newton(coeffs: Sequence, order: int) -> list[Fraction]:
    """Formal Newton iteration H <- H - (F(H)-z)/F'(H)."""
    a = pad(coeffs, order)
    status, _ = classify_invertibility(a)
    if status != "regular":
        raise ValueError("formal Newton reversion requires a[1] != 0")
    h = [Fraction(0)] * (order + 1)
    h[1] = 1 / a[1]
    precision = 1
    identity = [Fraction(0)] * (order + 1)
    identity[1] = 1
    while precision < order:
        target = min(order, 2 * precision)
        error = series_sub(series_compose(a, h, target), identity, target)
        fp_of_h = series_compose(series_derivative(a), h, target)
        correction = series_mul(error, series_reciprocal(fp_of_h, target), target)
        h[: target + 1] = series_sub(h[: target + 1], correction, target)
        precision = target
    return h


def inverse_derivative_jet(inverse_coeffs: Sequence) -> list[Fraction]:
    return [as_q(c) * math.factorial(n) for n, c in enumerate(inverse_coeffs)]


def validate_reversion(forward: Sequence, inverse: Sequence, order: int) -> dict:
    identity = [Fraction(0)] * (order + 1)
    identity[1] = 1
    left = series_sub(series_compose(forward, inverse, order), identity, order)
    right = series_sub(series_compose(inverse, forward, order), identity, order)
    return {
        "left_residual": [qstr(x) for x in left],
        "right_residual": [qstr(x) for x in right],
        "left_exact_through_order": all(x == 0 for x in left),
        "right_exact_through_order": all(x == 0 for x in right),
    }


def solve_linear_square(matrix: Sequence[Sequence], rhs: Sequence) -> list[Fraction] | None:
    rows = [[as_q(x) for x in row] + [as_q(b)] for row, b in zip(matrix, rhs)]
    if not rows:
        return []
    n = len(rows[0]) - 1
    if len(rows) != n:
        return None
    for col in range(n):
        pivot = next((r for r in range(col, n) if rows[r][col] != 0), None)
        if pivot is None:
            return None
        rows[col], rows[pivot] = rows[pivot], rows[col]
        p = rows[col][col]
        rows[col] = [x / p for x in rows[col]]
        for r in range(n):
            if r != col and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [rows[r][j] - factor * rows[col][j] for j in range(n + 1)]
    return [rows[i][-1] for i in range(n)]


def pade(coeffs: Sequence, numerator_degree: int, denominator_degree: int) -> tuple[list[Fraction], list[Fraction]] | None:
    m, n = numerator_degree, denominator_degree
    if m < 0 or n < 0:
        raise ValueError("Padé degrees must be nonnegative")
    c = pad(coeffs, m + n)
    if n == 0:
        return c[: m + 1], [Fraction(1)]
    matrix, rhs = [], []
    for k in range(m + 1, m + n + 1):
        matrix.append([c[k - j] for j in range(1, n + 1)])
        rhs.append(-c[k])
    q_tail = solve_linear_square(matrix, rhs)
    if q_tail is None:
        return None
    q_coeffs = [Fraction(1)] + q_tail
    p_coeffs = []
    for k in range(m + 1):
        p_coeffs.append(sum(q_coeffs[j] * c[k - j] for j in range(0, min(k, n) + 1)))
    return p_coeffs, q_coeffs


def series_divide(numerator: Sequence, denominator: Sequence, order: int) -> list[Fraction]:
    return series_mul(numerator, series_reciprocal(denominator, order), order)


def guess_rational(coeffs: Sequence, max_degree: int = 4) -> dict | None:
    c = [as_q(x) for x in coeffs]
    order = len(c) - 1
    for complexity in range(1, 2 * max_degree + 1):
        for n in range(1, max_degree + 1):
            m = complexity - n
            if m < 0 or m > max_degree or m + n + 3 > order:
                continue
            candidate = pade(c, m, n)
            if candidate is None:
                continue
            p, q = candidate
            if series_divide(p, q, order) == c:
                return {
                    "numerator_degree": m,
                    "denominator_degree": n,
                    "numerator": [qstr(x) for x in p],
                    "denominator": [qstr(x) for x in q],
                    "validated_coefficients": order + 1,
                    "status": "finite-series candidate; identity still requires proof",
                }
    return None


def nullspace_vector(matrix: Sequence[Sequence]) -> list[Fraction] | None:
    a = [[as_q(x) for x in row] for row in matrix]
    if not a:
        return None
    rows, cols = len(a), len(a[0])
    r, pivots = 0, []
    for col in range(cols):
        pivot = next((i for i in range(r, rows) if a[i][col] != 0), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        p = a[r][col]
        a[r] = [x / p for x in a[r]]
        for i in range(rows):
            if i != r and a[i][col] != 0:
                factor = a[i][col]
                a[i] = [a[i][j] - factor * a[r][j] for j in range(cols)]
        pivots.append(col)
        r += 1
        if r == rows:
            break
    free = [c for c in range(cols) if c not in pivots]
    if not free:
        return None
    free_col = free[-1]
    x = [Fraction(0)] * cols
    x[free_col] = 1
    for rr in range(len(pivots) - 1, -1, -1):
        pc = pivots[rr]
        x[pc] = -sum(a[rr][j] * x[j] for j in free if a[rr][j] != 0)
    lcm = 1
    for value in x:
        lcm = math.lcm(lcm, value.denominator)
    ints = [int(value * lcm) for value in x]
    gcd = 0
    for value in ints:
        gcd = math.gcd(gcd, abs(value))
    if gcd:
        ints = [value // gcd for value in ints]
    first = next((value for value in ints if value != 0), 1)
    if first < 0:
        ints = [-value for value in ints]
    return [Fraction(value) for value in ints]


def guess_algebraic_relation(coeffs: Sequence, max_z_degree: int = 2, max_w_degree: int = 3) -> dict | None:
    """Guess P(z,w)=0 from a finite inverse series w=H(z); never a proof."""
    h = [as_q(x) for x in coeffs]
    order = len(h) - 1
    powers = [series_pow(h, j, order) for j in range(max_w_degree + 1)]
    for dw in range(1, max_w_degree + 1):
        for dz in range(max_z_degree + 1):
            terms = [(i, j) for j in range(dw + 1) for i in range(dz + 1)]
            unknowns = len(terms)
            if order + 1 < unknowns + 2:
                continue
            matrix = []
            for k in range(unknowns - 1):
                matrix.append([powers[j][k - i] if k >= i else Fraction(0) for i, j in terms])
            vector = nullspace_vector(matrix)
            if vector is None:
                continue
            residual = [Fraction(0)] * (order + 1)
            for coefficient, (i, j) in zip(vector, terms):
                if coefficient == 0:
                    continue
                for k in range(i, order + 1):
                    residual[k] += coefficient * powers[j][k - i]
            if all(value == 0 for value in residual):
                return {
                    "terms": [
                        {"z_degree": i, "w_degree": j, "coefficient": qstr(c)}
                        for c, (i, j) in zip(vector, terms) if c != 0
                    ],
                    "validated_through_series_order": order,
                    "status": "finite-series algebraic candidate; not an analytic proof",
                }
    return None


def guess_rational_coefficient_ratio(coeffs: Sequence, max_degree: int = 2) -> dict | None:
    """Guess b[n+1]/b[n] = P(n)/Q(n) for consecutive nonzero coefficients."""
    c = [as_q(x) for x in coeffs]
    points = [
        (Fraction(n), c[n + 1] / c[n])
        for n in range(1, len(c) - 1)
        if c[n] != 0 and c[n + 1] != 0
    ]
    for dp in range(max_degree + 1):
        for dq in range(max_degree + 1):
            terms = (dp + 1) + (dq + 1)
            if len(points) < terms + 1:
                continue
            matrix = []
            for n, ratio in points[: terms - 1]:
                matrix.append([n**i for i in range(dp + 1)] + [-ratio * n**j for j in range(dq + 1)])
            vector = nullspace_vector(matrix)
            if vector is None:
                continue
            p, q = vector[: dp + 1], vector[dp + 1 :]
            if all(value == 0 for value in q):
                continue

            def evaluate(poly: Sequence[Fraction], n: Fraction) -> Fraction:
                return sum(poly[i] * n**i for i in range(len(poly)))

            if all(evaluate(q, n) != 0 and evaluate(p, n) == ratio * evaluate(q, n) for n, ratio in points):
                return {
                    "P": [qstr(x) for x in p],
                    "Q": [qstr(x) for x in q],
                    "samples": len(points),
                    "meaning": "b[n+1]/b[n] = P(n)/Q(n) on all tested consecutive nonzero coefficients",
                    "status": "finite-sequence candidate; not a proof",
                }
    return None


def polynomial_eval(coeffs: Sequence, x: complex) -> complex:
    value = 0j
    for c in reversed(coeffs):
        coefficient = c if isinstance(c, complex) else complex(float(as_q(c)))
        value = value * x + coefficient
    return value


def polynomial_roots(coeffs: Sequence, max_iter: int = 500, tol: float = 1e-12) -> list[complex]:
    data = [complex(float(as_q(c))) for c in coeffs]
    while len(data) > 1 and abs(data[-1]) < tol:
        data.pop()
    degree = len(data) - 1
    if degree <= 0:
        return []
    lead = data[-1]
    data = [c / lead for c in data]
    if degree == 1:
        return [-data[0]]
    if degree == 2:
        disc = data[1] ** 2 - 4 * data[0]
        root = cmath.sqrt(disc)
        return [(-data[1] + root) / 2, (-data[1] - root) / 2]
    radius = 1.0 + max(abs(c) for c in data[:-1])
    roots = [radius * cmath.exp(2j * math.pi * k / degree) for k in range(degree)]
    for _ in range(max_iter):
        updated = []
        max_delta = 0.0
        for i, root in enumerate(roots):
            denom = 1 + 0j
            for j, other in enumerate(roots):
                if i != j:
                    denom *= root - other
            if abs(denom) < tol:
                root += complex(tol, tol)
                denom = 1 + 0j
                for j, other in enumerate(roots):
                    if i != j:
                        denom *= root - other
            delta = polynomial_eval(data, root) / denom
            new_root = root - delta
            updated.append(new_root)
            max_delta = max(max_delta, abs(delta))
        roots = updated
        if max_delta < tol:
            break
    return roots


def critical_point_analysis(coeffs: Sequence) -> dict:
    points = polynomial_roots(series_derivative(coeffs))
    rows = []
    for x in points:
        y = polynomial_eval(coeffs, x)
        rows.append({"x": cdict(x), "critical_value": cdict(y), "abs_critical_value": abs(y)})
    positive = [row["abs_critical_value"] for row in rows if row["abs_critical_value"] > 1e-12]
    return {
        "critical_points_of_truncated_polynomial": rows,
        "critical_value_radius_proxy": min(positive) if positive else None,
        "warning": "Proxy uses only the supplied truncated polynomial; singularities/asymptotic values of the original function may dominate.",
    }


def complex_series_mul(a: Sequence[complex], b: Sequence[complex], order: int) -> list[complex]:
    aa = (list(a) + [0j] * max(0, order + 1 - len(a)))[: order + 1]
    bb = (list(b) + [0j] * max(0, order + 1 - len(b)))[: order + 1]
    out = [0j] * (order + 1)
    for i, ai in enumerate(aa):
        if ai == 0:
            continue
        for j in range(order + 1 - i):
            out[i + j] += ai * bb[j]
    return out


def complex_series_pow(a: Sequence[complex], exponent: int, order: int) -> list[complex]:
    out = [1 + 0j] + [0j] * order
    base = (list(a) + [0j] * max(0, order + 1 - len(a)))[: order + 1]
    k = exponent
    while k:
        if k & 1:
            out = complex_series_mul(out, base, order)
        base = complex_series_mul(base, base, order)
        k //= 2
    return out


def puiseux_branches(coeffs: Sequence, requested_terms: int = 6) -> dict:
    """Numeric Puiseux branches h(t), z=t**m, for a critical truncated series."""
    a_q = [as_q(x) for x in coeffs]
    status, multiplicity = classify_invertibility(a_q)
    if status != "critical" or multiplicity is None:
        raise ValueError("Puiseux mode requires first nonzero degree m > 1")
    m = multiplicity
    reliable_terms = min(requested_terms, len(a_q) - 1 - m + 1)
    reliable_terms = max(1, reliable_terms)
    a = [complex(float(x)) for x in a_q]
    am = a[m]
    principal = cmath.exp(cmath.log(1 / am) / m)
    branches = []
    for branch_index in range(m):
        c1 = principal * cmath.exp(2j * math.pi * branch_index / m)
        h = [0j] * (reliable_terms + 1)
        h[1] = c1
        denominator = m * am * c1 ** (m - 1)
        for k in range(2, reliable_terms + 1):
            target_degree = m + k - 1
            hh = h + [0j] * max(0, target_degree + 1 - len(h))
            residual = 0j
            for degree in range(m, min(len(a), target_degree + 1)):
                if a[degree] != 0:
                    residual += a[degree] * complex_series_pow(hh, degree, target_degree)[target_degree]
            h[k] = -residual / denominator
        branches.append({
            "branch": branch_index,
            "parameterization": f"z=t^{m}; h=sum(c_k t^k)",
            "coefficients_c_k": [cdict(value) for value in h],
        })
    return {
        "multiplicity": m,
        "branches": branches,
        "reliable_terms_from_supplied_truncation": reliable_terms,
        "warning": "Numeric Puiseux expansion of the supplied truncated polynomial; branch/global claims require separate analytic validation.",
    }


def default_pade_approximant(coeffs: Sequence) -> dict | None:
    order = len(coeffs) - 1
    if order < 2:
        return None
    denominator_degree = max(1, order // 2)
    numerator_degree = order - denominator_degree
    candidate = pade(coeffs, numerator_degree, denominator_degree)
    if candidate is None:
        return None
    p, q = candidate
    return {
        "numerator_degree": numerator_degree,
        "denominator_degree": denominator_degree,
        "numerator": [qstr(x) for x in p],
        "denominator": [qstr(x) for x in q],
        "matched_through_order": numerator_degree + denominator_degree,
        "status": "Padé approximant; poles are not automatically true singularities.",
    }


@dataclass(frozen=True)
class InverseCompilation:
    system_id: str
    x0: str
    y0: str
    order: int
    status: str
    multiplicity: int | None
    forward_coefficients: list[str]
    inverse_coefficients: list[str] | None
    inverse_derivative_jet: list[str] | None
    local_absolute_condition_number: float | None
    direct_newton_agreement: bool | None
    validation: dict | None
    pade_approximant: dict | None
    rational_candidate: dict | None
    algebraic_candidate: dict | None
    coefficient_ratio_candidate: dict | None
    critical_analysis: dict
    puiseux: dict | None
    oak_warnings: list[str]
    m_minus: list[str]


def compile_inverse(
    coeffs: Sequence,
    order: int,
    x0: int | float | str | Fraction = 0,
    y0: int | float | str | Fraction = 0,
    system_id: str = "omega_inverse_custom_v0_1",
) -> InverseCompilation:
    if order < 1:
        raise ValueError("order must be >= 1")
    forward = pad(coeffs, order)
    status, multiplicity = classify_invertibility(forward)
    critical = critical_point_analysis(forward)
    warnings = [
        "Local series inversion does not prove global one-to-one behavior.",
        "Recognition outputs are hypotheses until symbolic/analytic proof.",
        "Convergence radius is controlled by inverse-branch singularities, not just real critical points.",
    ]
    m_minus = [
        "Do not equate Padé poles with proven singularities.",
        "Do not extrapolate a truncated-polynomial critical atlas to the original function without validation.",
    ]
    common = dict(
        system_id=system_id,
        x0=qstr(as_q(x0)),
        y0=qstr(as_q(y0)),
        order=order,
        status=status,
        multiplicity=multiplicity,
        forward_coefficients=[qstr(x) for x in forward],
        critical_analysis=critical,
        oak_warnings=warnings,
        m_minus=m_minus,
    )
    if status == "regular":
        inverse = revert_series(forward, order)
        inverse_newton = revert_series_newton(forward, order)
        return InverseCompilation(
            **common,
            inverse_coefficients=[qstr(x) for x in inverse],
            inverse_derivative_jet=[qstr(x) for x in inverse_derivative_jet(inverse)],
            local_absolute_condition_number=1.0 / abs(float(forward[1])),
            direct_newton_agreement=inverse == inverse_newton,
            validation=validate_reversion(forward, inverse, order),
            pade_approximant=default_pade_approximant(inverse),
            rational_candidate=guess_rational(inverse),
            algebraic_candidate=guess_algebraic_relation(inverse),
            coefficient_ratio_candidate=guess_rational_coefficient_ratio(inverse),
            puiseux=None,
        )
    if status == "critical":
        warnings.append("Ordinary Taylor inverse unavailable at the base point; using Puiseux branches.")
        return InverseCompilation(
            **common,
            inverse_coefficients=None,
            inverse_derivative_jet=None,
            local_absolute_condition_number=None,
            direct_newton_agreement=None,
            validation=None,
            pade_approximant=None,
            rational_candidate=None,
            algebraic_candidate=None,
            coefficient_ratio_candidate=None,
            puiseux=puiseux_branches(forward, requested_terms=min(8, order)),
        )
    warnings.append("No nonconstant term was supplied; no local inverse can be constructed.")
    return InverseCompilation(
        **common,
        inverse_coefficients=None,
        inverse_derivative_jet=None,
        local_absolute_condition_number=None,
        direct_newton_agreement=None,
        validation=None,
        pade_approximant=None,
        rational_candidate=None,
        algebraic_candidate=None,
        coefficient_ratio_candidate=None,
        puiseux=None,
    )


def preset_coefficients(name: str, order: int) -> list[Fraction]:
    out = [Fraction(0)] * (order + 1)
    if name == "quadratic":
        out[1] = 1
        if order >= 2:
            out[2] = 1
    elif name == "exp-minus-one":
        for n in range(1, order + 1):
            out[n] = Fraction(1, math.factorial(n))
    elif name == "lambert":
        for n in range(1, order + 1):
            out[n] = Fraction(1, math.factorial(n - 1))
    elif name == "sin":
        for n in range(1, order + 1, 2):
            out[n] = Fraction((-1) ** ((n - 1) // 2), math.factorial(n))
    elif name == "mobius":
        for n in range(1, order + 1):
            out[n] = 1
    elif name == "critical-square":
        if order < 2:
            raise ValueError("critical-square requires order >= 2")
        out[2] = 1
    else:
        raise ValueError(f"unsupported preset: {name}")
    return out


def parse_coefficients(text: str) -> list[Fraction]:
    return [as_q(token.strip()) for token in text.split(",") if token.strip()]


def markdown_report(report: InverseCompilation) -> str:
    rows = [
        "# Ω-INVERSE-T∞ report", "",
        f"- system: `{report.system_id}`",
        f"- status: `{report.status}`",
        f"- order: `{report.order}`",
        f"- x0: `{report.x0}`",
        f"- y0: `{report.y0}`",
        f"- multiplicity: `{report.multiplicity}`", "",
        "## Forward local Taylor coefficients", "",
        "`[" + ", ".join(report.forward_coefficients) + "]`", "",
    ]
    if report.inverse_coefficients is not None:
        rows += [
            "## Inverse Taylor coefficients", "",
            "`[" + ", ".join(report.inverse_coefficients) + "]`", "",
            f"- direct/Newton formal reversion agree: `{report.direct_newton_agreement}`",
            f"- local absolute condition number: `{report.local_absolute_condition_number}`",
            f"- left composition exact through order: `{report.validation['left_exact_through_order']}`",
            f"- right composition exact through order: `{report.validation['right_exact_through_order']}`", "",
        ]
    if report.puiseux is not None:
        rows += ["## Puiseux branches", "", f"- multiplicity: `{report.puiseux['multiplicity']}`", ""]
        for branch in report.puiseux["branches"]:
            rows.append(f"- branch {branch['branch']}: `{branch['coefficients_c_k']}`")
        rows.append("")
    rows += [
        "## Recognition candidates", "",
        f"- Padé: `{report.pade_approximant}`",
        f"- rational: `{report.rational_candidate}`",
        f"- algebraic: `{report.algebraic_candidate}`",
        f"- coefficient ratio: `{report.coefficient_ratio_candidate}`", "",
        "## OAK boundary", "",
    ]
    rows += [f"- {item}" for item in report.oak_warnings]
    rows += ["", "## M-minus", ""]
    rows += [f"- {item}" for item in report.m_minus]
    return "\n".join(rows) + "\n"


def write_report(report: InverseCompilation, json_path: Path | None, markdown_path: Path | None) -> None:
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown_report(report), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω-INVERSE-T∞ local inverse-series compiler")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--preset", choices=["quadratic", "exp-minus-one", "lambert", "sin", "mobius", "critical-square"])
    source.add_argument("--coefficients", help="comma-separated local Taylor coefficients a0,a1,...; rationals like 1/6 supported")
    parser.add_argument("--order", type=int, default=8)
    parser.add_argument("--x0", default="0")
    parser.add_argument("--y0", default="0")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.preset:
        coeffs = preset_coefficients(args.preset, args.order)
        system_id = f"omega_inverse_{args.preset.replace('-', '_')}_v0_1"
    else:
        coeffs = parse_coefficients(args.coefficients)
        system_id = "omega_inverse_custom_v0_1"
    report = compile_inverse(coeffs, args.order, x0=args.x0, y0=args.y0, system_id=system_id)
    write_report(report, args.output, args.markdown_output)
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
