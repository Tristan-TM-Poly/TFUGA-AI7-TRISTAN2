from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from omega_millennium_t.r03.atlas import build_seed_records
from omega_millennium_t.r03.max_engine import (
    METHOD_FAMILIES,
    TARGET_KINDS,
    audit_max_output,
    compile_max_atlas,
    deduplicate_records_max,
    expand_max_cells,
    expand_research_targets,
    select_balanced_portfolio,
    unicode_canonical_key,
)
from omega_millennium_t.r03.strict_audit import audit_max_output_strict


def test_max_constellation_scale_and_referential_counts() -> None:
    records = build_seed_records()
    targets = expand_research_targets(records)
    cells = expand_max_cells(records, targets)
    assert len(records) == 72
    assert len(TARGET_KINDS) == 12
    assert len(targets) == 864
    assert len(cells) == 6_912
    assert len(METHOD_FAMILIES) == 32
    assert len({target.target_id for target in targets}) == len(targets)
    assert len({cell.cell_id for cell in cells}) == len(cells)
    assert not any(target.proof_claimed or target.solution_claimed for target in targets)
    assert not any(cell.proof_claimed or cell.solution_claimed for cell in cells)


def test_scores_are_profile_based_not_hash_noise() -> None:
    records = build_seed_records()
    targets = expand_research_targets(records)
    cells = expand_max_cells(records, targets)
    same_shape = [
        cell
        for cell in cells
        if cell.attack_mode == "statement_and_provenance_audit"
        and cell.target_id.endswith("::canonical_statement")
    ]
    assert len(same_shape) == 72
    assert {cell.scoring_basis for cell in same_shape} == {"transparent_profile_v1"}
    unverified = [cell for cell in same_shape if cell.problem_id != "poincare_benchmark"]
    assert len({cell.priority_score for cell in unverified}) <= 3


def test_balanced_primary_portfolio_covers_all_fronts() -> None:
    records = build_seed_records()
    targets = expand_research_targets(records)
    cells = expand_max_cells(records, targets)
    portfolio = select_balanced_portfolio(
        cells,
        primary_budget=24,
        secondary_budget=72,
        experiment_budget=256,
    )
    assert len(portfolio["primary"]) == 24
    assert len({item["front"] for item in portfolio["primary"]}) == 24
    assert len({item["problem_id"] for item in portfolio["primary"]}) == 24
    ids = [
        item["cell_id"]
        for bucket in ("primary", "secondary", "experiments")
        for item in portfolio[bucket]
    ]
    assert len(ids) == len(set(ids))
    assert portfolio["coverage"]["fronts"] == 24
    assert portfolio["permanent_total_cap"] is None


def test_unicode_canonicalization_does_not_break_erdos_name() -> None:
    key = unicode_canonical_key("Erdős–Hajnal conjecture")
    assert key == "erdős hajnal conjecture"
    assert "erd s" not in key


def test_dedup_prefers_verified_provenance() -> None:
    seed = build_seed_records()[0]
    weak = replace(
        seed,
        problem_id="duplicate_weak",
        source_verified_at=None,
        source_locator=None,
        provenance_digest="0" * 64,
    )
    strong = replace(
        seed,
        problem_id="duplicate_strong",
        source_verified_at="2026-08-03T00:00:00Z",
        source_locator="primary:statement",
        provenance_digest="f" * 64,
    )
    result = deduplicate_records_max((weak, strong))
    assert len(result) == 1
    assert result[0].problem_id == "duplicate_strong"


def test_compile_and_audit_max_are_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    report_a = compile_max_atlas(first)
    report_b = compile_max_atlas(second)
    assert report_a == report_b
    assert report_a["research_target_count"] == 864
    assert report_a["research_cell_count"] == 6_912
    assert report_a["hyperedge_count"] == 8_568
    assert report_a["portfolio_coverage"]["fronts"] == 24
    assert report_a["scoring_basis"] == "transparent_profile_v1"
    assert report_a["records_claiming_solution"] == 0
    assert report_a["targets_claiming_proof_or_solution"] == 0
    assert report_a["cells_claiming_proof_or_solution"] == 0
    assert report_a["permanent_total_cap"] is None
    assert audit_max_output(first)["valid"] is True
    strict = audit_max_output_strict(first)
    assert strict["valid"] is True
    assert strict["counts"] == {
        "problems": 72,
        "targets": 864,
        "cells": 6_912,
        "methods": 32,
        "hyperedges": 8_568,
    }
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    assert (first / "research_cells.jsonl").read_bytes() == (second / "research_cells.jsonl").read_bytes()


def test_audit_detects_artifact_tampering(tmp_path: Path) -> None:
    output = tmp_path / "atlas"
    compile_max_atlas(output)
    problem_file = output / "problems.jsonl"
    rows = problem_file.read_text(encoding="utf-8").splitlines()
    payload = json.loads(rows[0])
    payload["title"] = payload["title"] + " tampered"
    rows[0] = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    problem_file.write_text("\n".join(rows) + "\n", encoding="utf-8")
    audit = audit_max_output_strict(output)
    assert audit["valid"] is False
    assert any("problems.jsonl: sha256 mismatch" in error for error in audit["errors"])


def test_strict_audit_detects_report_tampering(tmp_path: Path) -> None:
    output = tmp_path / "atlas"
    compile_max_atlas(output)
    report_path = output / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["research_cell_count"] += 1
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit = audit_max_output_strict(output)
    assert audit["valid"] is False
    assert "report digest mismatch" in audit["errors"]
    assert any(error.startswith("research_cell_count:") for error in audit["errors"])
