"""Conservative comparison and apoptosis gates for synthesized operators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Hashable, Sequence, TypeVar

from .core import SynthesisReceipt

T = TypeVar("T", bound=Hashable)


@dataclass(frozen=True, slots=True)
class BaselineOperator:
    name: str
    exchange_signature: tuple[int, int]


@dataclass(frozen=True, slots=True)
class BaselineCoverage:
    covered: tuple[str, ...]
    uncovered: tuple[str, ...]
    synthesized_signatures: tuple[tuple[int, int], ...]

    @property
    def complete(self) -> bool:
        return not self.uncovered


@dataclass(frozen=True, slots=True)
class ApoptosisDecision:
    decision: str
    reasons: tuple[str, ...]
    automatic_delete: bool = False
    destructive_action_authorized: bool = False


def baseline_coverage(
    receipt: SynthesisReceipt[T], baselines: Sequence[BaselineOperator]
) -> BaselineCoverage:
    signatures = tuple(sorted({witness.exchange_signature for witness in receipt.witnesses}))
    covered = tuple(item.name for item in baselines if item.exchange_signature in signatures)
    uncovered = tuple(item.name for item in baselines if item.exchange_signature not in signatures)
    return BaselineCoverage(covered, uncovered, signatures)


def evaluate_apoptosis(
    receipt: SynthesisReceipt[T],
    baselines: Sequence[BaselineOperator],
    *,
    semantic_equivalence_evidence: bool = False,
    benchmark_noninferiority_evidence: bool = False,
) -> ApoptosisDecision:
    """Never delete automatically; return at most ELIGIBLE_FOR_REVIEW."""

    reasons: list[str] = []
    if receipt.status != "PASS" or not receipt.finite_minimality_certified:
        reasons.append("synthesis_not_finitely_certified")
    if not baselines:
        reasons.append("baseline_registry_required")
    coverage = baseline_coverage(receipt, baselines)
    if not coverage.complete:
        reasons.append("baseline_signatures_not_covered")
    if not semantic_equivalence_evidence:
        reasons.append("semantic_equivalence_evidence_required")
    if not benchmark_noninferiority_evidence:
        reasons.append("benchmark_noninferiority_evidence_required")

    if reasons:
        return ApoptosisDecision("HOLD", tuple(reasons))
    return ApoptosisDecision(
        "ELIGIBLE_FOR_REVIEW",
        (
            "declared baseline signatures covered",
            "semantic equivalence evidence attached",
            "benchmark noninferiority evidence attached",
            "human/repository governance review still required before deletion",
        ),
    )
