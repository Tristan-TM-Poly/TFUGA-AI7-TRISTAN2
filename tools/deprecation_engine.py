"""Deprecation Engine for Tristan CanonOS.

Deprecation is treated as canon protection. This module recommends how to lower,
archive, quarantine, or refactor weak ideas without deleting evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DeprecationAction(StrEnum):
    KEEP = "keep"
    DOWNRANK = "downrank"
    ARCHIVE = "archive"
    QUARANTINE = "quarantine"
    REFACTOR = "refactor"


@dataclass(frozen=True)
class DeprecationDecision:
    action: DeprecationAction
    rationale: str
    safe_next_action: str


def decide_deprecation(
    *,
    obsolete: bool = False,
    unsupported_claim: bool = False,
    unsafe: bool = False,
    duplicated: bool = False,
    salvageable: bool = True,
) -> DeprecationDecision:
    if unsafe:
        return DeprecationDecision(
            DeprecationAction.QUARANTINE,
            "Unsafe or high-risk content must not remain active canon.",
            "Move to quarantine notes; preserve provenance; block execution.",
        )
    if unsupported_claim:
        return DeprecationDecision(
            DeprecationAction.DOWNRANK,
            "Claim lacks supporting evidence for current rank.",
            "Lower rank and add ProofLadder target.",
        )
    if duplicated and salvageable:
        return DeprecationDecision(
            DeprecationAction.REFACTOR,
            "Duplicate content can be merged or split cleanly.",
            "Create refactor mutation plan in draft branch.",
        )
    if obsolete:
        return DeprecationDecision(
            DeprecationAction.ARCHIVE,
            "Obsolete content should remain traceable but inactive.",
            "Archive with reason and replacement link.",
        )
    return DeprecationDecision(
        DeprecationAction.KEEP,
        "No deprecation signal detected.",
        "Keep active and continue monitoring.",
    )
