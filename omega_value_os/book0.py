"""EconomicBOOK0 and deterministic regeneration receipts for Ω Value OS R2."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import FrozenSet, Iterable, Tuple


@dataclass(frozen=True)
class EconomicBOOK0:
    """Minimum candidate seed needed to reconstruct required economic capabilities."""

    capabilities: FrozenSet[str]
    user_problems: FrozenSet[str]
    offer_grammar: FrozenSet[str]
    pricing_rules: FrozenSet[str]
    revenue_mechanisms: FrozenSet[str]
    evidence_rules: FrozenSet[str]
    authority_rules: FrozenSet[str]
    dependencies: FrozenSet[str]
    recovery_probes: FrozenSet[str]


@dataclass(frozen=True)
class RegenerationReceipt:
    required_capabilities: FrozenSet[str]
    recovered_capabilities: FrozenSet[str]
    missing_capabilities: FrozenSet[str]
    regeneration_ratio: float
    probe_residual: float
    identity_claimed: bool = False


def regeneration_receipt(
    *,
    required_capabilities: Iterable[str],
    recovered_capabilities: Iterable[str],
    probe_residual: float,
) -> RegenerationReceipt:
    required = frozenset(required_capabilities)
    recovered = frozenset(recovered_capabilities)
    matched = required & recovered
    ratio = 1.0 if not required else len(matched) / len(required)
    return RegenerationReceipt(
        required_capabilities=required,
        recovered_capabilities=recovered,
        missing_capabilities=required - recovered,
        regeneration_ratio=ratio,
        probe_residual=max(0.0, float(probe_residual)),
    )


def regeneration_passes(
    receipt: RegenerationReceipt,
    *,
    minimum_ratio: float = 1.0,
    maximum_probe_residual: float = 0.0,
) -> bool:
    """Functional closure test; it never claims reconstruction of identity."""
    return (
        not receipt.identity_claimed
        and receipt.regeneration_ratio >= minimum_ratio
        and receipt.probe_residual <= maximum_probe_residual
    )


def ablate_book0(
    book: EconomicBOOK0,
    *,
    removable_capabilities: Iterable[str],
    required_capabilities: Iterable[str],
) -> Tuple[EconomicBOOK0, Tuple[str, ...]]:
    """Remove only capabilities explicitly shown not to be required.

    This is a conservative ablation court: callers must supply the required set
    from external probes/evidence.  The function does not invent necessity.
    """
    required = frozenset(required_capabilities)
    candidates = frozenset(removable_capabilities)
    removed = tuple(sorted((book.capabilities & candidates) - required))
    return replace(book, capabilities=book.capabilities - frozenset(removed)), removed


def future_work_annihilation(
    *,
    baseline_future_work: float,
    residual_future_work: float,
    verification_cost: float = 0.0,
) -> float:
    """Estimate future work eliminated after paying the verification burden."""
    eliminated = max(0.0, baseline_future_work - residual_future_work)
    return max(0.0, eliminated - max(0.0, verification_cost))
