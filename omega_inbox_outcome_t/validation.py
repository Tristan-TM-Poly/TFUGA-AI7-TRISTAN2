"""OAK validation for deliverables."""
from __future__ import annotations

from pathlib import Path

from .models import CaseRecord, DataClass, DeliverableManifest, ValidationResult, ValidationStatus
from .security import sha256_value


def validate_deliverable(case: CaseRecord, manifest: DeliverableManifest) -> ValidationResult:
    checks = {
        "completeness": bool(manifest.outputs),
        "provenance": all("sha256" in output for output in manifest.outputs),
        "files_exist": all(Path(output["path"]).exists() for output in manifest.outputs),
        "identity": case.identity.identity_confidence >= 0.50,
        "authority": case.identity.authority_confidence >= 0.50,
        "privacy": manifest.data_class not in {DataClass.PERSONAL, DataClass.RESTRICTED, DataClass.SECRET},
        "ip": case.analysis.primary_intent.value not in {"IP_OR_CONFIDENTIAL"},
        "claim_support": all(claim.get("source") and claim.get("status") == "verified" for claim in manifest.claims),
    }
    reasons: list[str] = []
    warnings: list[str] = []

    if not checks["completeness"] or not checks["files_exist"]:
        status = ValidationStatus.REGENERATE
        reasons.append("missing_or_unmaterialized_output")
    elif not checks["provenance"]:
        status = ValidationStatus.BLOCK
        reasons.append("missing_output_hash")
    elif not checks["identity"] or not checks["authority"]:
        status = ValidationStatus.REQUIRE_INFORMATION
        reasons.append("identity_or_authority_insufficient")
    elif not checks["privacy"] or not checks["ip"]:
        status = ValidationStatus.REQUIRE_APPROVAL
        reasons.append("privacy_or_ip_review_required")
    elif manifest.deliverable_type in {"commercial_proposal_draft", "invoice_draft", "professional_review_packet"}:
        status = ValidationStatus.REQUIRE_APPROVAL
        reasons.append("commitment_or_professional_domain")
    elif all(checks.values()):
        status = ValidationStatus.PASS
    else:
        status = ValidationStatus.PASS_WITH_WARNINGS
        warnings.extend(name for name, value in checks.items() if not value)

    manifest.validation = {"status": status.value, "checks": checks, "reasons": reasons, "warnings": warnings}
    manifest.approved_hash = sha256_value({"outputs": manifest.outputs, "validation": manifest.validation}) if status is ValidationStatus.PASS else None
    manifest.status = "VALIDATED" if status is ValidationStatus.PASS else status.value
    return ValidationResult(manifest.deliverable_id, status, checks, tuple(reasons), tuple(warnings))
