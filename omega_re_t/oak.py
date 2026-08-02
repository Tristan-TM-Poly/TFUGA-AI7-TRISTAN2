"""Fail-closed OAK promotion gate for reverse-engineering claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .evidence import EvidenceLedger
from .models import ClaimStatus, OAKMetricVector, OAKReport


@dataclass(frozen=True, slots=True)
class OAKThresholds:
    fidelity: float = 0.95
    generalization: float = 0.90
    causal_quality: float = 0.50
    parsimony: float = 0.50
    uncertainty_calibration: float = 0.70
    reproducibility: float = 0.90
    legal_provenance: float = 1.00


def evaluate_oak(
    metrics: OAKMetricVector,
    ledger: EvidenceLedger,
    *,
    thresholds: OAKThresholds = OAKThresholds(),
    independent_validation: bool = False,
    known_counterexamples: Sequence[str] = (),
) -> OAKReport:
    blockers: list[str] = []
    warnings: list[str] = []
    valid_chain, chain_errors = ledger.verify()
    if not valid_chain:
        blockers.extend(f"EVIDENCE_CHAIN: {error}" for error in chain_errors)
    for name, threshold in asdict(thresholds).items():
        value = getattr(metrics, name)
        if value < threshold:
            blockers.append(f"METRIC:{name}={value:.3f}<{threshold:.3f}")
    if known_counterexamples:
        blockers.extend(f"COUNTEREXAMPLE:{value}" for value in known_counterexamples)
    if not independent_validation:
        warnings.append("No independent validation; VERIFIED promotion is unavailable")
    if blockers:
        decision = "BLOCK"
        status = ClaimStatus.FALSIFIED if known_counterexamples else ClaimStatus.RECONSTRUCTED
    elif independent_validation:
        decision = "PROMOTE"
        status = ClaimStatus.VERIFIED
    else:
        decision = "CONDITIONAL"
        status = ClaimStatus.RECONSTRUCTED
    return OAKReport(
        decision=decision,
        metrics=metrics,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        promoted_status=status,
        evidence_root=ledger.root_hash,
    )
