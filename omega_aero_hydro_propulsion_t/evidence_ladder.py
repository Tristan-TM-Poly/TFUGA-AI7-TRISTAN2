from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable


TIERS = (
    "F0_ANALYTIC",
    "F1_SYSTEM",
    "F2_STRESS",
    "F3_VORTEX_PROXY",
    "F4_HIGH_FIDELITY_NUMERICAL",
    "F5_EXPERIMENT",
    "F6_ENGINEERING_REVIEW",
)
TIER_INDEX = {name: index for index, name in enumerate(TIERS)}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    tier: str
    artifact_sha256: str
    provenance: str
    method: str
    limitations: tuple[str, ...]
    metadata: dict[str, Any]
    independent_reproduction: bool = False
    certification_claim: bool = False

    def validate(self) -> None:
        if not self.receipt_id.strip() or not self.provenance.strip() or not self.method.strip():
            raise ValueError("receipt identity, provenance and method are required")
        if self.tier not in TIER_INDEX:
            raise ValueError(f"unknown evidence tier: {self.tier}")
        if not _SHA256.fullmatch(self.artifact_sha256):
            raise ValueError("artifact_sha256 must be a lowercase SHA-256 digest")
        if not self.limitations:
            raise ValueError("every receipt must declare at least one limitation")
        if self.certification_claim:
            raise ValueError("software receipts cannot assert certification")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["limitations"] = list(self.limitations)
        return payload


@dataclass(frozen=True)
class ReceiptAssessment:
    receipt_id: str
    tier: str
    accepted: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "tier": self.tier,
            "accepted": self.accepted,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class EvidenceLadderReport:
    assessments: tuple[ReceiptAssessment, ...]
    accepted_receipt_ids: tuple[str, ...]
    highest_supported_tier: str | None
    contiguous_tier: str | None
    missing_lower_tiers: tuple[str, ...]
    certification_claim: bool
    physics_certified: bool
    evidence_hash: str
    notice: str = (
        "highest_supported_tier describes evidence classification only; it does not grant "
        "airworthiness, seaworthiness, regulatory approval or physical certification"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessments": [item.to_dict() for item in self.assessments],
            "accepted_receipt_ids": list(self.accepted_receipt_ids),
            "highest_supported_tier": self.highest_supported_tier,
            "contiguous_tier": self.contiguous_tier,
            "missing_lower_tiers": list(self.missing_lower_tiers),
            "certification_claim": self.certification_claim,
            "physics_certified": self.physics_certified,
            "evidence_hash": self.evidence_hash,
            "notice": self.notice,
        }


def _required_metadata(tier: str) -> tuple[str, ...]:
    return {
        "F0_ANALYTIC": ("equations", "assumptions"),
        "F1_SYSTEM": ("subsystems", "constraints"),
        "F2_STRESS": ("scenario_count", "uncertainty_definition"),
        "F3_VORTEX_PROXY": ("vortex_model", "core_model", "discretization"),
        "F4_HIGH_FIDELITY_NUMERICAL": (
            "solver",
            "governing_equations",
            "boundary_conditions",
            "mesh_levels",
            "residual_converged",
        ),
        "F5_EXPERIMENT": (
            "facility",
            "instrumentation",
            "calibration_id",
            "uncertainty_budget",
            "raw_data_retained",
        ),
        "F6_ENGINEERING_REVIEW": (
            "reviewer_role",
            "review_scope",
            "review_reference",
            "review_date",
        ),
    }[tier]


def assess_receipt(receipt: EvidenceReceipt) -> ReceiptAssessment:
    receipt.validate()
    blockers: list[str] = []
    warnings: list[str] = []
    missing = [key for key in _required_metadata(receipt.tier) if key not in receipt.metadata]
    blockers.extend(f"missing_metadata:{key}" for key in missing)

    if receipt.tier == "F4_HIGH_FIDELITY_NUMERICAL":
        mesh_levels = receipt.metadata.get("mesh_levels")
        if not isinstance(mesh_levels, int) or mesh_levels < 3:
            blockers.append("mesh_independence_requires_at_least_three_levels")
        if receipt.metadata.get("residual_converged") is not True:
            blockers.append("residual_convergence_not_demonstrated")
        if receipt.metadata.get("solver_verified") is not True:
            warnings.append("solver_verification_not_independently_demonstrated")
    elif receipt.tier == "F5_EXPERIMENT":
        if receipt.metadata.get("raw_data_retained") is not True:
            blockers.append("raw_data_not_retained")
        if not receipt.metadata.get("uncertainty_budget"):
            blockers.append("uncertainty_budget_missing")
        if not receipt.independent_reproduction:
            warnings.append("experiment_not_independently_reproduced")
    elif receipt.tier == "F6_ENGINEERING_REVIEW":
        if receipt.metadata.get("approval_type") in {"airworthiness", "seaworthiness", "regulatory_certification"}:
            blockers.append("regulatory_certification_cannot_be_granted_by_this_ledger")
        warnings.append("engineering_review_is_scope_bounded_and_not_automatic_certification")

    return ReceiptAssessment(
        receipt_id=receipt.receipt_id,
        tier=receipt.tier,
        accepted=not blockers,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def assess_evidence_ladder(receipts: Iterable[EvidenceReceipt]) -> EvidenceLadderReport:
    receipt_list = tuple(receipts)
    ids = [item.receipt_id for item in receipt_list]
    if len(ids) != len(set(ids)):
        raise ValueError("receipt_id values must be unique")
    assessments = tuple(assess_receipt(item) for item in receipt_list)
    accepted = [item for item, assessment in zip(receipt_list, assessments) if assessment.accepted]
    accepted_tiers = {item.tier for item in accepted}
    highest = max(accepted_tiers, key=TIER_INDEX.__getitem__) if accepted_tiers else None

    contiguous: str | None = None
    missing_lower: list[str] = []
    if highest is not None:
        for tier in TIERS[: TIER_INDEX[highest] + 1]:
            if tier in accepted_tiers:
                if not missing_lower:
                    contiguous = tier
            else:
                missing_lower.append(tier)

    stable = {
        "receipts": [item.to_dict() for item in receipt_list],
        "assessments": [item.to_dict() for item in assessments],
        "highest": highest,
        "contiguous": contiguous,
        "missing_lower": missing_lower,
    }
    return EvidenceLadderReport(
        assessments=assessments,
        accepted_receipt_ids=tuple(item.receipt_id for item in accepted),
        highest_supported_tier=highest,
        contiguous_tier=contiguous,
        missing_lower_tiers=tuple(missing_lower),
        certification_claim=False,
        physics_certified=False,
        evidence_hash=_digest(stable),
    )


def computational_receipts(*, wake_hash: str) -> tuple[EvidenceReceipt, ...]:
    if not _SHA256.fullmatch(wake_hash):
        raise ValueError("wake_hash must be a lowercase SHA-256 digest")
    return (
        EvidenceReceipt(
            "r05-f0",
            "F0_ANALYTIC",
            _digest({"tier": "F0", "wake_hash": wake_hash}),
            "Ω-PROPULSION internal deterministic benchmark",
            "annular blade-element and momentum equations",
            ("low-order analytic model",),
            {"equations": "annular BEM", "assumptions": "steady incompressible sectional screening"},
        ),
        EvidenceReceipt(
            "r05-f1",
            "F1_SYSTEM",
            _digest({"tier": "F1", "wake_hash": wake_hash}),
            "Ω-PROPULSION internal deterministic benchmark",
            "coupled structural, acoustic, mission and fault screening",
            ("subsystems remain low-order and partially coupled",),
            {"subsystems": ["structure", "acoustics", "mission", "faults"], "constraints": "R0.3 Max policy"},
        ),
        EvidenceReceipt(
            "r05-f2",
            "F2_STRESS",
            _digest({"tier": "F2", "wake_hash": wake_hash}),
            "Ω-PROPULSION internal deterministic benchmark",
            "expanded deterministic uncertainty and fault campaign",
            ("scenario coverage is finite and not probabilistic certification",),
            {"scenario_count": 12, "uncertainty_definition": "declared deterministic perturbation atlas"},
        ),
        EvidenceReceipt(
            "r05-f3",
            "F3_VORTEX_PROXY",
            wake_hash,
            "WakeGraph-T deterministic report",
            "regularized prescribed helical finite-segment vortex proxy",
            (
                "prescribed wake geometry",
                "fixed numerical core",
                "not a free-wake, CFD or experimental result",
            ),
            {
                "vortex_model": "finite-segment Biot-Savart",
                "core_model": "fixed regularized core",
                "discretization": "helical filaments from annular BEM sections",
            },
        ),
    )
