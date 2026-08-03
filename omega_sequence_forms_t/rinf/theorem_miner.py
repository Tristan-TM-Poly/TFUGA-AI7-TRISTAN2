"""Ω-SUITE-FORM-T∞ MAX theorem and identity candidate miner.

This module searches exact relations among finite sequence prefixes.  Every
result is a conjecture scoped to the supplied indices.  Finite agreement never
sets ``global_identity_proved`` to true.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from hashlib import sha256
import json
from itertools import combinations, product
from math import comb
from typing import Callable, Iterable, Iterator, Mapping, Sequence

from ..exact import NumberLike, normalize_terms, solve_unique_linear_system, vector_complexity


class RelationKind(str, Enum):
    LINEAR_COMBINATION = "linear_combination"
    AFFINE_COMBINATION = "affine_combination"
    SHIFT_IDENTITY = "shift_identity"
    POINTWISE_PRODUCT = "pointwise_product"
    CAUCHY_CONVOLUTION = "cauchy_convolution"
    BINOMIAL_SUM = "binomial_sum"
    POLYNOMIAL_RELATION = "polynomial_relation"
    MODULAR_CONGRUENCE = "modular_congruence"
    INVARIANT = "invariant"
    INEQUALITY = "inequality"


@dataclass(frozen=True)
class SequenceRecord:
    sequence_id: str
    terms: tuple[Fraction, ...]
    provenance: str = "direct_input"
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        sequence_id: str,
        terms: Iterable[NumberLike],
        *,
        provenance: str = "direct_input",
        metadata: Mapping[str, object] | None = None,
    ) -> "SequenceRecord":
        values = normalize_terms(terms)
        if not sequence_id:
            raise ValueError("sequence_id is required")
        if not values:
            raise ValueError("sequence requires terms")
        return cls(sequence_id, values, provenance, dict(metadata or {}))

    @property
    def digest(self) -> str:
        canonical = json.dumps(
            {
                "sequence_id": self.sequence_id,
                "terms": [str(value) for value in self.terms],
                "provenance": self.provenance,
                "metadata": dict(self.metadata),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RelationEvidence:
    tested_indices: tuple[int, ...]
    matched_indices: tuple[int, ...]
    failed_indices: tuple[int, ...]
    held_out_indices: tuple[int, ...] = ()
    held_out_matches: tuple[int, ...] = ()
    arithmetic: str = "exact_rational"

    @property
    def exact_on_tested(self) -> bool:
        return bool(self.tested_indices) and self.tested_indices == self.matched_indices

    @property
    def predicts_holdout(self) -> bool:
        return bool(self.held_out_indices) and self.held_out_indices == self.held_out_matches

    def to_dict(self) -> dict[str, object]:
        return {
            "tested_indices": list(self.tested_indices),
            "matched_indices": list(self.matched_indices),
            "failed_indices": list(self.failed_indices),
            "held_out_indices": list(self.held_out_indices),
            "held_out_matches": list(self.held_out_matches),
            "exact_on_tested": self.exact_on_tested,
            "predicts_holdout": self.predicts_holdout,
            "arithmetic": self.arithmetic,
        }


@dataclass(frozen=True)
class RelationCandidate:
    relation_id: str
    kind: RelationKind
    expression: str
    source_ids: tuple[str, ...]
    target_id: str | None
    parameters: Mapping[str, object]
    evidence: RelationEvidence
    assumptions: tuple[str, ...]
    proof_obligations: tuple[str, ...]
    complexity: int
    counterexample: Mapping[str, object] | None = None
    global_identity_proved: bool = False

    def __post_init__(self) -> None:
        if self.global_identity_proved:
            raise ValueError("automatic finite-prefix miner cannot mark global proof")
        if not self.source_ids:
            raise ValueError("relation requires sources")

    def to_dict(self) -> dict[str, object]:
        return {
            "relation_id": self.relation_id,
            "kind": self.kind.value,
            "expression": self.expression,
            "source_ids": list(self.source_ids),
            "target_id": self.target_id,
            "parameters": dict(self.parameters),
            "evidence": self.evidence.to_dict(),
            "assumptions": list(self.assumptions),
            "proof_obligations": list(self.proof_obligations),
            "complexity": self.complexity,
            "counterexample": None if self.counterexample is None else dict(self.counterexample),
            "global_identity_proved": False,
        }

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MiningLimits:
    maximum_sources: int = 8
    maximum_shift: int = 16
    maximum_polynomial_degree: int = 4
    maximum_monomials: int = 256
    maximum_relations: int = 4096
    holdout: int | None = None

    def __post_init__(self) -> None:
        if min(
            self.maximum_sources,
            self.maximum_shift + 1,
            self.maximum_polynomial_degree + 1,
            self.maximum_monomials,
            self.maximum_relations,
        ) <= 0:
            raise ValueError("mining limits must be positive")


@dataclass
class MiningReport:
    sequences: tuple[SequenceRecord, ...]
    relations: list[RelationCandidate]
    limits: MiningLimits
    attempted_families: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = {
            "schema": "omega-sequence-theorem-miner/1",
            "sequences": [
                {
                    "sequence_id": item.sequence_id,
                    "term_count": len(item.terms),
                    "digest": item.digest,
                    "provenance": item.provenance,
                }
                for item in self.sequences
            ],
            "relation_count": len(self.relations),
            "relations": [item.to_dict() for item in self.relations],
            "attempted_families": list(self.attempted_families),
            "warnings": list(self.warnings),
            "limits": {
                "maximum_sources": self.limits.maximum_sources,
                "maximum_shift": self.limits.maximum_shift,
                "maximum_polynomial_degree": self.limits.maximum_polynomial_degree,
                "maximum_monomials": self.limits.maximum_monomials,
                "maximum_relations": self.limits.maximum_relations,
                "holdout": self.limits.holdout,
            },
            "global_identity_proved": False,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload["report_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload


def _split_count(length: int, holdout: int | None) -> tuple[int, int]:
    if holdout is None:
        holdout = 0 if length < 12 else max(3, min(32, length // 4))
    if not 0 <= holdout < length:
        raise ValueError("invalid holdout")
    return length - holdout, holdout


def _evidence(
    predicate: Callable[[int], bool],
    *,
    training_count: int,
    total_count: int,
) -> RelationEvidence:
    tested = tuple(range(training_count))
    matched = tuple(index for index in tested if predicate(index))
    failed = tuple(index for index in tested if index not in set(matched))
    held = tuple(range(training_count, total_count))
    held_matches = tuple(index for index in held if predicate(index))
    return RelationEvidence(tested, matched, failed, held, held_matches)


def _relation_id(kind: RelationKind, expression: str, source_ids: Sequence[str], target_id: str | None) -> str:
    canonical = json.dumps(
        {"kind": kind.value, "expression": expression, "sources": list(source_ids), "target": target_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"relation.{kind.value}.{sha256(canonical.encode('utf-8')).hexdigest()[:20]}"


def mine_linear_combination(
    sources: Sequence[SequenceRecord],
    target: SequenceRecord,
    *,
    affine: bool = False,
    holdout: int | None = None,
) -> RelationCandidate | None:
    if not sources:
        raise ValueError("at least one source is required")
    length = min([len(target.terms)] + [len(source.terms) for source in sources])
    training_count, _ = _split_count(length, holdout)
    width = len(sources) + int(affine)
    if training_count <= width:
        return None
    matrix = []
    rhs = []
    for index in range(training_count):
        row = [source.terms[index] for source in sources]
        if affine:
            row.append(Fraction(1))
        matrix.append(row)
        rhs.append(target.terms[index])
    solution = solve_unique_linear_system(matrix, rhs)
    if solution is None:
        return None
    coefficients = tuple(solution[: len(sources)])
    intercept = solution[-1] if affine else Fraction(0)

    def predicted(index: int) -> Fraction:
        return intercept + sum(
            (coefficient * source.terms[index] for coefficient, source in zip(coefficients, sources)),
            Fraction(0),
        )

    evidence = _evidence(lambda index: predicted(index) == target.terms[index], training_count=training_count, total_count=length)
    if not evidence.exact_on_tested:
        return None
    terms = [f"({coefficient})*{source.sequence_id}[n]" for coefficient, source in zip(coefficients, sources)]
    if affine and intercept:
        terms.append(str(intercept))
    expression = f"{target.sequence_id}[n] = " + " + ".join(terms)
    kind = RelationKind.AFFINE_COMBINATION if affine else RelationKind.LINEAR_COMBINATION
    return RelationCandidate(
        relation_id=_relation_id(kind, expression, tuple(source.sequence_id for source in sources), target.sequence_id),
        kind=kind,
        expression=expression,
        source_ids=tuple(source.sequence_id for source in sources),
        target_id=target.sequence_id,
        parameters={
            "coefficients": [str(value) for value in coefficients],
            "intercept": str(intercept),
        },
        evidence=evidence,
        assumptions=("common_index_origin", "exact_rational_values"),
        proof_obligations=("prove relation for all indices in domain", "justify source definitions"),
        complexity=vector_complexity(coefficients + (intercept,)) + len(sources),
    )


def mine_shift_identity(
    source: SequenceRecord,
    target: SequenceRecord,
    *,
    maximum_shift: int = 16,
    allow_scale: bool = True,
    holdout: int | None = None,
) -> tuple[RelationCandidate, ...]:
    candidates = []
    for shift in range(-maximum_shift, maximum_shift + 1):
        source_start = max(0, -shift)
        target_start = max(0, shift)
        available = min(len(source.terms) - source_start, len(target.terms) - target_start)
        if available < 4:
            continue
        training_count, _ = _split_count(available, holdout)
        pairs = [
            (source.terms[source_start + index], target.terms[target_start + index])
            for index in range(available)
        ]
        scale = Fraction(1)
        if allow_scale:
            first = next(((a, b) for a, b in pairs[:training_count] if a != 0), None)
            if first is None:
                continue
            scale = first[1] / first[0]
        def predicate(index: int) -> bool:
            a, b = pairs[index]
            return scale * a == b
        evidence = _evidence(predicate, training_count=training_count, total_count=available)
        if not evidence.exact_on_tested:
            continue
        expression = f"{target.sequence_id}[n+{target_start}] = ({scale})*{source.sequence_id}[n+{source_start}]"
        candidates.append(
            RelationCandidate(
                relation_id=_relation_id(RelationKind.SHIFT_IDENTITY, expression, (source.sequence_id,), target.sequence_id),
                kind=RelationKind.SHIFT_IDENTITY,
                expression=expression,
                source_ids=(source.sequence_id,),
                target_id=target.sequence_id,
                parameters={"shift": shift, "scale": str(scale)},
                evidence=evidence,
                assumptions=("overlapping_index_domain",),
                proof_obligations=("prove shifted identity globally",),
                complexity=abs(shift) + vector_complexity((scale,)) + 2,
            )
        )
    candidates.sort(key=lambda item: (not item.evidence.predicts_holdout, item.complexity, item.relation_id))
    return tuple(candidates)


def cauchy_prefix(left: Sequence[Fraction], right: Sequence[Fraction], count: int) -> tuple[Fraction, ...]:
    return tuple(
        sum(
            (left[k] * right[n - k] for k in range(max(0, n - len(right) + 1), min(n, len(left) - 1) + 1)),
            Fraction(0),
        )
        for n in range(count)
    )


def mine_cauchy_convolution(
    left: SequenceRecord,
    right: SequenceRecord,
    target: SequenceRecord,
    *,
    scale: bool = True,
    holdout: int | None = None,
) -> RelationCandidate | None:
    length = min(len(target.terms), len(left.terms) + len(right.terms) - 1)
    if length < 6:
        return None
    convolution = cauchy_prefix(left.terms, right.terms, length)
    training_count, _ = _split_count(length, holdout)
    factor = Fraction(1)
    if scale:
        first = next(((a, b) for a, b in zip(convolution[:training_count], target.terms[:training_count]) if a), None)
        if first is None:
            return None
        factor = first[1] / first[0]
    evidence = _evidence(
        lambda index: factor * convolution[index] == target.terms[index],
        training_count=training_count,
        total_count=length,
    )
    if not evidence.exact_on_tested:
        return None
    expression = f"{target.sequence_id}[n] = ({factor})*Sum(k=0..n,{left.sequence_id}[k]*{right.sequence_id}[n-k])"
    return RelationCandidate(
        relation_id=_relation_id(RelationKind.CAUCHY_CONVOLUTION, expression, (left.sequence_id, right.sequence_id), target.sequence_id),
        kind=RelationKind.CAUCHY_CONVOLUTION,
        expression=expression,
        source_ids=(left.sequence_id, right.sequence_id),
        target_id=target.sequence_id,
        parameters={"scale": str(factor)},
        evidence=evidence,
        assumptions=("zero_extension_outside_prefix", "ordinary_generating_function_semantics"),
        proof_obligations=("prove coefficient extraction identity",),
        complexity=vector_complexity((factor,)) + 8,
    )


def mine_pointwise_product(
    left: SequenceRecord,
    right: SequenceRecord,
    target: SequenceRecord,
    *,
    holdout: int | None = None,
) -> RelationCandidate | None:
    length = min(len(left.terms), len(right.terms), len(target.terms))
    training_count, _ = _split_count(length, holdout)
    evidence = _evidence(
        lambda index: left.terms[index] * right.terms[index] == target.terms[index],
        training_count=training_count,
        total_count=length,
    )
    if not evidence.exact_on_tested:
        return None
    expression = f"{target.sequence_id}[n] = {left.sequence_id}[n]*{right.sequence_id}[n]"
    return RelationCandidate(
        relation_id=_relation_id(RelationKind.POINTWISE_PRODUCT, expression, (left.sequence_id, right.sequence_id), target.sequence_id),
        kind=RelationKind.POINTWISE_PRODUCT,
        expression=expression,
        source_ids=(left.sequence_id, right.sequence_id),
        target_id=target.sequence_id,
        parameters={},
        evidence=evidence,
        assumptions=("common_index_origin",),
        proof_obligations=("prove factorization for all n",),
        complexity=4,
    )


def exponent_vectors(variable_count: int, maximum_degree: int, maximum_monomials: int) -> tuple[tuple[int, ...], ...]:
    vectors = []
    for exponents in product(range(maximum_degree + 1), repeat=variable_count):
        if sum(exponents) <= maximum_degree:
            vectors.append(tuple(exponents))
        if len(vectors) >= maximum_monomials:
            break
    vectors.sort(key=lambda item: (sum(item), item))
    return tuple(vectors)


def monomial_value(values: Sequence[Fraction], exponents: Sequence[int]) -> Fraction:
    result = Fraction(1)
    for value, exponent in zip(values, exponents):
        result *= value**exponent
    return result


def mine_polynomial_relation(
    records: Sequence[SequenceRecord],
    *,
    maximum_degree: int = 3,
    maximum_monomials: int = 128,
    holdout: int | None = None,
) -> tuple[RelationCandidate, ...]:
    if len(records) < 2:
        raise ValueError("polynomial relation requires at least two sequences")
    length = min(len(record.terms) for record in records)
    training_count, _ = _split_count(length, holdout)
    exponents = exponent_vectors(len(records), maximum_degree, maximum_monomials)
    if training_count <= len(exponents) - 1:
        return ()
    rows = [
        [monomial_value([record.terms[index] for record in records], vector) for vector in exponents]
        for index in range(training_count)
    ]
    relations = []
    for pivot in range(len(exponents)):
        matrix = [[row[column] for column in range(len(exponents)) if column != pivot] for row in rows]
        rhs = [-row[pivot] for row in rows]
        solution = solve_unique_linear_system(matrix, rhs)
        if solution is None:
            continue
        coefficients = list(solution)
        coefficients.insert(pivot, Fraction(1))
        first = next((value for value in coefficients if value), None)
        if first is None:
            continue
        coefficients = [value / first for value in coefficients]
        def residual(index: int) -> Fraction:
            values = [record.terms[index] for record in records]
            return sum(
                (coefficient * monomial_value(values, vector) for coefficient, vector in zip(coefficients, exponents)),
                Fraction(0),
            )
        evidence = _evidence(lambda index: residual(index) == 0, training_count=training_count, total_count=length)
        if not evidence.exact_on_tested:
            continue
        pieces = []
        for coefficient, vector in zip(coefficients, exponents):
            if coefficient == 0:
                continue
            factors = []
            for record, exponent in zip(records, vector):
                if exponent:
                    factors.append(f"{record.sequence_id}[n]^{exponent}")
            monomial = "*".join(factors) if factors else "1"
            pieces.append(f"({coefficient})*{monomial}")
        expression = " + ".join(pieces) + " = 0"
        relation = RelationCandidate(
            relation_id=_relation_id(RelationKind.POLYNOMIAL_RELATION, expression, tuple(record.sequence_id for record in records), None),
            kind=RelationKind.POLYNOMIAL_RELATION,
            expression=expression,
            source_ids=tuple(record.sequence_id for record in records),
            target_id=None,
            parameters={
                "maximum_degree": maximum_degree,
                "exponents": [list(vector) for vector in exponents],
                "coefficients": [str(value) for value in coefficients],
            },
            evidence=evidence,
            assumptions=("exact_rational_values", "finite_monomial_basis"),
            proof_obligations=("prove polynomial identity globally", "exclude algebraic overfitting"),
            complexity=vector_complexity(coefficients) + sum(sum(vector) for vector in exponents),
        )
        relations.append(relation)
    unique = {relation.digest(): relation for relation in relations}
    return tuple(sorted(unique.values(), key=lambda item: (not item.evidence.predicts_holdout, item.complexity, item.relation_id)))


def first_counterexample(
    relation: RelationCandidate,
    evaluator: Callable[[int], tuple[Fraction, Fraction]],
    indices: Iterable[int],
) -> Mapping[str, object] | None:
    for index in indices:
        left, right = evaluator(index)
        if left != right:
            return {
                "index": index,
                "left": str(left),
                "right": str(right),
                "residual": str(left - right),
            }
    return None


def mine_relations(
    records: Sequence[SequenceRecord],
    *,
    limits: MiningLimits | None = None,
) -> MiningReport:
    limits = limits or MiningLimits()
    if len(records) > limits.maximum_sources:
        records = records[: limits.maximum_sources]
    relations: list[RelationCandidate] = []

    for target in records:
        sources = [record for record in records if record.sequence_id != target.sequence_id]
        for source in sources:
            relations.extend(
                mine_shift_identity(
                    source,
                    target,
                    maximum_shift=limits.maximum_shift,
                    holdout=limits.holdout,
                )[:8]
            )
        for size in range(1, min(len(sources), 4) + 1):
            for subset in combinations(sources, size):
                for affine in (False, True):
                    candidate = mine_linear_combination(subset, target, affine=affine, holdout=limits.holdout)
                    if candidate is not None:
                        relations.append(candidate)
                if len(relations) >= limits.maximum_relations:
                    break
            if len(relations) >= limits.maximum_relations:
                break

    for left, right in combinations(records, 2):
        for target in records:
            if target.sequence_id in {left.sequence_id, right.sequence_id}:
                continue
            product_candidate = mine_pointwise_product(left, right, target, holdout=limits.holdout)
            if product_candidate is not None:
                relations.append(product_candidate)
            convolution_candidate = mine_cauchy_convolution(left, right, target, holdout=limits.holdout)
            if convolution_candidate is not None:
                relations.append(convolution_candidate)
            if len(relations) >= limits.maximum_relations:
                break

    if len(records) >= 2 and len(relations) < limits.maximum_relations:
        relations.extend(
            mine_polynomial_relation(
                records,
                maximum_degree=limits.maximum_polynomial_degree,
                maximum_monomials=limits.maximum_monomials,
                holdout=limits.holdout,
            )[: max(0, limits.maximum_relations - len(relations))]
        )

    unique = {relation.digest(): relation for relation in relations}
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            not item.evidence.predicts_holdout,
            not item.evidence.exact_on_tested,
            item.complexity,
            item.relation_id,
        ),
    )[: limits.maximum_relations]
    return MiningReport(
        sequences=tuple(records),
        relations=list(ordered),
        limits=limits,
        attempted_families=(
            RelationKind.SHIFT_IDENTITY.value,
            RelationKind.LINEAR_COMBINATION.value,
            RelationKind.AFFINE_COMBINATION.value,
            RelationKind.POINTWISE_PRODUCT.value,
            RelationKind.CAUCHY_CONVOLUTION.value,
            RelationKind.POLYNOMIAL_RELATION.value,
        ),
        warnings=(
            "All relations are finite-prefix conjectures.",
            "Held-out agreement is evidence, not proof.",
            "Polynomial lifts can overfit when the monomial basis is too large.",
        ),
    )
