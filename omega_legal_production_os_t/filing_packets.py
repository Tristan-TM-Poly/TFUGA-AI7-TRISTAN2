"""Verified government and incorporation filing packets.

This module produces real, content-addressed submission packages and records
official portal receipts. It does not authenticate to, scrape, or submit through
a government portal.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping
import zipfile

from .models import canonicalize, detect_forbidden_payload_keys, hash_payload


_PACKET_ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,79}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_ALLOWED_JURISDICTIONS = frozenset({"QC", "CA"})
_ALLOWED_TYPES = frozenset(
    {
        "INCORPORATION",
        "INITIAL_DECLARATION",
        "ANNUAL_RETURN",
        "CURRENT_UPDATE",
        "BENEFICIAL_OWNERSHIP_UPDATE",
        "TAX_REGISTRATION",
        "OTHER",
    }
)


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _safe_name(value: str) -> str:
    name = Path(value).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    if not cleaned:
        raise ValueError("document filename is empty after sanitization")
    return cleaned


@dataclass(frozen=True, slots=True)
class FilingDocument:
    role: str
    path: str
    sha256: str
    required: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FilingDocument":
        return cls(
            role=str(data["role"]).strip().upper(),
            path=str(data["path"]),
            sha256=str(data["sha256"]),
            required=bool(data.get("required", True)),
        )

    def validate(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.role:
            reasons.append("document_role_missing")
        if not _SHA256.fullmatch(self.sha256):
            reasons.append(f"document_hash_invalid:{self.role}")
        path = Path(self.path)
        if not path.is_file():
            reasons.append(f"document_missing:{self.role}")
        else:
            actual = sha256_bytes(path.read_bytes())
            if actual != self.sha256:
                reasons.append(f"document_hash_mismatch:{self.role}")
        return tuple(reasons)


@dataclass(frozen=True, slots=True)
class GovernmentFilingPacket:
    packet_id: str
    company_id: str
    legal_name: str
    jurisdiction: str
    filing_type: str
    professional_review_hash: str
    founder_approval_hash: str
    documents: tuple[FilingDocument, ...]
    portal_name: str
    attestation_required: bool = True
    metadata: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "GovernmentFilingPacket":
        return cls(
            packet_id=str(data["packet_id"]),
            company_id=str(data["company_id"]),
            legal_name=str(data["legal_name"]),
            jurisdiction=str(data["jurisdiction"]).upper(),
            filing_type=str(data["filing_type"]).upper(),
            professional_review_hash=str(data["professional_review_hash"]),
            founder_approval_hash=str(data["founder_approval_hash"]),
            documents=tuple(FilingDocument.from_mapping(item) for item in data.get("documents", [])),
            portal_name=str(data["portal_name"]),
            attestation_required=bool(data.get("attestation_required", True)),
            metadata=dict(data.get("metadata", {})),
        )

    def request_payload(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "company_id": self.company_id,
            "legal_name": self.legal_name,
            "jurisdiction": self.jurisdiction,
            "filing_type": self.filing_type,
            "professional_review_hash": self.professional_review_hash,
            "founder_approval_hash": self.founder_approval_hash,
            "documents": [
                {
                    "role": item.role,
                    "path": _safe_name(item.path),
                    "sha256": item.sha256,
                    "required": item.required,
                }
                for item in self.documents
            ],
            "portal_name": self.portal_name,
            "attestation_required": self.attestation_required,
            "metadata": canonicalize(self.metadata or {}),
        }

    @property
    def packet_hash(self) -> str:
        return hash_payload(self.request_payload())

    def validate(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not _PACKET_ID.fullmatch(self.packet_id):
            reasons.append("packet_id_invalid")
        if not self.company_id.strip() or not self.legal_name.strip() or not self.portal_name.strip():
            reasons.append("company_legal_name_or_portal_missing")
        if self.jurisdiction not in _ALLOWED_JURISDICTIONS:
            reasons.append("jurisdiction_invalid")
        if self.filing_type not in _ALLOWED_TYPES:
            reasons.append("filing_type_invalid")
        if not _SHA256.fullmatch(self.professional_review_hash):
            reasons.append("professional_review_hash_invalid")
        if not _SHA256.fullmatch(self.founder_approval_hash):
            reasons.append("founder_approval_hash_invalid")
        forbidden = detect_forbidden_payload_keys(self.metadata or {}, path="metadata")
        reasons.extend(f"secret_like_key:{item}" for item in forbidden)
        if not self.documents:
            reasons.append("documents_missing")
        roles: set[str] = set()
        names: set[str] = set()
        for document in self.documents:
            reasons.extend(document.validate())
            if document.role in roles:
                reasons.append(f"duplicate_document_role:{document.role}")
            roles.add(document.role)
            safe_name = _safe_name(document.path)
            if safe_name in names:
                reasons.append(f"duplicate_document_filename:{safe_name}")
            names.add(safe_name)
        if self.filing_type == "INCORPORATION":
            required_roles = {
                "ARTICLES",
                "REGISTERED_OFFICE",
                "DIRECTORS",
                "SHARE_STRUCTURE",
            }
            missing = sorted(required_roles - roles)
            reasons.extend(f"incorporation_role_missing:{role}" for role in missing)
        return tuple(sorted(set(reasons)))


def load_packet(path: str | Path) -> GovernmentFilingPacket:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("filing manifest must contain a JSON object")
    packet = GovernmentFilingPacket.from_mapping(data)
    reasons = packet.validate()
    if reasons:
        raise ValueError("invalid filing packet: " + ",".join(reasons))
    supplied = data.get("packet_hash")
    if supplied is not None and supplied != packet.packet_hash:
        raise ValueError("packet_hash does not match canonical content")
    return packet


def build_packet(manifest_path: str | Path, output_zip: str | Path) -> dict[str, Any]:
    packet = load_packet(manifest_path)
    output = Path(output_zip)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = packet.request_payload()
    manifest["packet_hash"] = packet.packet_hash
    manifest["status"] = "READY_FOR_AUTHORIZED_PORTAL_SUBMISSION"
    checklist = {
        "packet_id": packet.packet_id,
        "packet_hash": packet.packet_hash,
        "portal_name": packet.portal_name,
        "attestation_required": packet.attestation_required,
        "human_steps": [
            "authenticate_to_official_portal",
            "verify_every_displayed_field_against_packet",
            "perform_required_human_attestation",
            "approve_filing_fee_if_applicable",
            "submit_once",
            "download_official_receipt",
            "record_receipt_with_omega_legal_real",
        ],
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        archive.writestr("submission_checklist.json", json.dumps(checklist, indent=2, sort_keys=True) + "\n")
        for document in packet.documents:
            archive.write(document.path, arcname=f"documents/{_safe_name(document.path)}")
    archive_hash = sha256_bytes(output.read_bytes())
    return {
        "schema": "omega-government-filing-handoff-v1",
        "packet_id": packet.packet_id,
        "packet_hash": packet.packet_hash,
        "archive_path": str(output),
        "archive_hash": archive_hash,
        "documents": len(packet.documents),
        "status": "READY_FOR_AUTHORIZED_PORTAL_SUBMISSION",
    }


def record_official_receipt(
    *,
    packet_manifest_path: str | Path,
    official_receipt_path: str | Path,
    reference_number: str,
    status: str,
    output_path: str | Path,
) -> dict[str, Any]:
    packet = load_packet(packet_manifest_path)
    receipt_file = Path(official_receipt_path)
    if not receipt_file.is_file():
        raise ValueError("official receipt file does not exist")
    normalized_status = status.strip().upper()
    if normalized_status not in {"SUBMITTED", "ACCEPTED", "REJECTED", "REQUIRES_CORRECTION"}:
        raise ValueError("official filing status is invalid")
    if not reference_number.strip():
        raise ValueError("official reference number is required")
    result = {
        "schema": "omega-government-filing-receipt-v1",
        "packet_id": packet.packet_id,
        "packet_hash": packet.packet_hash,
        "official_reference_hash": sha256_bytes(reference_number.strip().encode()),
        "official_receipt_hash": sha256_bytes(receipt_file.read_bytes()),
        "status": normalized_status,
        "effect_confirmed": normalized_status in {"ACCEPTED", "REJECTED", "REQUIRES_CORRECTION"},
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
