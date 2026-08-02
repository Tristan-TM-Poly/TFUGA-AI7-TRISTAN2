from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from omega_legal_production_os_t.filing_packets import (
    build_packet,
    load_packet,
    record_official_receipt,
)


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_manifest(tmp_path: Path) -> Path:
    roles = {
        "ARTICLES": b"articles-v1",
        "REGISTERED_OFFICE": b"registered-office-v1",
        "DIRECTORS": b"directors-v1",
        "SHARE_STRUCTURE": b"share-structure-v1",
    }
    documents = []
    for role, data in roles.items():
        path = tmp_path / f"{role.lower()}.txt"
        path.write_bytes(data)
        documents.append({"role": role, "path": str(path), "sha256": sha256(data)})
    manifest = {
        "packet_id": "FILE-QC-001",
        "company_id": "tristan_parent_opco",
        "legal_name": "Tristan Parent OpCo — candidate name",
        "jurisdiction": "QC",
        "filing_type": "INCORPORATION",
        "professional_review_hash": "sha256:" + "a" * 64,
        "founder_approval_hash": "sha256:" + "b" * 64,
        "portal_name": "Registraire des entreprises",
        "attestation_required": True,
        "documents": documents,
        "metadata": {"language": "fr", "version": 1},
    }
    path = tmp_path / "filing.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_build_real_content_addressed_filing_zip(tmp_path: Path) -> None:
    manifest_path = make_manifest(tmp_path)
    output = tmp_path / "packet.zip"
    result = build_packet(manifest_path, output)
    assert result["status"] == "READY_FOR_AUTHORIZED_PORTAL_SUBMISSION"
    assert result["documents"] == 4
    assert output.is_file()
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "submission_checklist.json" in names
        assert "documents/articles.txt" in names
        embedded = json.loads(archive.read("manifest.json"))
        assert embedded["packet_hash"] == result["packet_hash"]
        assert embedded["status"] == "READY_FOR_AUTHORIZED_PORTAL_SUBMISSION"


def test_missing_incorporation_role_is_blocked(tmp_path: Path) -> None:
    manifest_path = make_manifest(tmp_path)
    data = json.loads(manifest_path.read_text())
    data["documents"] = [item for item in data["documents"] if item["role"] != "DIRECTORS"]
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="incorporation_role_missing:DIRECTORS"):
        load_packet(manifest_path)


def test_document_tampering_is_blocked(tmp_path: Path) -> None:
    manifest_path = make_manifest(tmp_path)
    data = json.loads(manifest_path.read_text())
    Path(data["documents"][0]["path"]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="document_hash_mismatch"):
        build_packet(manifest_path, tmp_path / "packet.zip")


def test_secret_like_metadata_is_blocked(tmp_path: Path) -> None:
    manifest_path = make_manifest(tmp_path)
    data = json.loads(manifest_path.read_text())
    data["metadata"]["portal_password"] = "do-not-store"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="secret_like_key"):
        load_packet(manifest_path)


def test_record_official_receipt_hashes_reference_and_document(tmp_path: Path) -> None:
    manifest_path = make_manifest(tmp_path)
    official = tmp_path / "official-receipt.pdf"
    official.write_bytes(b"official portal receipt")
    output = tmp_path / "recorded.json"
    result = record_official_receipt(
        packet_manifest_path=manifest_path,
        official_receipt_path=official,
        reference_number="QC-2026-123456",
        status="ACCEPTED",
        output_path=output,
    )
    assert result["status"] == "ACCEPTED"
    assert result["effect_confirmed"] is True
    assert result["official_receipt_hash"] == sha256(b"official portal receipt")
    assert "QC-2026-123456" not in output.read_text()
