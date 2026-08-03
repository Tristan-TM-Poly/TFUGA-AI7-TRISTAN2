from __future__ import annotations

import json
from pathlib import Path

from omega_millennium_t.r04 import (
    audit_source_bundle,
    compile_source_bundle,
    load_source_snapshot,
)


FIXTURE_DIR = Path("data/omega_problem_atlas_r04")


def _write_snapshot(path: Path, *, records: list[dict], **overrides: object) -> Path:
    payload = {
        "schema": "omega-problem-source-snapshot/4",
        "snapshot_id": "test-primary-snapshot",
        "source_id": "clay",
        "source_url": "https://www.claymath.org/millennium-problems/",
        "retrieved_at": "2026-08-03T16:00:00Z",
        "revision": None,
        "retrieval_mode": "manual_reviewed_primary_snapshot",
        "license_note": "Test metadata only.",
        "records": records,
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_sample_snapshots_compile_deterministically(tmp_path: Path) -> None:
    inputs = (
        FIXTURE_DIR / "clay_snapshot.sample.json",
        FIXTURE_DIR / "formal_conjectures_snapshot.sample.json",
    )
    first = tmp_path / "first"
    second = tmp_path / "second"
    report_a = compile_source_bundle(inputs, first)
    report_b = compile_source_bundle(tuple(reversed(inputs)), second)

    assert report_a == report_b
    assert report_a["snapshot_count"] == 2
    assert report_a["input_record_count"] == 5
    assert report_a["accepted_import_count"] == 5
    assert report_a["quarantine_count"] == 0
    assert report_a["current_open_claim_count"] == 0
    assert report_a["solution_claim_count"] == 0
    assert report_a["source_retrieval_certified"] is False
    assert report_a["current_status_certification_claimed"] is False
    assert report_a["permanent_total_cap"] is None
    assert audit_source_bundle(first)["valid"] is True
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    assert (first / "imports.jsonl").read_bytes() == (second / "imports.jsonl").read_bytes()


def test_revision_pinned_source_rejects_missing_revision(tmp_path: Path) -> None:
    path = tmp_path / "formal.json"
    _write_snapshot(
        path,
        records=[],
        source_id="formal_conjectures",
        source_url="https://github.com/google-deepmind/formal-conjectures",
        revision=None,
    )
    try:
        load_source_snapshot(path)
    except ValueError as exc:
        assert "requires revision" in str(exc)
    else:
        raise AssertionError("missing revision should fail")


def test_dated_primary_open_claim_is_accepted(tmp_path: Path) -> None:
    source = _write_snapshot(
        tmp_path / "primary.json",
        records=[
            {
                "problem_id": "riemann_hypothesis_verified_fixture",
                "title": "Riemann hypothesis verified fixture",
                "front": "analytic_number_theory",
                "observed_status": "open",
                "source_locator": "fixture:primary:riemann",
                "statement": "Test-only statement.",
                "verification_basis": "primary_source",
                "status_verified_at": "2026-08-03T16:00:00Z",
                "current_open_status_claimed": True,
                "solution_claimed": False,
            }
        ],
    )
    output = tmp_path / "bundle"
    report = compile_source_bundle((source,), output)
    imports = [json.loads(line) for line in (output / "imports.jsonl").read_text().splitlines()]
    receipts = [json.loads(line) for line in (output / "status_receipts.jsonl").read_text().splitlines()]

    assert report["accepted_import_count"] == 1
    assert report["current_open_claim_count"] == 1
    assert imports[0]["current_open_status_claimed"] is True
    assert imports[0]["source_verified_at"] == "2026-08-03T16:00:00Z"
    assert receipts[0]["claim_allowed"] is True
    assert receipts[0]["blockers"] == []
    assert audit_source_bundle(output)["valid"] is True


def test_open_claim_without_dated_receipt_is_quarantined(tmp_path: Path) -> None:
    source = _write_snapshot(
        tmp_path / "bad-open.json",
        records=[
            {
                "problem_id": "bad_open_claim",
                "title": "Bad open claim",
                "front": "graphs_hypergraphs",
                "observed_status": "open",
                "source_locator": "fixture:bad-open",
                "verification_basis": "primary_source",
                "current_open_status_claimed": True,
                "solution_claimed": False,
            }
        ],
    )
    output = tmp_path / "bundle"
    report = compile_source_bundle((source,), output)
    quarantine = [json.loads(line) for line in (output / "quarantine.jsonl").read_text().splitlines()]

    assert report["accepted_import_count"] == 0
    assert report["quarantine_count"] == 1
    assert "open_claim_missing_dated_receipt" in quarantine[0]["reason_codes"]
    assert audit_source_bundle(output)["valid"] is True


def test_solution_claim_is_quarantined(tmp_path: Path) -> None:
    source = _write_snapshot(
        tmp_path / "solution.json",
        records=[
            {
                "problem_id": "forbidden_solution",
                "title": "Forbidden solution",
                "front": "logic_foundations",
                "observed_status": "solved",
                "source_locator": "fixture:forbidden-solution",
                "verification_basis": "primary_source",
                "status_verified_at": "2026-08-03T16:00:00Z",
                "current_open_status_claimed": False,
                "solution_claimed": True,
            }
        ],
    )
    output = tmp_path / "bundle"
    report = compile_source_bundle((source,), output)
    quarantine = [json.loads(line) for line in (output / "quarantine.jsonl").read_text().splitlines()]

    assert report["accepted_import_count"] == 0
    assert report["solution_claim_count"] == 0
    assert "solution_claim_forbidden" in quarantine[0]["reason_codes"]


def test_audit_detects_import_tampering(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    compile_source_bundle((FIXTURE_DIR / "clay_snapshot.sample.json",), output)
    path = output / "imports.jsonl"
    rows = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(rows[0])
    payload["title"] += " tampered"
    rows[0] = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    audit = audit_source_bundle(output)
    assert audit["valid"] is False
    assert any("imports.jsonl: sha256 mismatch" in error for error in audit["errors"])
