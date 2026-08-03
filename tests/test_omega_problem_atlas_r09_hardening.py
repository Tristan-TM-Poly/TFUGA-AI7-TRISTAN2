from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

from omega_millennium_t.r09 import compile_promotion_gate


def _fixtures() -> dict:
    return runpy.run_path("tests/test_omega_problem_atlas_r09_promotion_gate.py")


def _compile(tmp_path: Path, bundle: dict) -> dict:
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    output = tmp_path / "output"
    compile_promotion_gate(bundle_path, output)
    return json.loads((output / "promotion_receipt.json").read_text(encoding="utf-8"))


def test_missing_evidence_reference_blocks(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["checks"][0]["evidence_reference_ids"] = ["ref.missing"]
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert any(item.startswith("check_missing_evidence:") for item in receipt["blockers"])


def test_invalid_source_digest_is_rejected(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["evidence"][0]["source_digest"] = "not-a-digest"
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        compile_promotion_gate(bundle_path, tmp_path / "output")


def test_unzoned_review_date_is_rejected(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    bundle["checks"][0]["reviewed_at"] = "2026-08-03T18:00:00"
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(ValueError, match="timezone"):
        compile_promotion_gate(bundle_path, tmp_path / "output")


def test_formal_artifact_requires_kernel_checked_receipt(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"](
        status="formal_artifact",
        destination="internal_archive",
        ip_decision="publish",
    )
    formal = next(item for item in bundle["checks"] if item["check_kind"] == "formal_verification")
    formal["metadata"]["kernel_checked"] = False
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert any(item.startswith("formal_artifact_not_kernel_checked:") for item in receipt["blockers"])


def test_mminus_history_count_must_match(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    negative = next(item for item in bundle["checks"] if item["check_kind"] == "negative_results")
    negative["metadata"]["m_minus_records_included"] = 0
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert any(item.startswith("m_minus_coverage_mismatch:") for item in receipt["blockers"])


def test_competition_submission_requires_confirmed_eligibility(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"](
        status="manuscript",
        destination="competition_submission",
        ip_decision="publish",
    )
    rules = next(item for item in bundle["checks"] if item["check_kind"] == "competition_rules")
    rules["metadata"]["eligibility_confirmed"] = False
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert any(item.startswith("competition_eligibility_unconfirmed:") for item in receipt["blockers"])
    assert receipt["submission_performed"] is False


def test_prize_recognition_check_outside_prize_claim_is_blocked(tmp_path: Path) -> None:
    fixture = _fixtures()
    bundle = fixture["_build_bundle"]()
    authors = bundle["author_ids"]
    prize_check = {
        "check_id": "check.extra.prize",
        "check_kind": "prize_recognition",
        "outcome": "pass",
        "scope": "Fixture prize scope",
        "reviewer_id": "authority.fixture",
        "reviewer_role": "official_authority",
        "reviewed_at": fixture["NOW"],
        "evidence_reference_ids": ["ref.primary"],
        "limitations": ["Fixture only"],
        "metadata": fixture["_metadata"](
            "prize_recognition",
            authors,
            bundle["exact_statement"],
            bundle["assumptions"],
            len(bundle["m_minus_records"]),
        ),
    }
    bundle["checks"].append(prize_check)
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert "prize_recognition_outside_prize_claim_forbidden" in receipt["blockers"]


def test_patent_filing_requires_patent_ip_decision(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"](
        status="manuscript",
        destination="patent_filing",
        ip_decision="publish",
    )
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert "patent_destination_requires_patent_decision" in receipt["blockers"]
    assert receipt["patent_filing_performed"] is False


def test_open_source_release_requires_open_source_decision(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"](
        status="experiment",
        destination="open_source_release",
        ip_decision="publish",
    )
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert "open_source_destination_requires_open_source_decision" in receipt["blockers"]
    assert receipt["public_disclosure_performed"] is False


def test_not_applicable_cannot_satisfy_mandatory_check(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    novelty = next(item for item in bundle["checks"] if item["check_kind"] == "novelty_review")
    novelty["outcome"] = "not_applicable"
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert "mandatory_check_not_passed:novelty_review" in receipt["blockers"]
    assert "mandatory_check_marked_not_applicable:novelty_review" in receipt["blockers"]


def test_explicit_failed_check_always_blocks(tmp_path: Path) -> None:
    bundle = _fixtures()["_build_bundle"]()
    literature = next(item for item in bundle["checks"] if item["check_kind"] == "literature_search")
    literature["outcome"] = "fail"
    receipt = _compile(tmp_path, bundle)
    assert receipt["gate_ready"] is False
    assert f"check_failed:{literature['check_id']}" in receipt["blockers"]
