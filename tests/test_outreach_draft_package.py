from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "OUT-2026-0003"
DRAFT_PATH = ROOT / "company_outreach" / "drafts" / f"{CASE_ID}.md"
MANIFEST_PATH = ROOT / "company_outreach" / "drafts" / f"{CASE_ID}.manifest.json"
CASE_PATH = ROOT / "company_outreach" / "cases" / f"{CASE_ID}.json"
EVIDENCE_PATH = ROOT / "company_outreach" / "evidence" / f"{CASE_ID}.evidence.json"


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def extract_email_body(markdown: str) -> str:
    marker = "# Corps du courriel\n\n"
    end_marker = "\n# Verrou d’exécution"
    assert marker in markdown
    assert end_marker in markdown
    return markdown.split(marker, 1)[1].split(end_marker, 1)[0]


def test_draft_hashes_match_exact_content() -> None:
    draft = DRAFT_PATH.read_text(encoding="utf-8")
    manifest = load_json(MANIFEST_PATH)
    case = load_json(CASE_PATH)

    subject = draft.split("# Objet\n\n", 1)[1].split("\n\n# Corps du courriel", 1)[0]
    body = extract_email_body(draft)

    assert sha256_text(subject) == manifest["content"]["subject_hash"]
    assert sha256_text(body) == manifest["content"]["body_hash"]
    assert subject == case["subject"]


def test_manifest_package_hash_is_canonical() -> None:
    manifest = load_json(MANIFEST_PATH)
    stored_hash = manifest.pop("package_hash")
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert sha256_text(canonical) == stored_hash


def test_package_is_non_executable_and_not_sent() -> None:
    manifest = load_json(MANIFEST_PATH)
    case = load_json(CASE_PATH)

    assert manifest["status"] == "PREPARED_NOT_SENT"
    assert manifest["execution"] == {
        "allowed": False,
        "approval_state": "not_requested",
        "campaign": False,
        "requires_private_recipient_resolution": True,
        "requires_separate_explicit_authorization": True,
        "transport": "none",
    }
    assert case["status"] == "prepared"
    assert case["sent_at"] is None
    assert case["provider_receipt_hash"] is None
    assert case["thread_hash"] is None


def test_repository_contains_no_raw_recipient_address() -> None:
    forbidden = "m.charest" + "@" + "laval.ca"
    for path in (DRAFT_PATH, MANIFEST_PATH, CASE_PATH, EVIDENCE_PATH):
        assert forbidden not in path.read_text(encoding="utf-8").lower()


def test_evidence_uses_public_official_sources() -> None:
    evidence = load_json(EVIDENCE_PATH)
    assert evidence["evidence_status"] == "public_sources_verified"
    assert len(evidence["findings"]) >= 3
    assert all(
        finding["source_url"].startswith("https://lavaleconomique.com/")
        for finding in evidence["findings"]
    )
    assert evidence["privacy"]["raw_recipient_address_in_repository"] is False
