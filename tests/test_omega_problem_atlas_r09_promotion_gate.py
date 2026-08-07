from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r09 import audit_promotion_gate, compile_promotion_gate
from omega_millennium_t.r09.compiler import _required_checks, _signature_payload
from omega_millennium_t.r09.model import BUNDLE_SCHEMA, PromotionRequest, stable_digest

NOW = "2026-08-03T18:00:00Z"
SOURCE_DIGEST = "a" * 64
ENV_DIGEST = "b" * 64
CODE_DIGEST = "c" * 64
DATA_DIGEST = "d" * 64


def _metadata(kind: str, authors: list[str], statement: str, assumptions: list[str], mminus_count: int) -> dict:
    if kind in {"literature_search", "prior_art_search"}:
        return {
            "queries": ["exact statement", "closest prior theorem"],
            "databases": ["Crossref", "zbMATH", "arXiv"],
            "source_count": 12,
            "search_cutoff": "2026-08-03",
        }
    if kind == "novelty_review":
        return {
            "comparison_reference_ids": ["ref.primary"],
            "conclusion": "no_conflict_found",
        }
    if kind == "independent_reconstruction":
        return {
            "result": "reproduced",
            "environment_digest": ENV_DIGEST,
            "replay_command": "python -m fixture.replay",
        }
    if kind == "reproducibility_snapshot":
        return {
            "code_digest": CODE_DIGEST,
            "data_digest": DATA_DIGEST,
            "environment_digest": ENV_DIGEST,
            "replay_command": "python -m fixture.replay",
        }
    if kind in {"dependency_audit", "hidden_assumption_audit"}:
        return {"items_reviewed": ["dep.one", "dep.two"], "unresolved_count": 0}
    if kind == "formal_verification":
        return {"checker": "Lean", "checker_version": "4.fixture", "kernel_checked": True}
    if kind == "negative_results":
        return {"m_minus_records_included": mminus_count}
    if kind == "authorship":
        return {
            "declared_author_ids": authors,
            "contribution_statement_ref": "ref.primary#contributions",
        }
    if kind == "license_copyright":
        return {
            "licenses_reviewed": ["MIT", "CC-BY-4.0"],
            "copyright_owner": authors[0],
            "redistribution_permitted": True,
        }
    if kind == "dataset_terms":
        return {
            "datasets_used": True,
            "dataset_terms_refs": ["ref.primary#dataset-terms"],
            "redistribution_permitted": True,
        }
    if kind == "competition_rules":
        return {
            "official_rules_reference_id": "ref.primary",
            "competition_name": "Fixture Competition",
            "eligibility_confirmed": True,
        }
    if kind == "prize_recognition":
        return {
            "official_authority_reference_id": "ref.primary",
            "official_award_status": "awarded",
        }
    if kind == "ip_decision":
        return {
            "decision": "publish",
            "rationale": "Publication selected after prior-art review.",
            "disclosure_state": "not_publicly_disclosed",
        }
    if kind == "statement_scope":
        return {
            "statement_digest": stable_digest(
                {"exact_statement": statement, "assumptions": assumptions}
            ),
            "assumptions": assumptions,
        }
    if kind == "limitations":
        return {"declared_limitations": ["Fixture only", "No general proof claim"]}
    if kind == "citations":
        return {
            "citation_reference_ids": ["ref.primary"],
            "citation_style": "numeric",
        }
    raise AssertionError(kind)


def _role(kind: str) -> str:
    if kind == "formal_verification":
        return "formal_verifier"
    if kind == "ip_decision":
        return "ip_reviewer"
    if kind == "competition_rules":
        return "competition_officer"
    if kind == "prize_recognition":
        return "official_authority"
    return "independent_reviewer"


def _build_bundle(
    *,
    status: str = "manuscript",
    destination: str = "public_preprint",
    ip_decision: str = "publish",
    public_signature_method: str = "pgp",
) -> dict:
    authors = ["author.fixture"]
    statement = "For every fixture x satisfying H, property P(x) holds."
    assumptions = ["H is finite", "the fixture arithmetic is exact"]
    mminus = [
        {
            "record_id": "mminus.fixture.001",
            "kind": "failed_method",
            "summary": "Naive extrapolation failed on a boundary case.",
            "source_ref": "ref.primary#negative-result",
        }
    ]
    evidence = [
        {
            "reference_id": "ref.primary",
            "source_uri": "fixture://primary",
            "source_digest": SOURCE_DIGEST,
            "observed_at": NOW,
            "location": "fixture section 1",
            "license_note": "Synthetic fixture; redistribution permitted.",
            "metadata": {"source_type": "fixture"},
        }
    ]
    probe = {
        "schema": BUNDLE_SCHEMA,
        "request_id": "promotion.fixture.001",
        "canonical_problem_id": "problem::fixture",
        "artifact_id": "artifact::fixture",
        "title": "Fixture result",
        "exact_statement": statement,
        "assumptions": assumptions,
        "status": status,
        "destination": destination,
        "author_ids": authors,
        "ip_decision": ip_decision,
        "requested_at": NOW,
        "evidence": evidence,
        "checks": [],
        "signatures": [],
        "m_minus_records": mminus,
        "metadata": {"fixture": True},
    }
    request_probe = PromotionRequest.from_dict(probe)
    required = _required_checks(request_probe)
    checks = []
    for index, kind in enumerate(sorted(required), start=1):
        metadata = _metadata(kind, authors, statement, assumptions, len(mminus))
        if kind == "ip_decision":
            metadata["decision"] = ip_decision
        checks.append(
            {
                "check_id": f"check.{index:02d}.{kind}",
                "check_kind": kind,
                "outcome": "pass",
                "scope": f"Full fixture scope for {kind}",
                "reviewer_id": f"reviewer.{kind}",
                "reviewer_role": _role(kind),
                "reviewed_at": NOW,
                "evidence_reference_ids": ["ref.primary"],
                "limitations": ["Synthetic fixture only"],
                "metadata": metadata,
            }
        )
    probe["checks"] = checks
    unsigned = PromotionRequest.from_dict(probe)
    payload_digest = stable_digest(_signature_payload(unsigned))
    if destination == "internal_archive":
        signatures = [
            {
                "signature_id": "sig.gate",
                "signer_id": "reviewer.gate",
                "signer_role": "independent_reviewer",
                "signed_at": NOW,
                "method": "sha256_detached",
                "signature_ref": f"sha256:{payload_digest}",
                "payload_digest": payload_digest,
            }
        ]
    else:
        signatures = [
            {
                "signature_id": "sig.gate",
                "signer_id": "reviewer.gate",
                "signer_role": "independent_reviewer",
                "signed_at": NOW,
                "method": public_signature_method,
                "signature_ref": "fixture://signature/gate",
                "payload_digest": payload_digest,
            },
            {
                "signature_id": "sig.ip",
                "signer_id": "reviewer.ip",
                "signer_role": "ip_reviewer",
                "signed_at": NOW,
                "method": "sigstore",
                "signature_ref": "fixture://signature/ip",
                "payload_digest": payload_digest,
            },
        ]
    probe["signatures"] = signatures
    return probe


def _write_bundle(tmp_path: Path, bundle: dict, name: str = "bundle.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    return path


def test_valid_public_preprint_is_deterministic_and_dry_run(tmp_path: Path) -> None:
    bundle_path = _write_bundle(tmp_path, _build_bundle())
    output_a = tmp_path / "out-a"
    output_b = tmp_path / "out-b"
    report_a = compile_promotion_gate(bundle_path, output_a)
    report_b = compile_promotion_gate(bundle_path, output_b)
    assert report_a == report_b
    assert report_a["gate_ready"] is True
    assert report_a["external_action_performed"] is False
    assert sorted(path.name for path in output_a.iterdir()) == sorted(path.name for path in output_b.iterdir())
    for path_a in sorted(output_a.iterdir()):
        assert path_a.read_bytes() == (output_b / path_a.name).read_bytes()
    receipt = json.loads((output_a / "promotion_receipt.json").read_text(encoding="utf-8"))
    assert receipt["publication_performed"] is False
    assert receipt["submission_performed"] is False
    assert receipt["prize_or_clay_recognition_inferred"] is False
    assert audit_promotion_gate(output_a)["valid"] is True


def test_internal_archive_accepts_non_authenticating_fixture_signature(tmp_path: Path) -> None:
    bundle = _build_bundle(
        status="experiment",
        destination="internal_archive",
        ip_decision="abandon",
    )
    path = _write_bundle(tmp_path, bundle)
    report = compile_promotion_gate(path, tmp_path / "out")
    assert report["gate_ready"] is True
    assert audit_promotion_gate(tmp_path / "out")["valid"] is True


def test_missing_mandatory_novelty_review_blocks(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["checks"] = [item for item in bundle["checks"] if item["check_kind"] != "novelty_review"]
    path = _write_bundle(tmp_path, bundle)
    compile_promotion_gate(path, tmp_path / "out")
    receipt = json.loads((tmp_path / "out" / "promotion_receipt.json").read_text(encoding="utf-8"))
    assert receipt["gate_ready"] is False
    assert "mandatory_check_not_passed:novelty_review" in receipt["blockers"]


def test_nested_self_approval_field_is_rejected(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["metadata"] = {"generated_assessment": {"novel": True}}
    with pytest.raises(ValueError, match="self-approval field"):
        compile_promotion_gate(_write_bundle(tmp_path, bundle), tmp_path / "out")


def test_public_destination_rejects_sha256_only_signature(tmp_path: Path) -> None:
    bundle = _build_bundle(public_signature_method="sha256_detached")
    digest = bundle["signatures"][0]["payload_digest"]
    bundle["signatures"][0]["signature_ref"] = f"sha256:{digest}"
    path = _write_bundle(tmp_path, bundle)
    compile_promotion_gate(path, tmp_path / "out")
    receipt = json.loads((tmp_path / "out" / "promotion_receipt.json").read_text(encoding="utf-8"))
    assert receipt["gate_ready"] is False
    assert any(item.startswith("authenticated_signature_required:") for item in receipt["blockers"])


def test_author_cannot_sign_independent_gate_receipt(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["signatures"][0]["signer_id"] = bundle["author_ids"][0]
    path = _write_bundle(tmp_path, bundle)
    compile_promotion_gate(path, tmp_path / "out")
    receipt = json.loads((tmp_path / "out" / "promotion_receipt.json").read_text(encoding="utf-8"))
    assert receipt["gate_ready"] is False
    assert "signature_self_approval_forbidden:sig.gate" in receipt["blockers"]


def test_secret_ip_decision_blocks_public_preprint(tmp_path: Path) -> None:
    bundle = _build_bundle(ip_decision="secret")
    path = _write_bundle(tmp_path, bundle)
    compile_promotion_gate(path, tmp_path / "out")
    receipt = json.loads((tmp_path / "out" / "promotion_receipt.json").read_text(encoding="utf-8"))
    assert receipt["gate_ready"] is False
    assert "ip_destination_conflict:secret->public_preprint" in receipt["blockers"]


def test_prize_claim_requires_official_award(tmp_path: Path) -> None:
    bundle = _build_bundle(
        status="independently_reviewed_result",
        destination="prize_claim",
        ip_decision="publish",
    )
    prize = next(item for item in bundle["checks"] if item["check_kind"] == "prize_recognition")
    prize["metadata"]["official_award_status"] = "nominated"
    path = _write_bundle(tmp_path, bundle)
    compile_promotion_gate(path, tmp_path / "out")
    receipt = json.loads((tmp_path / "out" / "promotion_receipt.json").read_text(encoding="utf-8"))
    assert receipt["gate_ready"] is False
    assert any(item.startswith("official_prize_not_awarded:") for item in receipt["blockers"])
    assert receipt["prize_claim_submitted"] is False


def test_model_cannot_self_approve_novelty(tmp_path: Path) -> None:
    bundle = _build_bundle()
    novelty = next(item for item in bundle["checks"] if item["check_kind"] == "novelty_review")
    novelty["reviewer_role"] = "model"
    path = _write_bundle(tmp_path, bundle)
    compile_promotion_gate(path, tmp_path / "out")
    receipt = json.loads((tmp_path / "out" / "promotion_receipt.json").read_text(encoding="utf-8"))
    assert receipt["gate_ready"] is False
    assert any(item.startswith("independence_required:") for item in receipt["blockers"])


def test_tampering_is_detected_by_replay_audit(tmp_path: Path) -> None:
    bundle_path = _write_bundle(tmp_path, _build_bundle())
    output = tmp_path / "out"
    compile_promotion_gate(bundle_path, output)
    receipt_path = output / "promotion_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["gate_ready"] = False
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    audit = audit_promotion_gate(output)
    assert audit["valid"] is False
    assert "receipt_replay_mismatch" in audit["errors"]


def test_unknown_bundle_field_fails_closed(tmp_path: Path) -> None:
    bundle = _build_bundle()
    bundle["submit_now"] = True
    with pytest.raises(ValueError, match="unknown promotion-bundle fields"):
        compile_promotion_gate(_write_bundle(tmp_path, bundle), tmp_path / "out")
