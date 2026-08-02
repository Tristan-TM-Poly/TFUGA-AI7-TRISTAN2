from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


EVIDENCE_TIERS = (
    "D0_STRUCTURE",
    "D1_UNIT_TESTED",
    "D2_SIMULATED_COMPONENT",
    "D3_COSIMULATED_SYSTEM",
    "D4_HIL_SIL",
    "D5_BENCH_EXPERIMENT",
    "D6_FIELD_TRIAL",
    "D7_ENGINEERING_REVIEW",
    "D8_REGULATORY_CERTIFICATION",
)


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


@dataclass(frozen=True)
class SystemEvidenceReceipt:
    receipt_id: str
    tier: str
    artifact_sha256: str
    provenance: str
    method: str
    limitations: tuple[str, ...]
    metadata: Mapping[str, Any]
    origin: str = "internal_software"
    certification_claim: bool = False

    def validate(self) -> None:
        if not self.receipt_id.strip() or not self.provenance.strip() or not self.method.strip() or not self.origin.strip():
            raise ValueError("receipt identifiers, provenance, method and origin are required")
        if self.tier not in EVIDENCE_TIERS:
            raise ValueError("unknown evidence tier")
        if not _is_sha256(self.artifact_sha256):
            raise ValueError("artifact_sha256 must be a SHA-256 hexadecimal digest")
        if not self.limitations or any(not item.strip() for item in self.limitations):
            raise ValueError("at least one explicit limitation is required")
        if self.certification_claim and self.tier != "D8_REGULATORY_CERTIFICATION":
            raise ValueError("certification_claim is only syntactically valid for D8 receipts")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["limitations"] = list(self.limitations)
        payload["metadata"] = dict(self.metadata)
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
class SystemEvidenceLedger:
    receipts: tuple[SystemEvidenceReceipt, ...]
    assessments: tuple[ReceiptAssessment, ...]
    accepted_tiers: tuple[str, ...]
    highest_supported_tier: str | None
    contiguous_tier: str | None
    missing_lower_tiers: tuple[str, ...]
    external_certification_receipt_present: bool
    automatic_model_promotion: bool
    software_granted_certification: bool
    evidence_hash: str
    physics_certified: bool = False
    software_certified: bool = False
    regulatory_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipts": [item.to_dict() for item in self.receipts],
            "assessments": [item.to_dict() for item in self.assessments],
            "accepted_tiers": list(self.accepted_tiers),
            "highest_supported_tier": self.highest_supported_tier,
            "contiguous_tier": self.contiguous_tier,
            "missing_lower_tiers": list(self.missing_lower_tiers),
            "external_certification_receipt_present": self.external_certification_receipt_present,
            "automatic_model_promotion": self.automatic_model_promotion,
            "software_granted_certification": self.software_granted_certification,
            "evidence_hash": self.evidence_hash,
            "physics_certified": self.physics_certified,
            "software_certified": self.software_certified,
            "regulatory_certified": self.regulatory_certified,
            "limitations": [
                "accepted receipt metadata is not independently verified by this package",
                "tier continuity organizes evidence but does not prove correctness",
                "regulatory status can only be established by the relevant external authority",
            ],
        }


def _missing(metadata: Mapping[str, Any], keys: Sequence[str]) -> list[str]:
    return [key for key in keys if key not in metadata or metadata[key] in (None, "", (), [], {})]


def assess_receipt(receipt: SystemEvidenceReceipt) -> ReceiptAssessment:
    receipt.validate()
    metadata = receipt.metadata
    blockers: list[str] = []
    warnings: list[str] = []
    requirements: dict[str, tuple[str, ...]] = {
        "D0_STRUCTURE": ("blueprint_hash", "component_count", "connection_count", "interface_contract_count"),
        "D1_UNIT_TESTED": ("test_count", "passed_test_count", "test_definition_hash", "runtime_environment"),
        "D2_SIMULATED_COMPONENT": ("model_ids", "governing_equations", "parameters", "initial_conditions", "finite"),
        "D3_COSIMULATED_SYSTEM": ("interface_contracts", "integration_step_s", "energy_ledger", "timing_model", "finite"),
        "D4_HIL_SIL": ("hardware_ids", "firmware_hash", "timing_log_hash", "safety_interlocks", "raw_logs_retained"),
        "D5_BENCH_EXPERIMENT": ("instrumentation", "calibration_ids", "uncertainty_budget", "raw_data_hash", "test_article_id"),
        "D6_FIELD_TRIAL": ("environment", "operator", "incident_log_hash", "rollback_plan", "supervised"),
        "D7_ENGINEERING_REVIEW": ("reviewer", "discipline", "scope", "signed_artifact_hash", "independence_statement"),
        "D8_REGULATORY_CERTIFICATION": ("authority", "certificate_id", "scope", "expiry", "independently_verified"),
    }
    for key in _missing(metadata, requirements[receipt.tier]):
        blockers.append(f"missing_metadata:{key}")
    if receipt.tier == "D1_UNIT_TESTED":
        if metadata.get("test_count", 0) < 1:
            blockers.append("test_count_must_be_positive")
        if metadata.get("passed_test_count") != metadata.get("test_count"):
            blockers.append("not_all_declared_tests_passed")
    if receipt.tier in ("D2_SIMULATED_COMPONENT", "D3_COSIMULATED_SYSTEM") and metadata.get("finite") is not True:
        blockers.append("simulation_not_declared_finite")
    if receipt.tier == "D3_COSIMULATED_SYSTEM":
        if not isinstance(metadata.get("integration_step_s"), (int, float)) or metadata.get("integration_step_s", 0) <= 0:
            blockers.append("integration_step_must_be_positive")
    if receipt.tier == "D4_HIL_SIL":
        if metadata.get("raw_logs_retained") is not True:
            blockers.append("hil_sil_raw_logs_not_retained")
        if not metadata.get("safety_interlocks"):
            blockers.append("hil_sil_requires_safety_interlocks")
    if receipt.tier == "D5_BENCH_EXPERIMENT":
        uncertainty = metadata.get("uncertainty_budget")
        if not isinstance(uncertainty, Mapping) or not uncertainty:
            blockers.append("bench_test_requires_nonempty_uncertainty_budget")
        if not _is_sha256(metadata.get("raw_data_hash")):
            blockers.append("bench_raw_data_hash_invalid")
    if receipt.tier == "D6_FIELD_TRIAL":
        if metadata.get("supervised") is not True:
            blockers.append("field_trial_must_be_supervised_in_r0_1")
        if not metadata.get("rollback_plan"):
            blockers.append("field_trial_requires_rollback_plan")
    if receipt.tier == "D7_ENGINEERING_REVIEW":
        if not _is_sha256(metadata.get("signed_artifact_hash")):
            blockers.append("engineering_review_signature_hash_invalid")
    if receipt.tier == "D8_REGULATORY_CERTIFICATION":
        if receipt.origin == "internal_software":
            blockers.append("internal_software_cannot_issue_regulatory_certification")
        if metadata.get("independently_verified") is not True:
            blockers.append("regulatory_receipt_not_independently_verified")
        if not receipt.certification_claim:
            warnings.append("external_receipt_present_without_active_certification_claim")
    elif receipt.certification_claim:
        blockers.append("certification_claim_outside_D8")
    if receipt.origin == "synthetic_fixture":
        warnings.append("synthetic_fixture_not_real_world_evidence")
    return ReceiptAssessment(
        receipt_id=receipt.receipt_id,
        tier=receipt.tier,
        accepted=not blockers,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def assess_evidence_ledger(receipts: Sequence[SystemEvidenceReceipt]) -> SystemEvidenceLedger:
    if not receipts:
        raise ValueError("at least one evidence receipt is required")
    receipt_ids: set[str] = set()
    ordered = sorted(receipts, key=lambda item: (EVIDENCE_TIERS.index(item.tier), item.receipt_id))
    for receipt in ordered:
        receipt.validate()
        if receipt.receipt_id in receipt_ids:
            raise ValueError("duplicate receipt_id")
        receipt_ids.add(receipt.receipt_id)
    assessments = tuple(assess_receipt(item) for item in ordered)
    accepted = tuple(
        tier
        for tier in EVIDENCE_TIERS
        if any(item.accepted and item.tier == tier for item in assessments)
    )
    highest = accepted[-1] if accepted else None
    contiguous: str | None = None
    missing: list[str] = []
    gap_seen = False
    for tier in EVIDENCE_TIERS:
        if tier in accepted and not gap_seen:
            contiguous = tier
        elif tier not in accepted:
            gap_seen = True
            if highest is not None and EVIDENCE_TIERS.index(tier) < EVIDENCE_TIERS.index(highest):
                missing.append(tier)
    external_d8 = any(
        assessment.accepted
        and receipt.tier == "D8_REGULATORY_CERTIFICATION"
        and receipt.origin != "internal_software"
        for receipt, assessment in zip(ordered, assessments)
    )
    payload = {
        "receipts": [item.to_dict() for item in ordered],
        "assessments": [item.to_dict() for item in assessments],
        "accepted_tiers": accepted,
        "highest_supported_tier": highest,
        "contiguous_tier": contiguous,
        "missing_lower_tiers": missing,
        "external_certification_receipt_present": external_d8,
    }
    return SystemEvidenceLedger(
        receipts=tuple(ordered),
        assessments=assessments,
        accepted_tiers=accepted,
        highest_supported_tier=highest,
        contiguous_tier=contiguous,
        missing_lower_tiers=tuple(missing),
        external_certification_receipt_present=external_d8,
        automatic_model_promotion=False,
        software_granted_certification=False,
        evidence_hash=_stable_hash(payload),
    )


def computational_demo_receipts(
    *,
    blueprint_hash: str,
    simulation_hash: str,
    test_definition_hash: str,
    test_count: int,
) -> tuple[SystemEvidenceReceipt, ...]:
    if not all(_is_sha256(value) for value in (blueprint_hash, simulation_hash, test_definition_hash)):
        raise ValueError("demo receipt hashes must be SHA-256 digests")
    return (
        SystemEvidenceReceipt(
            receipt_id="cps-d0-blueprint",
            tier="D0_STRUCTURE",
            artifact_sha256=blueprint_hash,
            provenance="omega_cyber_physical_systems_t.models",
            method="typed multi-domain blueprint validation",
            limitations=("interface completeness does not establish physical correctness",),
            metadata={
                "blueprint_hash": blueprint_hash,
                "component_count": 7,
                "connection_count": 6,
                "interface_contract_count": 6,
            },
        ),
        SystemEvidenceReceipt(
            receipt_id="cps-d1-tests",
            tier="D1_UNIT_TESTED",
            artifact_sha256=test_definition_hash,
            provenance="GitHub Actions synthetic regression fixture",
            method="deterministic Python tests",
            limitations=("tests cover declared fixtures rather than all implementations",),
            metadata={
                "test_count": test_count,
                "passed_test_count": test_count,
                "test_definition_hash": test_definition_hash,
                "runtime_environment": "CPython 3.11 on ubuntu-24.04",
            },
        ),
        SystemEvidenceReceipt(
            receipt_id="cps-d2-components",
            tier="D2_SIMULATED_COMPONENT",
            artifact_sha256=simulation_hash,
            provenance="omega_cyber_physical_systems_t.dynamics",
            method="linear lumped component simulation",
            limitations=("no hardware calibration or nonlinear saturation validation",),
            metadata={
                "model_ids": ["mass-spring-damper-r0.1", "dc-motor-electromechanical-r0.1"],
                "governing_equations": "declared state-space ODEs",
                "parameters": "embedded in immutable model receipts",
                "initial_conditions": "explicit deterministic fixtures",
                "finite": True,
            },
        ),
        SystemEvidenceReceipt(
            receipt_id="cps-d3-cosim",
            tier="D3_COSIMULATED_SYSTEM",
            artifact_sha256=simulation_hash,
            provenance="omega_cyber_physical_systems_t.cosim",
            method="fixed-step electromechanical-electronic-software co-simulation",
            limitations=("synthetic timing, thermal and component parameters",),
            metadata={
                "interface_contracts": ["power", "torque-speed", "force-velocity", "measurement", "command"],
                "integration_step_s": 0.0002,
                "energy_ledger": "electrical and positive mechanical integrals",
                "timing_model": "sampled PID with synthetic compute-time deadline",
                "finite": True,
            },
        ),
    )
