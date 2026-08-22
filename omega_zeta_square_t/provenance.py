"""Provenance gates for rigorous interval inputs in Ω-ZETA-SQUARE-T∞.

Rigorous interval arithmetic is only as strong as the source of its input
enclosures.  This module keeps *arithmetic rigor* separate from *analytic source
certification* so supplied/test intervals cannot silently become certified xi
bounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable

from .intervals import RationalInterval


class EvidenceKind(str, Enum):
    SUPPLIED = "SUPPLIED"
    EXACT_IDENTITY = "EXACT_IDENTITY"
    NUMERIC_APPROXIMATION = "NUMERIC_APPROXIMATION"
    ANALYTIC_CERTIFIED_INTERVAL = "ANALYTIC_CERTIFIED_INTERVAL"
    FORMAL_VERIFIED_INTERVAL = "FORMAL_VERIFIED_INTERVAL"


_CERTIFIED_KINDS = {
    EvidenceKind.ANALYTIC_CERTIFIED_INTERVAL,
    EvidenceKind.FORMAL_VERIFIED_INTERVAL,
}


@dataclass(frozen=True)
class IntervalEvidence:
    quantity: str
    enclosure: RationalInterval
    kind: EvidenceKind
    method: str = ""
    reference: str = ""
    source_sha256: str = ""
    notes: str = ""

    @property
    def analytically_certified(self) -> bool:
        return self.kind in _CERTIFIED_KINDS


@dataclass(frozen=True)
class ProvenanceVerdict:
    admissible_for_rigorous_propagation: bool
    analytically_certified_inputs: bool
    promotion_cap: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    proves_rh: bool = False


def _valid_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value))


def validate_interval_evidence(items: Iterable[IntervalEvidence]) -> ProvenanceVerdict:
    evidence = tuple(items)
    errors: list[str] = []
    warnings: list[str] = []
    if not evidence:
        errors.append("at least one interval evidence item is required")

    seen: set[str] = set()
    for item in evidence:
        if not item.quantity:
            errors.append("quantity must be non-empty")
            continue
        if item.quantity in seen:
            errors.append(f"duplicate quantity: {item.quantity}")
        seen.add(item.quantity)

        if item.kind in _CERTIFIED_KINDS:
            if not item.method:
                errors.append(f"{item.quantity}: certified interval requires method")
            if not item.reference:
                errors.append(f"{item.quantity}: certified interval requires reference")
            if item.source_sha256 and not _valid_sha256(item.source_sha256):
                errors.append(f"{item.quantity}: source_sha256 must be 64 hex chars")
        elif item.kind is EvidenceKind.SUPPLIED:
            warnings.append(
                f"{item.quantity}: supplied enclosure is rigorous only conditionally on the supplied bounds"
            )
        elif item.kind is EvidenceKind.NUMERIC_APPROXIMATION:
            warnings.append(
                f"{item.quantity}: numeric approximation is not a certified enclosure source"
            )

    analytic = bool(evidence) and all(item.analytically_certified for item in evidence)
    admissible = not errors
    if not admissible:
        cap = "BLOCKED_INVALID_PROVENANCE"
    elif analytic:
        cap = "CERTIFIED_INPUTS_FINITE_CONSEQUENCES_ONLY"
    else:
        cap = "RIGOROUS_PROPAGATION_CONDITIONAL_ON_INPUTS_ONLY"
    return ProvenanceVerdict(
        admissible_for_rigorous_propagation=admissible,
        analytically_certified_inputs=analytic,
        promotion_cap=cap,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
