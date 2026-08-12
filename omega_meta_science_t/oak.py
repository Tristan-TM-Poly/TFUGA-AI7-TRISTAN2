"""Fail-closed OAK and Meta-OAK mutation testing for scientific claim packets."""

from __future__ import annotations

from dataclasses import replace

from .models import ClaimPacket, MutationCampaign, OAKReport


FAULT_TYPES = (
    "missing_provenance",
    "unit_mismatch",
    "non_reproducible",
    "overclaim_residual",
)


def evaluate_oak(packet: ClaimPacket) -> OAKReport:
    blockers: list[str] = []
    warnings: list[str] = []

    if not packet.provenance:
        blockers.append("PROVENANCE_MISSING")
    if packet.uncertainty < 0.0:
        blockers.append("UNCERTAINTY_INVALID")
    if not packet.baseline_declared:
        blockers.append("BASELINE_MISSING")
    if not packet.reproducible:
        blockers.append("REPRODUCIBILITY_FAILED")
    if not packet.unit_consistent:
        blockers.append("UNIT_MISMATCH")
    if not packet.falsifier_declared:
        blockers.append("FALSIFIER_MISSING")
    if packet.residual > packet.residual_tolerance:
        blockers.append(
            f"RESIDUAL_EXCEEDS_TOLERANCE:{packet.residual:g}>{packet.residual_tolerance:g}"
        )

    if blockers:
        return OAKReport("BLOCK", tuple(blockers), tuple(warnings))

    if packet.survivor_count != 1:
        warnings.append(f"UNDERDETERMINED:{packet.survivor_count}_SURVIVORS")
        return OAKReport("CONDITIONAL", (), tuple(warnings))

    return OAKReport("PROMOTE", (), ())


def inject_fault(packet: ClaimPacket, fault: str) -> ClaimPacket:
    if fault == "missing_provenance":
        return replace(packet, provenance="")
    if fault == "unit_mismatch":
        return replace(packet, unit_consistent=False)
    if fault == "non_reproducible":
        return replace(packet, reproducible=False)
    if fault == "overclaim_residual":
        return replace(packet, residual=max(1.0, packet.residual_tolerance * 1000.0))
    raise ValueError(f"unknown epistemic fault: {fault}")


def meta_oak_mutation_campaign(packet: ClaimPacket) -> MutationCampaign:
    detected: list[str] = []
    missed: list[str] = []
    for fault in FAULT_TYPES:
        mutated = inject_fault(packet, fault)
        if evaluate_oak(mutated).decision == "BLOCK":
            detected.append(fault)
        else:
            missed.append(fault)
    total = len(FAULT_TYPES)
    score = len(detected) / total if total else 1.0
    return MutationCampaign(
        injected=total,
        detected=len(detected),
        mutation_score=score,
        detected_faults=tuple(detected),
        missed_faults=tuple(missed),
    )
