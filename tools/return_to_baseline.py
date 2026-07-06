"""Return-to-Baseline protocol for high-entropy AIT exploration.

This module converts high-entropy conceptual exploration into a safer, labeled,
anchored, testable, or quarantined output. It is not a truth oracle and not a
substitute for qualified human review.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.hallucination_labeler import ClaimLabel, ClaimStatus, label_claim
from tools.immune_compiler import RollbackProof, compile_action_immune_packet
from tools.ait_action_autonomy_gate import RiskDomain


@dataclass(frozen=True)
class BaselineReturnPacket:
    original_text: str
    sanitized_summary: str
    claim_label: ClaimLabel
    m_minus_notes: tuple[str, ...]
    quarantine_required: bool
    safe_next_action: str
    action_packet_status: str


UNSAFE_TERMS = {
    "dose",
    "extraction",
    "potentiate",
    "mixing protocol",
    "delete logs",
    "steal",
    "bypass safety",
}


def sanitize_exploration_text(text: str) -> tuple[str, tuple[str, ...]]:
    """Remove or flag unsafe boundary terms from a conceptual exploration."""

    lowered = text.lower()
    notes: list[str] = []
    sanitized = text
    for term in UNSAFE_TERMS:
        if term in lowered:
            sanitized = sanitized.replace(term, "[REDACTED_UNSAFE_TERM]")
            sanitized = sanitized.replace(term.title(), "[REDACTED_UNSAFE_TERM]")
            notes.append(f"unsafe_term_removed:{term}")
    return sanitized, tuple(notes)


def return_to_baseline(
    *,
    exploration_text: str,
    has_reality_anchor: bool = False,
    has_test: bool = False,
    has_implementation: bool = False,
    has_measurement: bool = False,
    independently_reproduced: bool = False,
    risk_domains: tuple[RiskDomain | str, ...] = (RiskDomain.LOW_RISK_CREATIVE,),
) -> BaselineReturnPacket:
    """Convert exploratory text into a safe baseline packet."""

    sanitized, notes = sanitize_exploration_text(exploration_text)
    label = label_claim(
        sanitized,
        has_reality_anchor=has_reality_anchor,
        has_test=has_test,
        has_implementation=has_implementation,
        has_measurement=has_measurement,
        independently_reproduced=independently_reproduced,
    )

    quarantine_required = label.status == ClaimStatus.QUARANTINED
    missing_tests = not has_test
    claim_too_strong = "overclaim_language_detected" in label.reasons

    action_packet = compile_action_immune_packet(
        goal="Return high-entropy exploration to baseline",
        expected_benefit="Preserve creative insight while reducing hallucination and execution risk.",
        risk_domains=risk_domains,
        action_text=sanitized,
        rollback=RollbackProof(exists=True, tested=False, summary="Revert generated artifact and keep only notes."),
        missing_tests=missing_tests,
        claim_too_strong=claim_too_strong,
        irreversible_or_public_side_effect=quarantine_required,
    )

    if quarantine_required:
        next_action = "Quarantine; analysis only; no execution or publication."
    elif label.status in {ClaimStatus.VISION, ClaimStatus.METAPHOR}:
        next_action = "Add RealityAnchor and falsification test before any prototype."
    elif label.status == ClaimStatus.HYPOTHESIS:
        next_action = "Implement minimal reversible test in sandbox or draft branch."
    elif label.status == ClaimStatus.PROTOTYPE:
        next_action = "Benchmark, measure, and add M- notes before stronger claims."
    else:
        next_action = "Document scope, uncertainty, and reproduction status."

    return BaselineReturnPacket(
        original_text=exploration_text,
        sanitized_summary=sanitized,
        claim_label=label,
        m_minus_notes=notes,
        quarantine_required=quarantine_required,
        safe_next_action=next_action,
        action_packet_status=str(action_packet.oak_status),
    )
