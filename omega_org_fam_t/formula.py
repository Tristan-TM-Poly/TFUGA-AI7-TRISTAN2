"""Exact molecular-formula parsing and reaction-balance utilities.

The module performs bookkeeping only. A balanced equation is not evidence that a
reaction occurs, is selective, safe, or experimentally feasible.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from math import gcd
import re
from typing import Iterable, Mapping, Sequence

_TOKEN = re.compile(r"([A-Z][a-z]?|\(|\)|\d+|\[\d+[A-Z][a-z]?\])")


@dataclass(frozen=True, slots=True)
class Species:
    formula: str
    charge: int = 0

    @property
    def composition(self) -> dict[str, int]:
        return parse_formula(self.formula)


def _lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b) if a and b else 0


def parse_formula(formula: str) -> dict[str, int]:
    """Parse a conventional molecular formula with nested parentheses.

    Isotope labels such as ``[13C]`` are retained as separate element keys.
    Hydrate/adduct separators and structural notation are intentionally rejected.
    """
    text = formula.strip()
    if not text:
        raise ValueError("formula is empty")
    if text in {"e", "e-", "electron"}:
        return {}
    tokens = _TOKEN.findall(text)
    if "".join(tokens) != text:
        raise ValueError(f"unsupported formula syntax: {formula!r}")
    stack: list[defaultdict[str, int]] = [defaultdict(int)]
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "(":
            stack.append(defaultdict(int))
            index += 1
            continue
        if token == ")":
            if len(stack) == 1:
                raise ValueError("unmatched closing parenthesis")
            group = stack.pop()
            multiplier = 1
            if index + 1 < len(tokens) and tokens[index + 1].isdigit():
                multiplier = int(tokens[index + 1])
                index += 1
            if multiplier <= 0:
                raise ValueError("formula multipliers must be positive")
            for element, count in group.items():
                stack[-1][element] += multiplier * count
            index += 1
            continue
        if token.isdigit():
            raise ValueError("a multiplier must follow an element or parenthesized group")
        element = token[1:-1] if token.startswith("[") else token
        multiplier = 1
        if index + 1 < len(tokens) and tokens[index + 1].isdigit():
            multiplier = int(tokens[index + 1])
            index += 1
        if multiplier <= 0:
            raise ValueError("formula multipliers must be positive")
        stack[-1][element] += multiplier
        index += 1
    if len(stack) != 1:
        raise ValueError("unmatched opening parenthesis")
    return dict(sorted(stack[0].items()))


def reaction_residual(
    reactants: Iterable[tuple[int, Species]],
    products: Iterable[tuple[int, Species]],
) -> dict[str, int]:
    residual: defaultdict[str, int] = defaultdict(int)
    for sign, side in ((-1, reactants), (1, products)):
        for coefficient, species in side:
            if coefficient <= 0:
                raise ValueError("stoichiometric coefficients must be positive")
            for element, count in species.composition.items():
                residual[element] += sign * coefficient * count
            residual["__charge__"] += sign * coefficient * species.charge
    return {key: value for key, value in sorted(residual.items()) if value != 0}


def is_balanced(
    reactants: Iterable[tuple[int, Species]],
    products: Iterable[tuple[int, Species]],
) -> bool:
    return not reaction_residual(reactants, products)


def _rref(matrix: list[list[Fraction]]) -> tuple[list[list[Fraction]], list[int]]:
    if not matrix:
        return matrix, []
    rows, cols = len(matrix), len(matrix[0])
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(cols):
        row = next((r for r in range(pivot_row, rows) if matrix[r][column]), None)
        if row is None:
            continue
        matrix[pivot_row], matrix[row] = matrix[row], matrix[pivot_row]
        pivot = matrix[pivot_row][column]
        matrix[pivot_row] = [value / pivot for value in matrix[pivot_row]]
        for r in range(rows):
            if r == pivot_row:
                continue
            factor = matrix[r][column]
            if factor:
                matrix[r] = [a - factor * b for a, b in zip(matrix[r], matrix[pivot_row], strict=True)]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break
    return matrix, pivot_columns


def balance_reaction(
    reactants: Sequence[Species],
    products: Sequence[Species],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Return the smallest positive integer coefficients for a 1-D nullspace.

    Raises ``ValueError`` for underdetermined, impossible, or sign-inconsistent
    systems rather than choosing an arbitrary chemistry.
    """
    species = tuple(reactants) + tuple(products)
    if not reactants or not products:
        raise ValueError("both reaction sides are required")
    compositions = [item.composition for item in species]
    elements = sorted({element for comp in compositions for element in comp})
    rows: list[list[Fraction]] = []
    for element in elements:
        row = []
        for index, comp in enumerate(compositions):
            sign = 1 if index < len(reactants) else -1
            row.append(Fraction(sign * comp.get(element, 0)))
        rows.append(row)
    charge_row = [
        Fraction((1 if index < len(reactants) else -1) * item.charge)
        for index, item in enumerate(species)
    ]
    if any(charge_row):
        rows.append(charge_row)
    reduced, pivots = _rref([row[:] for row in rows])
    free = [column for column in range(len(species)) if column not in pivots]
    if len(free) != 1:
        raise ValueError(f"reaction has nullity {len(free)}; exactly one free scale is required")
    vector = [Fraction(0) for _ in species]
    vector[free[0]] = Fraction(1)
    for row_index in range(len(pivots) - 1, -1, -1):
        pivot = pivots[row_index]
        vector[pivot] = -sum(
            reduced[row_index][column] * vector[column]
            for column in range(pivot + 1, len(species))
        )
    if all(value < 0 for value in vector):
        vector = [-value for value in vector]
    if any(value <= 0 for value in vector):
        raise ValueError("no strictly positive stoichiometric solution")
    denominator_lcm = 1
    for value in vector:
        denominator_lcm = _lcm(denominator_lcm, value.denominator)
    integers = [int(value * denominator_lcm) for value in vector]
    common = 0
    for value in integers:
        common = gcd(common, abs(value))
    integers = [value // common for value in integers]
    left = tuple(integers[: len(reactants)])
    right = tuple(integers[len(reactants) :])
    if not is_balanced(zip(left, reactants, strict=True), zip(right, products, strict=True)):
        raise ArithmeticError("internal balancing failure")
    return left, right


def residual_from_mappings(
    reactants: Mapping[str, int], products: Mapping[str, int]
) -> dict[str, int]:
    """Convenience wrapper for neutral species keyed by formula."""
    return reaction_residual(
        ((coefficient, Species(formula)) for formula, coefficient in reactants.items()),
        ((coefficient, Species(formula)) for formula, coefficient in products.items()),
    )
