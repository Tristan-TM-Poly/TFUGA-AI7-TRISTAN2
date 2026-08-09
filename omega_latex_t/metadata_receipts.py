from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping


class MetadataReceiptError(ValueError):
    pass

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)


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


def metadata_receipt(payload: Mapping[str, Any], *, provider: str = "crossref") -> dict[str, Any]:
    provider_name = str(provider).strip().lower()
    if provider_name not in {"crossref", "datacite", "openalex", "manual"}:
        raise MetadataReceiptError(f"unsupported provider {provider!r}")
    doi_raw = payload.get("DOI", payload.get("doi", ""))
    doi = normalize_doi(doi_raw) if doi_raw else ""
    title = payload.get("title", "")
    if isinstance(title, list): title = title[0] if title else ""
    author = payload.get("author", ())
    normalized = {
        "provider": provider_name,
        "doi": doi,
        "title": str(title),
        "author": author if isinstance(author, list) else [],
        "issued": payload.get("issued", payload.get("published", {})),
        "type": str(payload.get("type", "")),
        "publisher": str(payload.get("publisher", "")),
        "container_title": payload.get("container-title", payload.get("container_title", "")),
    }
    raw_hash = sha256(_canonical(dict(payload))).hexdigest()
    normalized_hash = sha256(_canonical(normalized)).hexdigest()
    return {
        "schema_version": "1.0.0",
        "provider": provider_name,
        "doi": doi,
        "normalized": normalized,
        "raw_metadata_sha256": raw_hash,
        "normalized_metadata_sha256": normalized_hash,
        "boundary": "metadata identity receipt only; provider metadata does not prove article claims, peer review quality, reproducibility, ownership or current legal status",
    }


def metadata_receipt_report(doc: Any) -> dict[str, Any]:
    provenance = dict(getattr(doc, "provenance", {}) or {})
    raw = provenance.get("metadata_receipts", ())
    entries = []
    for index, item in enumerate(raw if isinstance(raw, (list, tuple)) else ()):
        if not isinstance(item, Mapping):
            entries.append({"index": index, "valid": False, "reasons": ["receipt_not_object"]})
            continue
        reasons = []
        for field in ("provider", "raw_metadata_sha256", "normalized_metadata_sha256"):
            if not str(item.get(field, "")).strip(): reasons.append(f"missing_{field}")
        doi = str(item.get("doi", ""))
        if doi:
            try: normalize_doi(doi)
            except MetadataReceiptError: reasons.append("invalid_doi")
        entries.append({"index": index, "valid": not reasons, "receipt": dict(item), "reasons": reasons})
    return {"semantic_hash": getattr(doc, "semantic_hash", lambda: "")(), "entries": entries, "valid_count": sum(1 for x in entries if x.get("valid") is True), "boundary": "metadata receipts attest normalized metadata identity only; they do not certify source claims or publication quality"}
