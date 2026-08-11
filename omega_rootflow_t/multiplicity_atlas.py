"""Exact global multiplicity atlas for Ω-ROOTFLOW-T∞ R0.9.

R0.7/R0.8 analyze a supplied multiple root locally. R0.9 adds a global exact
view over Q without numerically solving for the roots.

For P of degree n, define the derivative-gcd tower

    G_q = gcd(P, P', ..., P^(q)), q=0,...,n.

If the complex roots have multiplicities m_i, then

    deg G_q = sum_i max(m_i-q, 0).

Therefore

    N_{>=q} = deg G_(q-1) - deg G_q

is the exact number of distinct complex roots whose multiplicity is at least q,
and

    N_{=q} = N_{>=q} - N_{>=q+1}

reconstructs the multiplicity partition. This counts algebraic roots over C;
irreducible rational factors contribute their degree.

The module also implements exact characteristic-zero square-free decomposition
(Yun-style gcd decomposition) and a combinatorial adjacency model of complex
multiplicity partitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Iterator

from .exact import ExactPolynomial, ExactScalar, exact_coefficients, exact_monic_gcd, exact_polydivmod


def _trim(values: Iterable[Fraction]) -> ExactPolynomial:
    coeffs = tuple(values)
    if not coeffs:
        return (Fraction(0),)
    last = len(coeffs) - 1
    while last > 0 and coeffs[last] == 0:
        last -= 1
    return coeffs[: last + 1]


def _degree(polynomial: ExactPolynomial) -> int:
    p = _trim(polynomial)
    return len(p) - 1 if not (len(p) == 1 and p[0] == 0) else -1


def _is_one(polynomial: ExactPolynomial) -> bool:
    p = _trim(polynomial)
    return len(p) == 1 and p[0] == 1


def _monic(polynomial: ExactPolynomial) -> ExactPolynomial:
    p = _trim(polynomial)
    if len(p) == 1 and p[0] == 0:
        return p
    return tuple(value / p[-1] for value in p)


def _derivative_any(polynomial: ExactPolynomial) -> ExactPolynomial:
    p = _trim(polynomial)
    if len(p) <= 1:
        return (Fraction(0),)
    return _trim(Fraction(index) * p[index] for index in range(1, len(p)))


def _multiply(first: ExactPolynomial, second: ExactPolynomial) -> ExactPolynomial:
    a = _trim(first)
    b = _trim(second)
    if (len(a) == 1 and a[0] == 0) or (len(b) == 1 and b[0] == 0):
        return (Fraction(0),)
    result = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, left in enumerate(a):
        for j, right in enumerate(b):
            result[i + j] += left * right
    return _trim(result)


def _power(polynomial: ExactPolynomial, exponent: int) -> ExactPolynomial:
    if exponent < 0:
        raise ValueError("exponent must be non-negative")
    result: ExactPolynomial = (Fraction(1),)
    base = _trim(polynomial)
    power = exponent
    while power:
        if power & 1:
            result = _multiply(result, base)
        base = _multiply(base, base)
        power >>= 1
    return result


def _divide_exact(dividend: ExactPolynomial, divisor: ExactPolynomial) -> ExactPolynomial:
    quotient, remainder = exact_polydivmod(dividend, divisor)
    if not (len(remainder) == 1 and remainder[0] == 0):
        raise ArithmeticError("expected exact polynomial division")
    return _trim(quotient)


def derivative_gcd_tower(coefficients: Iterable[ExactScalar]) -> tuple[ExactPolynomial, ...]:
    """Return monic G_q=gcd(P,...,P^(q)) for q=0,...,degree."""
    polynomial = exact_coefficients(coefficients)
    degree = len(polynomial) - 1
    current_gcd = _monic(polynomial)
    derivative = polynomial
    tower: list[ExactPolynomial] = [current_gcd]
    for _order in range(1, degree + 1):
        derivative = _derivative_any(derivative)
        current_gcd = exact_monic_gcd(current_gcd, derivative)
        tower.append(_monic(current_gcd))
    return tuple(tower)


@dataclass(frozen=True)
class SquareFreeFactor:
    multiplicity: int
    coefficients: ExactPolynomial
    degree: int

    def to_dict(self) -> dict[str, object]:
        return {
            "multiplicity": self.multiplicity,
            "degree": self.degree,
            "coefficients": [_fraction_text(value) for value in self.coefficients],
        }


def square_free_decomposition(coefficients: Iterable[ExactScalar]) -> tuple[SquareFreeFactor, ...]:
    """Exact square-free decomposition over Q in characteristic zero.

    Returned factors are monic, pairwise coprime and tagged by root
    multiplicity. The input leading coefficient is intentionally external to
    the factor list and is restored by the audit reconstruction.
    """
    polynomial = exact_coefficients(coefficients)
    monic = _monic(polynomial)
    derivative = _derivative_any(monic)
    repeated = exact_monic_gcd(monic, derivative)
    square_free_part = _divide_exact(monic, repeated)

    factors: list[SquareFreeFactor] = []
    multiplicity = 1
    w = square_free_part
    c = repeated
    while not _is_one(w):
        y = exact_monic_gcd(w, c)
        z = _monic(_divide_exact(w, y))
        if _degree(z) > 0:
            factors.append(SquareFreeFactor(multiplicity, z, _degree(z)))
        w = _monic(y)
        c = _monic(_divide_exact(c, y))
        multiplicity += 1
    return tuple(factors)


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _polynomial_text(polynomial: ExactPolynomial) -> list[str]:
    return [_fraction_text(value) for value in polynomial]


@dataclass(frozen=True)
class ExactMultiplicityAtlas:
    degree: int
    leading_coefficient: Fraction
    gcd_tower: tuple[ExactPolynomial, ...]
    gcd_degrees: tuple[int, ...]
    at_least_multiplicity_counts: tuple[int, ...]
    exact_multiplicity_counts: tuple[int, ...]
    multiplicity_partition: tuple[int, ...]
    distinct_root_count_over_c: int
    complex_stratum_codimension: int
    square_free_factors: tuple[SquareFreeFactor, ...]
    reconstruction_matches: bool
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "degree": self.degree,
            "leading_coefficient": _fraction_text(self.leading_coefficient),
            "gcd_tower": [_polynomial_text(item) for item in self.gcd_tower],
            "gcd_degrees": list(self.gcd_degrees),
            "at_least_multiplicity_counts": list(self.at_least_multiplicity_counts),
            "exact_multiplicity_counts": list(self.exact_multiplicity_counts),
            "multiplicity_partition": list(self.multiplicity_partition),
            "distinct_root_count_over_c": self.distinct_root_count_over_c,
            "complex_stratum_codimension": self.complex_stratum_codimension,
            "square_free_factors": [factor.to_dict() for factor in self.square_free_factors],
            "reconstruction_matches": self.reconstruction_matches,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def exact_multiplicity_atlas(coefficients: Iterable[ExactScalar]) -> ExactMultiplicityAtlas:
    polynomial = exact_coefficients(coefficients)
    degree = len(polynomial) - 1
    leading = polynomial[-1]
    tower = derivative_gcd_tower(polynomial)
    degrees = tuple(max(_degree(item), 0) for item in tower)

    at_least = [degrees[q - 1] - degrees[q] for q in range(1, degree + 1)]
    exact_counts = [
        at_least[q - 1] - (at_least[q] if q < degree else 0)
        for q in range(1, degree + 1)
    ]
    partition: list[int] = []
    for multiplicity, count in enumerate(exact_counts, start=1):
        if count < 0:
            raise ArithmeticError("invalid negative multiplicity count from gcd tower")
        partition.extend([multiplicity] * count)
    partition_tuple = tuple(sorted(partition, reverse=True))

    factors = square_free_decomposition(polynomial)
    reconstructed: ExactPolynomial = (Fraction(1),)
    for factor in factors:
        reconstructed = _multiply(reconstructed, _power(factor.coefficients, factor.multiplicity))
    reconstructed = tuple(leading * value for value in reconstructed)
    reconstruction_matches = _trim(reconstructed) == _trim(polynomial)

    distinct = at_least[0] if at_least else degree
    codimension = degree - distinct
    partition_degree = sum(partition_tuple)
    factor_degree = sum(factor.degree * factor.multiplicity for factor in factors)
    passed = (
        reconstruction_matches
        and partition_degree == degree
        and factor_degree == degree
        and all(degrees[index] >= degrees[index + 1] for index in range(len(degrees) - 1))
        and degrees[-1] == 0
    )
    status = "OAK_PASS_EXACT_MULTIPLICITY_ATLAS" if passed else "OAK_FAIL_EXACT_MULTIPLICITY_ATLAS"
    return ExactMultiplicityAtlas(
        degree=degree,
        leading_coefficient=leading,
        gcd_tower=tower,
        gcd_degrees=degrees,
        at_least_multiplicity_counts=tuple(at_least),
        exact_multiplicity_counts=tuple(exact_counts),
        multiplicity_partition=partition_tuple,
        distinct_root_count_over_c=distinct,
        complex_stratum_codimension=codimension,
        square_free_factors=factors,
        reconstruction_matches=reconstruction_matches,
        status=status,
    )


def _normalize_partition(partition: Iterable[int]) -> tuple[int, ...]:
    values = tuple(sorted((int(value) for value in partition), reverse=True))
    if not values or any(value <= 0 for value in values):
        raise ValueError("partition must contain positive integers")
    return values


def immediate_more_singular(partition: Iterable[int]) -> tuple[tuple[int, ...], ...]:
    """Immediate partition neighbors obtained by merging two root clusters."""
    values = _normalize_partition(partition)
    neighbors: set[tuple[int, ...]] = set()
    for first in range(len(values)):
        for second in range(first + 1, len(values)):
            merged = [value for index, value in enumerate(values) if index not in (first, second)]
            merged.append(values[first] + values[second])
            neighbors.add(tuple(sorted(merged, reverse=True)))
    return tuple(sorted(neighbors, reverse=True))


def immediate_less_singular(partition: Iterable[int]) -> tuple[tuple[int, ...], ...]:
    """Immediate partition neighbors obtained by splitting one root cluster."""
    values = _normalize_partition(partition)
    neighbors: set[tuple[int, ...]] = set()
    for index, value in enumerate(values):
        if value < 2:
            continue
        for smaller in range(1, value // 2 + 1):
            larger = value - smaller
            split = [item for position, item in enumerate(values) if position != index]
            split.extend((larger, smaller))
            neighbors.add(tuple(sorted(split, reverse=True)))
    return tuple(sorted(neighbors, reverse=True))


@dataclass(frozen=True)
class PartitionNeighborhood:
    partition: tuple[int, ...]
    degree: int
    distinct_root_count: int
    complex_codimension: int
    more_singular: tuple[tuple[int, ...], ...]
    less_singular: tuple[tuple[int, ...], ...]
    status: str = "OAK_PASS_PARTITION_NEIGHBORHOOD"
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "partition": list(self.partition),
            "degree": self.degree,
            "distinct_root_count": self.distinct_root_count,
            "complex_codimension": self.complex_codimension,
            "more_singular": [list(item) for item in self.more_singular],
            "less_singular": [list(item) for item in self.less_singular],
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def partition_neighborhood(partition: Iterable[int]) -> PartitionNeighborhood:
    values = _normalize_partition(partition)
    degree = sum(values)
    distinct = len(values)
    return PartitionNeighborhood(
        partition=values,
        degree=degree,
        distinct_root_count=distinct,
        complex_codimension=degree - distinct,
        more_singular=immediate_more_singular(values),
        less_singular=immediate_less_singular(values),
    )


def integer_partitions(total: int, maximum: int | None = None) -> Iterator[tuple[int, ...]]:
    """Generate integer partitions in non-increasing order."""
    if total < 1:
        raise ValueError("total must be positive")
    upper = total if maximum is None else min(total, maximum)
    if total == 0:
        yield ()
        return
    for first in range(upper, 0, -1):
        if first == total:
            yield (first,)
        elif first < total:
            for tail in integer_partitions(total - first, first):
                yield (first,) + tail


@dataclass(frozen=True)
class PartitionLattice:
    degree: int
    nodes: tuple[tuple[int, ...], ...]
    edges_less_to_more_singular: tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "degree": self.degree,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges_less_to_more_singular),
            "nodes": [list(node) for node in self.nodes],
            "edges_less_to_more_singular": [
                {"from": list(source), "to": list(target)}
                for source, target in self.edges_less_to_more_singular
            ],
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def build_partition_lattice(degree: int, *, maximum_nodes: int | None = None) -> PartitionLattice:
    if degree < 1:
        raise ValueError("degree must be positive")
    if maximum_nodes is not None and maximum_nodes < 1:
        raise ValueError("maximum_nodes must be positive when supplied")
    nodes_list: list[tuple[int, ...]] = []
    for partition in integer_partitions(degree):
        nodes_list.append(partition)
        if maximum_nodes is not None and len(nodes_list) > maximum_nodes:
            raise RuntimeError("partition lattice exceeded configured maximum_nodes resource guard")
    node_set = set(nodes_list)
    edges: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()
    for source in nodes_list:
        for target in immediate_more_singular(source):
            if target in node_set and len(target) == len(source) - 1:
                edges.add((source, target))
    return PartitionLattice(
        degree=degree,
        nodes=tuple(nodes_list),
        edges_less_to_more_singular=tuple(sorted(edges)),
        status="OAK_PASS_MULTIPLICITY_PARTITION_LATTICE",
    )
