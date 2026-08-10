from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping


class MetadataReceiptError(ValueError):
    pass


_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def normalize_doi(value: Any) -> str:
    doi = str(value or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):].strip()
            break
    doi = doi.lower()
    if not _DOI_RE.fullmatch(doi):
        raise MetadataReceiptError(f"invalid DOI syntax: {value!r}")
    return doi


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash_mapping(payload: Mapping[str, Any]) -> str:
    return sha256(_canonical(payload)).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return bool(_SHA256_RE.fullmatch(str(value or "").lower()))


def _normalized_metadata(payload: Mapping[str, Any], provider_name: str) -> dict[str, Any]:
    doi_raw = payload.get("DOI", payload.get("doi", ""))
    doi = normalize_doi(doi_raw) if doi_raw else ""
    title = payload.get("title", "")
    if isinstance(title, list):
        title = title[0] if title else ""
    author = payload.get("author", ())
    return {
        "provider": provider_name,
        "doi": doi,
        "title": str(title),
        "author": author if isinstance(author, list) else [],
        "issued": payload.get("issued", payload.get("published", {})),
        "type": str(payload.get("type", "")),
        "publisher": str(payload.get("publisher", "")),
        "container_title": payload.get("container-title", payload.get("container_title", "")),
    }


def metadata_receipt(payload: Mapping[str, Any], *, provider: str = "crossref") -> dict[str, Any]:
    provider_name = str(provider).strip().lower()
    if provider_name not in {"crossref", "datacite", "openalex", "manual"}:
        raise MetadataReceiptError(f"unsupported provider {provider!r}")
    raw_metadata = dict(payload)
    normalized = _normalized_metadata(raw_metadata, provider_name)
    return {
        "schema_version": "1.0.1",
        "provider": provider_name,
        "doi": normalized["doi"],
        "raw_metadata": raw_metadata,
        "normalized": normalized,
        "raw_metadata_sha256": _hash_mapping(raw_metadata),
        "normalized_metadata_sha256": _hash_mapping(normalized),
        "boundary": "self-verifying metadata identity receipt only; metadata integrity does not prove article claims, peer review quality, reproducibility, ownership or current legal status",
    }


def validate_metadata_receipt(item: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    provider = str(item.get("provider", "")).strip().lower()
    if provider not in {"crossref", "datacite", "openalex", "manual"}:
        reasons.append("invalid_provider")

    raw_hash = str(item.get("raw_metadata_sha256", "")).lower()
    normalized_hash = str(item.get("normalized_metadata_sha256", "")).lower()
    if not _valid_sha256(raw_hash):
        reasons.append("invalid_raw_metadata_sha256")
    if not _valid_sha256(normalized_hash):
        reasons.append("invalid_normalized_metadata_sha256")

    doi = str(item.get("doi", ""))
    if doi:
        try:
            normalize_doi(doi)
        except MetadataReceiptError:
            reasons.append("invalid_doi")

    normalized = item.get("normalized")
    if not isinstance(normalized, Mapping):
        reasons.append("normalized_metadata_missing")
    elif _valid_sha256(normalized_hash):
        actual = _hash_mapping(dict(normalized))
        if actual != normalized_hash:
            reasons.append("normalized_metadata_hash_mismatch")
        normalized_provider = str(normalized.get("provider", "")).strip().lower()
        if provider and normalized_provider and normalized_provider != provider:
            reasons.append("provider_mismatch")
        normalized_doi = str(normalized.get("doi", ""))
        if doi and normalized_doi and normalized_doi != doi:
            reasons.append("doi_mismatch")

    raw_metadata = item.get("raw_metadata")
    if raw_metadata is None:
        reasons.append("raw_metadata_unavailable_for_verification")
    elif not isinstance(raw_metadata, Mapping):
        reasons.append("raw_metadata_invalid")
    elif _valid_sha256(raw_hash):
        actual = _hash_mapping(dict(raw_metadata))
        if actual != raw_hash:
            reasons.append("raw_metadata_hash_mismatch")
        if isinstance(normalized, Mapping) and provider in {"crossref", "datacite", "openalex", "manual"}:
            try:
                expected_normalized = _normalized_metadata(dict(raw_metadata), provider)
            except MetadataReceiptError:
                reasons.append("raw_metadata_normalization_failed")
            else:
                if dict(normalized) != expected_normalized:
                    reasons.append("normalized_metadata_content_mismatch")

    return tuple(reasons)


def metadata_receipt_report(doc: Any) -> dict[str, Any]:
    provenance = dict(getattr(doc, "provenance", {}) or {})
    raw = provenance.get("metadata_receipts", ())
    entries = []
    for index, item in enumerate(raw if isinstance(raw, (list, tuple)) else ()):
        if not isinstance(item, Mapping):
            entries.append({"index": index, "valid": False, "verified": False, "reasons": ["receipt_not_object"]})
            continue
        reasons = list(validate_metadata_receipt(item))
        legacy_only = reasons == ["raw_metadata_unavailable_for_verification"]
        valid = not reasons or legacy_only
        verified = not reasons
        entries.append({
            "index": index,
            "valid": valid,
            "verified": verified,
            "receipt": dict(item),
            "reasons": reasons,
        })
    return {
        "semantic_hash": getattr(doc, "semantic_hash", lambda: "")(),
        "entries": entries,
        "valid_count": sum(1 for x in entries if x.get("valid") is True),
        "verified_count": sum(1 for x in entries if x.get("verified") is True),
        "boundary": "verified metadata receipts attest canonical metadata identity only; they do not certify source claims or publication quality",
    }
