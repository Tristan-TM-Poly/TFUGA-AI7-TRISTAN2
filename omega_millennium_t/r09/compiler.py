from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import (
    BUNDLE_SCHEMA,
    CHECK_KINDS,
    MANDATORY_BY_DESTINATION,
    MANDATORY_BY_STATUS,
    REPORT_SCHEMA,
    REVIEW_REQUIRED_CHECKS,
    CheckAttestation,
    PromotionRequest,
    canonical_json,
    load_request,
    stable_digest,
    write_json,
    write_jsonl,
)

PUBLIC_DESTINATIONS = {
    "public_preprint",
    "journal_submission",
    "competition_submission",
    "prize_claim",
    "patent_filing",
    "open_source_release",
    "public_talk",
}

PUBLIC_DISCLOSURE_DESTINATIONS = {
    "public_preprint",
    "journal_submission",
    "competition_submission",
    "open_source_release",
    "public_talk",
}

INDEPENDENT_ROLES = {
    "independent_reviewer",
    "external_reviewer",
    "formal_verifier",
    "ip_reviewer",
    "competition_officer",
    "official_authority",
}

DISALLOWED_REVIEWER_ROLES = {"author", "coauthor", "model", "generator", "assistant", "owner"}


def _required_checks(request: PromotionRequest) -> set[str]:
    return set(MANDATORY_BY_STATUS[request.status]) | set(MANDATORY_BY_DESTINATION[request.destination])


def _check_map(request: PromotionRequest) -> dict[str, list[CheckAttestation]]:
    grouped: dict[str, list[CheckAttestation]] = {kind: [] for kind in CHECK_KINDS}
    for check in request.checks:
        grouped[check.check_kind].append(check)
    return grouped


def _validate_reference_integrity(request: PromotionRequest) -> list[str]:
    blockers: list[str] = []
    reference_ids = {item.reference_id for item in request.evidence}
    for check in request.checks:
        missing = sorted(set(check.evidence_reference_ids) - reference_ids)
        if missing:
            blockers.append(f"check_missing_evidence:{check.check_id}:{','.join(missing)}")
    return blockers


def _is_independent(request: PromotionRequest, check: CheckAttestation) -> bool:
    return (
        check.reviewer_id not in request.author_ids
        and check.reviewer_role in INDEPENDENT_ROLES
        and check.reviewer_role not in DISALLOWED_REVIEWER_ROLES
    )


def _require_metadata_list(
    check: CheckAttestation,
    key: str,
    blockers: list[str],
    *,
    minimum: int = 1,
) -> list[Any]:
    value = check.metadata.get(key)
    if not isinstance(value, list) or len(value) < minimum:
        blockers.append(f"check_metadata_missing:{check.check_id}:{key}")
        return []
    return value


def _require_metadata_string(check: CheckAttestation, key: str, blockers: list[str]) -> str:
    value = str(check.metadata.get(key, "")).strip()
    if not value:
        blockers.append(f"check_metadata_missing:{check.check_id}:{key}")
    return value


def _validate_check_semantics(request: PromotionRequest, check: CheckAttestation) -> list[str]:
    blockers: list[str] = []
    kind = check.check_kind
    if kind in REVIEW_REQUIRED_CHECKS and not _is_independent(request, check):
        blockers.append(f"independence_required:{check.check_id}")

    if kind in {"literature_search", "prior_art_search"}:
        _require_metadata_list(check, "queries", blockers)
        _require_metadata_list(check, "databases", blockers)
        source_count = check.metadata.get("source_count")
        if not isinstance(source_count, int) or source_count < 1:
            blockers.append(f"check_metadata_invalid:{check.check_id}:source_count")
        _require_metadata_string(check, "search_cutoff", blockers)

    elif kind == "novelty_review":
        _require_metadata_list(check, "comparison_reference_ids", blockers)
        conclusion = _require_metadata_string(check, "conclusion", blockers)
        if conclusion not in {"no_conflict_found", "overlap_found", "not_novel", "inconclusive"}:
            blockers.append(f"check_metadata_invalid:{check.check_id}:conclusion")
        if conclusion in {"overlap_found", "not_novel", "inconclusive"} and check.outcome == "pass":
            blockers.append(f"novelty_outcome_conflict:{check.check_id}")

    elif kind == "independent_reconstruction":
        result = _require_metadata_string(check, "result", blockers)
        if result not in {"reproduced", "partial", "failed"}:
            blockers.append(f"check_metadata_invalid:{check.check_id}:result")
        _require_metadata_string(check, "environment_digest", blockers)
        _require_metadata_string(check, "replay_command", blockers)
        if result != "reproduced" and check.outcome == "pass":
            blockers.append(f"reconstruction_outcome_conflict:{check.check_id}")

    elif kind == "reproducibility_snapshot":
        for key in ("code_digest", "environment_digest", "replay_command"):
            _require_metadata_string(check, key, blockers)
        if "data_digest" not in check.metadata:
            blockers.append(f"check_metadata_missing:{check.check_id}:data_digest")

    elif kind in {"dependency_audit", "hidden_assumption_audit"}:
        _require_metadata_list(check, "items_reviewed", blockers)
        unresolved = check.metadata.get("unresolved_count")
        if not isinstance(unresolved, int) or unresolved < 0:
            blockers.append(f"check_metadata_invalid:{check.check_id}:unresolved_count")
        elif unresolved > 0 and check.outcome == "pass":
            blockers.append(f"unresolved_items_conflict:{check.check_id}")

    elif kind == "formal_verification":
        _require_metadata_string(check, "checker", blockers)
        _require_metadata_string(check, "checker_version", blockers)
        if not isinstance(check.metadata.get("kernel_checked"), bool):
            blockers.append(f"check_metadata_invalid:{check.check_id}:kernel_checked")
        if request.status == "formal_artifact" and check.metadata.get("kernel_checked") is not True:
            blockers.append(f"formal_artifact_not_kernel_checked:{check.check_id}")

    elif kind == "negative_results":
        included = check.metadata.get("m_minus_records_included")
        if not isinstance(included, int) or included < 0:
            blockers.append(f"check_metadata_invalid:{check.check_id}:m_minus_records_included")
        elif included != len(request.m_minus_records):
            blockers.append(f"m_minus_coverage_mismatch:{check.check_id}")

    elif kind == "authorship":
        declared = check.metadata.get("declared_author_ids")
        if not isinstance(declared, list) or sorted(map(str, declared)) != sorted(request.author_ids):
            blockers.append(f"authorship_mismatch:{check.check_id}")
        _require_metadata_string(check, "contribution_statement_ref", blockers)

    elif kind == "license_copyright":
        _require_metadata_list(check, "licenses_reviewed", blockers)
        _require_metadata_string(check, "copyright_owner", blockers)
        if check.metadata.get("redistribution_permitted") is not True and request.destination in PUBLIC_DISCLOSURE_DESTINATIONS:
            blockers.append(f"redistribution_not_permitted:{check.check_id}")

    elif kind == "dataset_terms":
        datasets_used = check.metadata.get("datasets_used")
        if not isinstance(datasets_used, bool):
            blockers.append(f"check_metadata_invalid:{check.check_id}:datasets_used")
        if datasets_used is True:
            _require_metadata_list(check, "dataset_terms_refs", blockers)
            if check.metadata.get("redistribution_permitted") is not True and request.destination in PUBLIC_DISCLOSURE_DESTINATIONS:
                blockers.append(f"dataset_redistribution_not_permitted:{check.check_id}")

    elif kind == "competition_rules":
        _require_metadata_string(check, "official_rules_reference_id", blockers)
        _require_metadata_string(check, "competition_name", blockers)
        if check.metadata.get("eligibility_confirmed") is not True:
            blockers.append(f"competition_eligibility_unconfirmed:{check.check_id}")
        if check.reviewer_role not in {"independent_reviewer", "competition_officer", "official_authority"}:
            blockers.append(f"competition_reviewer_role_invalid:{check.check_id}")

    elif kind == "prize_recognition":
        _require_metadata_string(check, "official_authority_reference_id", blockers)
        status = _require_metadata_string(check, "official_award_status", blockers)
        if status != "awarded":
            blockers.append(f"official_prize_not_awarded:{check.check_id}")
        if check.reviewer_role != "official_authority":
            blockers.append(f"official_authority_required:{check.check_id}")
        if check.reviewer_id in request.author_ids:
            blockers.append(f"official_authority_not_independent:{check.check_id}")

    elif kind == "ip_decision":
        decision = _require_metadata_string(check, "decision", blockers)
        if decision != request.ip_decision:
            blockers.append(f"ip_decision_mismatch:{check.check_id}")
        _require_metadata_string(check, "rationale", blockers)
        _require_metadata_string(check, "disclosure_state", blockers)
        if check.reviewer_role not in {"ip_reviewer", "independent_reviewer"}:
            blockers.append(f"ip_reviewer_role_invalid:{check.check_id}")

    elif kind == "statement_scope":
        _require_metadata_string(check, "statement_digest", blockers)
        _require_metadata_list(check, "assumptions", blockers, minimum=0)
        expected = stable_digest(
            {"exact_statement": request.exact_statement, "assumptions": list(request.assumptions)}
        )
        if check.metadata.get("statement_digest") != expected:
            blockers.append(f"statement_digest_mismatch:{check.check_id}")
        if list(check.metadata.get("assumptions", [])) != list(request.assumptions):
            blockers.append(f"statement_assumptions_mismatch:{check.check_id}")

    elif kind == "limitations":
        limitations = _require_metadata_list(check, "declared_limitations", blockers)
        if not limitations:
            blockers.append(f"limitations_empty:{check.check_id}")

    elif kind == "citations":
        _require_metadata_list(check, "citation_reference_ids", blockers)
        _require_metadata_string(check, "citation_style", blockers)

    return blockers


def _validate_ip_compatibility(request: PromotionRequest) -> list[str]:
    blockers: list[str] = []
    decision = request.ip_decision
    destination = request.destination
    if destination in PUBLIC_DISCLOSURE_DESTINATIONS and decision in {"secret", "abandon"}:
        blockers.append(f"ip_destination_conflict:{decision}->{destination}")
    if destination == "patent_filing" and decision != "patent":
        blockers.append("patent_destination_requires_patent_decision")
    if destination == "open_source_release" and decision != "open_source":
        blockers.append("open_source_destination_requires_open_source_decision")
    if destination in {"public_preprint", "journal_submission", "public_talk"} and decision not in {
        "publish",
        "open_source",
        "patent",
    }:
        blockers.append(f"public_destination_ip_decision_invalid:{decision}")
    if destination == "prize_claim" and request.status != "independently_reviewed_result":
        blockers.append("prize_claim_requires_independently_reviewed_result")
    return blockers


def _signature_payload(request: PromotionRequest) -> dict[str, Any]:
    return {
        "schema": BUNDLE_SCHEMA,
        "request_id": request.request_id,
        "canonical_problem_id": request.canonical_problem_id,
        "artifact_id": request.artifact_id,
        "title": request.title,
        "exact_statement": request.exact_statement,
        "assumptions": list(request.assumptions),
        "status": request.status,
        "destination": request.destination,
        "author_ids": list(request.author_ids),
        "ip_decision": request.ip_decision,
        "requested_at": request.requested_at,
        "evidence_digests": sorted(item.source_digest for item in request.evidence),
        "check_digests": sorted(stable_digest(item.to_dict()) for item in request.checks),
        "m_minus_digest": stable_digest([dict(item) for item in request.m_minus_records]),
    }


def _validate_signatures(request: PromotionRequest) -> tuple[list[str], str]:
    blockers: list[str] = []
    payload_digest = stable_digest(_signature_payload(request))
    if not request.signatures:
        blockers.append("signed_receipt_missing")
        return blockers, payload_digest
    independent_gate_signers = 0
    ip_signers = 0
    for signature in request.signatures:
        if signature.payload_digest != payload_digest:
            blockers.append(f"signature_payload_mismatch:{signature.signature_id}")
        if signature.signer_id in request.author_ids:
            blockers.append(f"signature_self_approval_forbidden:{signature.signature_id}")
        if signature.signer_role in {"independent_reviewer", "external_reviewer", "formal_verifier"}:
            independent_gate_signers += 1
        if signature.signer_role == "ip_reviewer":
            ip_signers += 1
        if signature.method == "sha256_detached":
            expected_ref = f"sha256:{payload_digest}"
            if signature.signature_ref != expected_ref:
                blockers.append(f"detached_signature_mismatch:{signature.signature_id}")
            if request.destination in PUBLIC_DESTINATIONS:
                blockers.append(f"authenticated_signature_required:{signature.signature_id}")
    if independent_gate_signers < 1:
        blockers.append("independent_gate_signature_missing")
    if request.destination in PUBLIC_DESTINATIONS and ip_signers < 1:
        blockers.append("ip_signature_missing")
    return blockers, payload_digest


def _checklist(request: PromotionRequest) -> tuple[list[dict[str, Any]], list[str]]:
    required = _required_checks(request)
    grouped = _check_map(request)
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for kind in sorted(CHECK_KINDS):
        attestations = grouped[kind]
        mandatory = kind in required
        passing = [item for item in attestations if item.outcome == "pass"]
        failing = [item for item in attestations if item.outcome == "fail"]
        not_applicable = [item for item in attestations if item.outcome == "not_applicable"]
        item_blockers: list[str] = []
        if mandatory and not passing:
            item_blockers.append(f"mandatory_check_not_passed:{kind}")
        if failing:
            item_blockers.extend(f"check_failed:{item.check_id}" for item in failing)
        if mandatory and not_applicable and not passing:
            item_blockers.append(f"mandatory_check_marked_not_applicable:{kind}")
        for attestation in attestations:
            item_blockers.extend(_validate_check_semantics(request, attestation))
        item_blockers = sorted(set(item_blockers))
        blockers.extend(item_blockers)
        row = {
            "check_kind": kind,
            "mandatory": mandatory,
            "attestation_ids": sorted(item.check_id for item in attestations),
            "pass_count": len(passing),
            "fail_count": len(failing),
            "not_applicable_count": len(not_applicable),
            "status": "blocked" if item_blockers else ("passed" if passing else "optional_missing"),
            "blockers": item_blockers,
        }
        row["checklist_digest"] = stable_digest(row)
        rows.append(row)
    return rows, blockers


def evaluate_request(request: PromotionRequest) -> dict[str, Any]:
    checklist, blockers = _checklist(request)
    blockers.extend(_validate_reference_integrity(request))
    blockers.extend(_validate_ip_compatibility(request))
    signature_blockers, signature_payload_digest = _validate_signatures(request)
    blockers.extend(signature_blockers)

    if request.destination != "prize_claim":
        prize_checks = [item for item in request.checks if item.check_kind == "prize_recognition"]
        if any(item.outcome == "pass" for item in prize_checks):
            blockers.append("prize_recognition_outside_prize_claim_forbidden")

    if request.destination == "internal_archive" and request.ip_decision == "abandon":
        # Abandon remains auditable but cannot be promoted beyond internal archive.
        pass

    blockers = sorted(set(blockers))
    gate_ready = not blockers
    receipt = {
        "schema": REPORT_SCHEMA,
        "request_id": request.request_id,
        "canonical_problem_id": request.canonical_problem_id,
        "artifact_id": request.artifact_id,
        "status": request.status,
        "destination": request.destination,
        "ip_decision": request.ip_decision,
        "gate_ready": gate_ready,
        "blockers": blockers,
        "required_check_kinds": sorted(_required_checks(request)),
        "checklist_digest": stable_digest(checklist),
        "signature_payload_digest": signature_payload_digest,
        "signature_count": len(request.signatures),
        "evidence_reference_count": len(request.evidence),
        "m_minus_record_count": len(request.m_minus_records),
        "dry_run": True,
        "external_action_performed": False,
        "submission_performed": False,
        "publication_performed": False,
        "patent_filing_performed": False,
        "public_disclosure_performed": False,
        "prize_claim_submitted": False,
        "prize_or_clay_recognition_inferred": False,
        "novelty_or_correctness_self_approved": False,
        "mathematical_truth_probability_claimed": False,
        "proof_claimed_by_gate": False,
        "solution_claimed_by_gate": False,
    }
    receipt["receipt_digest"] = stable_digest(receipt)
    return {"receipt": receipt, "checklist": checklist}


def _publication_bundle(request: PromotionRequest, receipt: Mapping[str, Any]) -> dict[str, Any]:
    limitations: list[str] = []
    citations: list[str] = []
    for check in request.checks:
        limitations.extend(check.limitations)
        if check.check_kind == "limitations":
            value = check.metadata.get("declared_limitations", [])
            if isinstance(value, list):
                limitations.extend(str(item) for item in value)
        if check.check_kind == "citations":
            value = check.metadata.get("citation_reference_ids", [])
            if isinstance(value, list):
                citations.extend(str(item) for item in value)
    bundle = {
        "schema": "omega-problem-publication-bundle/9",
        "request_id": request.request_id,
        "canonical_problem_id": request.canonical_problem_id,
        "artifact_id": request.artifact_id,
        "title": request.title,
        "exact_statement": request.exact_statement,
        "assumptions": list(request.assumptions),
        "status": request.status,
        "destination": request.destination,
        "ip_decision": request.ip_decision,
        "author_ids": list(request.author_ids),
        "citation_reference_ids": sorted(set(citations)),
        "limitations": sorted(set(item for item in limitations if item)),
        "evidence": [item.to_dict() for item in request.evidence],
        "m_minus_history": [dict(item) for item in request.m_minus_records],
        "gate_receipt_digest": receipt["receipt_digest"],
        "ready_for_human_review": receipt["gate_ready"],
        "dry_run": True,
        "external_action_performed": False,
        "disclaimer": (
            "This bundle is an auditable dry-run artifact. It is not a publication, submission, "
            "patent filing, prize application, recognition, proof certificate or solution claim."
        ),
    }
    bundle["bundle_digest"] = stable_digest(bundle)
    return bundle


def _render_summary(request: PromotionRequest, receipt: Mapping[str, Any]) -> str:
    blocker_lines = "\n".join(f"- `{item}`" for item in receipt["blockers"]) or "- None"
    return (
        f"# Promotion gate — {request.title}\n\n"
        f"- Request: `{request.request_id}`\n"
        f"- Status: `{request.status}`\n"
        f"- Destination: `{request.destination}`\n"
        f"- IP decision: `{request.ip_decision}`\n"
        f"- Gate ready: `{str(receipt['gate_ready']).lower()}`\n"
        f"- Dry run: `true`\n"
        f"- External action performed: `false`\n\n"
        "## Blockers\n\n"
        f"{blocker_lines}\n\n"
        "## Non-claims\n\n"
        "This gate does not establish mathematical truth, novelty, correctness, publication, "
        "competition eligibility, prize recognition, patentability or solution of an open problem.\n"
    )


def compile_promotion_gate(
    bundle_path: str | Path,
    output_dir: str | Path,
    *,
    clean: bool = True,
) -> dict[str, Any]:
    request = load_request(bundle_path)
    output = Path(output_dir)
    if output.exists() and clean:
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    evaluation = evaluate_request(request)
    receipt = evaluation["receipt"]
    checklist = evaluation["checklist"]
    publication_bundle = _publication_bundle(request, receipt)

    write_json(output / "request.json", request.to_dict())
    write_jsonl(output / "checklist.jsonl", checklist)
    write_json(output / "promotion_receipt.json", receipt)
    write_json(output / "publication_bundle.json", publication_bundle)
    (output / "SUMMARY.md").write_text(_render_summary(request, receipt), encoding="utf-8")

    file_digests = {
        path.name: stable_digest(path.read_text(encoding="utf-8"))
        for path in sorted(output.iterdir())
        if path.is_file()
    }
    manifest = {
        "schema": "omega-problem-promotion-manifest/9",
        "request_id": request.request_id,
        "file_digests": file_digests,
        "file_count": len(file_digests),
        "gate_ready": receipt["gate_ready"],
        "dry_run": True,
        "external_action_performed": False,
    }
    manifest["manifest_digest"] = stable_digest(manifest)
    write_json(output / "manifest.json", manifest)

    report = {
        "schema": REPORT_SCHEMA,
        "request_id": request.request_id,
        "output_dir": str(output),
        "gate_ready": receipt["gate_ready"],
        "blocker_count": len(receipt["blockers"]),
        "check_count": len(checklist),
        "mandatory_check_count": sum(1 for item in checklist if item["mandatory"]),
        "passed_mandatory_check_count": sum(
            1 for item in checklist if item["mandatory"] and item["status"] == "passed"
        ),
        "evidence_reference_count": len(request.evidence),
        "signature_count": len(request.signatures),
        "m_minus_record_count": len(request.m_minus_records),
        "receipt_digest": receipt["receipt_digest"],
        "publication_bundle_digest": publication_bundle["bundle_digest"],
        "manifest_digest": manifest["manifest_digest"],
        "dry_run": True,
        "external_action_performed": False,
        "proof_claimed": False,
        "solution_claimed": False,
        "novelty_claimed_by_compiler": False,
        "prize_recognition_claimed": False,
    }
    report["report_digest"] = stable_digest(report)
    write_json(output / "report.json", report)
    return report
