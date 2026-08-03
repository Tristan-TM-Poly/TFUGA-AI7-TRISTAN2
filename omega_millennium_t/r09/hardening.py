"""Additional fail-closed semantic validation for R0.9."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable

from .model import PromotionRequest, parse_zoned_datetime, stable_digest


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _base_reference(value: str) -> str:
    return value.split("#", 1)[0]


def _metadata_reference_ids(check_kind: str, metadata: dict[str, Any]) -> list[str]:
    keys_by_kind = {
        "novelty_review": ("comparison_reference_ids",),
        "dataset_terms": ("dataset_terms_refs",),
        "competition_rules": ("official_rules_reference_id",),
        "prize_recognition": ("official_authority_reference_id",),
        "citations": ("citation_reference_ids",),
    }
    result: list[str] = []
    for key in keys_by_kind.get(check_kind, ()):
        value = metadata.get(key)
        if isinstance(value, list):
            result.extend(_base_reference(str(item)) for item in value)
        elif isinstance(value, str) and value:
            result.append(_base_reference(value))
    return result


def evaluate_request_hardened(
    request: PromotionRequest,
    base_evaluator: Callable[[PromotionRequest], dict[str, Any]],
) -> dict[str, Any]:
    evaluation = base_evaluator(request)
    receipt = dict(evaluation["receipt"])
    blockers = list(receipt["blockers"])
    evidence_ids = {item.reference_id for item in request.evidence}
    requested_at = parse_zoned_datetime(request.requested_at, "requested_at")

    for evidence in request.evidence:
        observed_at = parse_zoned_datetime(evidence.observed_at, "observed_at")
        if observed_at > requested_at:
            blockers.append(f"evidence_after_request:{evidence.reference_id}")

    for check in request.checks:
        reviewed_at = parse_zoned_datetime(check.reviewed_at, "reviewed_at")
        if reviewed_at > requested_at:
            blockers.append(f"review_after_request:{check.check_id}")

        metadata = dict(check.metadata)
        digest_keys: tuple[str, ...] = ()
        if check.check_kind == "independent_reconstruction":
            digest_keys = ("environment_digest",)
        elif check.check_kind == "reproducibility_snapshot":
            digest_keys = ("code_digest", "environment_digest")
            data_digest = metadata.get("data_digest")
            if data_digest != "none" and not _is_sha256(data_digest):
                blockers.append(f"check_metadata_not_sha256:{check.check_id}:data_digest")
        elif check.check_kind == "statement_scope":
            digest_keys = ("statement_digest",)
        for key in digest_keys:
            if not _is_sha256(metadata.get(key)):
                blockers.append(f"check_metadata_not_sha256:{check.check_id}:{key}")

        missing_metadata_refs = sorted(
            set(_metadata_reference_ids(check.check_kind, metadata)) - evidence_ids
        )
        if missing_metadata_refs:
            blockers.append(
                f"check_metadata_reference_missing:{check.check_id}:{','.join(missing_metadata_refs)}"
            )

        if check.check_kind in {"literature_search", "prior_art_search"}:
            cutoff = metadata.get("search_cutoff")
            try:
                cutoff_date = date.fromisoformat(str(cutoff))
            except ValueError:
                blockers.append(f"search_cutoff_invalid:{check.check_id}")
            else:
                if cutoff_date > requested_at.date():
                    blockers.append(f"search_cutoff_after_request:{check.check_id}")

    for signature in request.signatures:
        signed_at = parse_zoned_datetime(signature.signed_at, "signed_at")
        if signed_at < requested_at:
            blockers.append(f"signature_before_request:{signature.signature_id}")
        if signature.method in {"pgp", "sigstore"}:
            if ":" not in signature.signature_ref or signature.signature_ref.startswith("sha256:"):
                blockers.append(f"external_signature_reference_invalid:{signature.signature_id}")

    blockers = sorted(set(blockers))
    receipt["blockers"] = blockers
    receipt["gate_ready"] = not blockers
    receipt["receipt_digest"] = stable_digest(
        {key: value for key, value in receipt.items() if key != "receipt_digest"}
    )
    return {"receipt": receipt, "checklist": evaluation["checklist"]}
