"""Dependency-free symbolic Hankel/TensorProdLift compiler for R10.

Let A(u)=Theta(u)/Theta(0)=1+a_1 u+a_2 u^2+... . Newton identities
express reciprocal-zero power sums p_k in the elementary coefficients a_j.
R10 says RH is equivalent to PSD of all basic/shifted Hankel matrices built from
m_k=p_{k+1}. Each finite determinant is therefore a polynomial inequality in
the a_j, and becomes a linear functional after monomial TensorProdLift.

This module compiles those finite polynomial constraints exactly. It does not
establish their non-negativity and never proves RH.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations
from typing import Iterable, Mapping

Exponent = tuple[int, ...]
Polynomial = dict[Exponent, Fraction]


def _zero(nvars: int) -> Exponent:
    return (0,) * nvars


def _clean(poly: Polynomial) -> Polynomial:
    return {exp: coeff for exp, coeff in poly.items() if coeff}


def constant(value: int | Fraction, nvars: int) -> Polynomial:
    q = value if isinstance(value, Fraction) else Fraction(value)
    return {} if q == 0 else {_zero(nvars): q}


def variable(index: int, nvars: int) -> Polynomial:
    """Return a_(index+1), where index is zero-based."""
    if not 0 <= index < nvars:
        raise ValueError("variable index out of range")
    exp = [0] * nvars
    exp[index] = 1
    return {tuple(exp): Fraction(1)}


def add(left: Polynomial, right: Polynomial) -> Polynomial:
    out = dict(left)
    for exp, coeff in right.items():
        out[exp] = out.get(exp, Fraction(0)) + coeff
    return _clean(out)


def scale(poly: Polynomial, factor: int | Fraction) -> Polynomial:
    q = factor if isinstance(factor, Fraction) else Fraction(factor)
    return _clean({exp: q * coeff for exp, coeff in poly.items()})


def multiply(left: Polynomial, right: Polynomial) -> Polynomial:
    if not left or not right:
        return {}
    nvars = len(next(iter(left)))
    if any(len(exp) != nvars for exp in right):
        raise ValueError("polynomial variable dimensions do not match")
    out: Polynomial = {}
    for exp_l, coeff_l in left.items():
        for exp_r, coeff_r in right.items():
            exp = tuple(a + b for a, b in zip(exp_l, exp_r))
            out[exp] = out.get(exp, Fraction(0)) + coeff_l * coeff_r
    return _clean(out)


def newton_power_sum_polynomials(max_k: int) -> list[Polynomial]:
    """Return p_1,...,p_max_k in variables a_1,...,a_max_k.

    For A(u)=prod_j(1+lambda_j u)=sum e_k u^k, a_k=e_k and

      p_k = a1 p_(k-1) - a2 p_(k-2) + ...
            + (-1)^k a_(k-1) p1 + (-1)^(k-1) k a_k.
    """
    if not isinstance(max_k, int) or max_k < 1:
        raise ValueError("max_k must be a positive integer")
    nvars = max_k
    a = [variable(i, nvars) for i in range(nvars)]
    p: list[Polynomial] = []
    for k in range(1, max_k + 1):
        value: Polynomial = {}
        for j in range(1, k):
            term = multiply(a[j - 1], p[k - j - 1])
            value = add(value, scale(term, 1 if j % 2 else -1))
        value = add(value, scale(a[k - 1], k if k % 2 else -k))
        p.append(value)
    return p


def _permutation_sign(perm: tuple[int, ...]) -> int:
    inversions = sum(
        1
        for i in range(len(perm))
        for j in range(i + 1, len(perm))
        if perm[i] > perm[j]
    )
    return -1 if inversions % 2 else 1


def determinant_polynomial(matrix: list[list[Polynomial]]) -> Polynomial:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    if n > 5:
        raise ValueError("symbolic determinant capped at size 5 to control combinatorial growth")
    first_nonzero = next((poly for row in matrix for poly in row if poly), None)
    if first_nonzero is None:
        return {}
    nvars = len(next(iter(first_nonzero)))
    total: Polynomial = {}
    for perm in permutations(range(n)):
        term = constant(1, nvars)
        for row, col in enumerate(perm):
            term = multiply(term, matrix[row][col])
        total = add(total, scale(term, _permutation_sign(perm)))
    return _clean(total)


@dataclass(frozen=True)
class TensorLiftTerm:
    coefficient: Fraction
    exponents: Exponent

    @property
    def total_degree(self) -> int:
        return sum(self.exponents)

    @property
    def monomial(self) -> str:
        factors: list[str] = []
        for index, power in enumerate(self.exponents, start=1):
            if power == 1:
                factors.append(f"a{index}")
            elif power > 1:
                factors.append(f"a{index}^{power}")
        return "*".join(factors) if factors else "1"


@dataclass(frozen=True)
class HankelPolynomialConstraint:
    size: int
    shift: int
    max_power_sum: int
    terms: tuple[TensorLiftTerm, ...]
    relation: str = ">= 0"
    epistemic_status: str = "EXACT_FINITE_CONSTRAINT_COMPILER_ONLY"
    proves_rh: bool = False

    @property
    def term_count(self) -> int:
        return len(self.terms)

    @property
    def max_total_degree(self) -> int:
        return max((term.total_degree for term in self.terms), default=0)


def hankel_determinant_polynomial(size: int, shift: int = 0) -> Polynomial:
    """Compile det H_size^(shift) as a polynomial in normalized Theta a_j."""
    if not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    if not isinstance(shift, int) or shift < 0:
        raise ValueError("shift must be a non-negative integer")
    if size > 5:
        raise ValueError("symbolic Hankel compiler capped at size 5")
    max_p = 2 * size - 1 + shift
    p = newton_power_sum_polynomials(max_p)
    matrix = [
        [p[i + j + shift] for j in range(size)]
        for i in range(size)
    ]
    return determinant_polynomial(matrix)


def tensor_lift_constraint(size: int, shift: int = 0) -> HankelPolynomialConstraint:
    poly = hankel_determinant_polynomial(size, shift)
    terms = tuple(
        TensorLiftTerm(coeff, exp)
        for exp, coeff in sorted(poly.items(), key=lambda item: (sum(item[0]), item[0]))
    )
    return HankelPolynomialConstraint(
        size=size,
        shift=shift,
        max_power_sum=2 * size - 1 + shift,
        terms=terms,
    )


def evaluate_polynomial(poly: Mapping[Exponent, Fraction], values: Iterable[int | Fraction]) -> Fraction:
    vals = tuple(v if isinstance(v, Fraction) else Fraction(v) for v in values)
    out = Fraction(0)
    for exp, coeff in poly.items():
        if len(exp) > len(vals):
            raise ValueError("not enough coefficient values")
        term = coeff
        for value, power in zip(vals, exp):
            term *= value**power
        out += term
    return out
