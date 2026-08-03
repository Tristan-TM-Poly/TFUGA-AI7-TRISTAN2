from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r03 import (
    ATTACK_MODES,
    FRONTS,
    audit_output,
    build_seed_records,
    compile_atlas,
    expand_research_cells,
    load_source_registry,
    select_portfolio,
)


def test_seed_constellation_covers_24_fronts_and_72_families() -> None:
    records = build_seed_records()
    assert len(FRONTS) == 24
    assert len(records) == 72
    assert {record.front for record in records} == set(FRONTS)
    assert all(record.solution_claimed is False for record in records)
    assert all(record.current_open_status_claimed is False for record in records)
    assert all(not record.validate() for record in records)


def test_eight_attack_modes_materialize_576_cells() -> None:
    records = build_seed_records()
    cells = expand_research_cells(records)
    assert len(ATTACK_MODES) == 8
    assert len(cells) == 576
    assert len({cell.cell_id for cell in cells}) == len(cells)
    assert all(cell.proof_claimed is False for cell in cells)
    assert all(not cell.validate() for cell in cells)


def test_source_registry_requires_refresh_and_verification() -> None:
    sources = load_source_registry()
    assert len(sources) >= 16
    assert {source.source_id for source in sources} >= {
        "clay",
        "erdos_problems",
        "aim_problem_lists",
        "formal_conjectures",
        "open_quantum_problems",
        "imo",
        "putnam",
        "comap_mcm_icm",
        "kaggle",
        "arc_prize",
        "aimo_prize",
    }
    assert all(not source.validate() for source in sources)


def test_compile_is_deterministic_and_oak_safe(tmp_path: Path) -> None:
    first = compile_atlas(tmp_path / "first")
    second = compile_atlas(tmp_path / "second")
    assert first == second
    assert first["seed_problem_count"] == 72
    assert first["front_count"] == 24
    assert first["attack_mode_count"] == 8
    assert first["materialized_research_cell_count"] == 576
    assert first["materialized_hyperedge_count"] == 576
    assert first["permanent_total_cap"] is None
    assert first["solution_claimed"] is False
    assert first["formal_proof_claimed"] is False
    assert first["scientific_validation_claimed"] is False
    assert first["current_status_certification_claimed"] is False
    assert first["records_claiming_solution"] == 0
    assert first["research_cells_claiming_proof"] == 0
    assert audit_output(tmp_path / "first")["valid"] is True


def test_import_requires_timestamp_before_open_status_claim(tmp_path: Path) -> None:
    bad = tmp_path / "bad.jsonl"
    bad.write_text(
        json.dumps(
            {
                "problem_id": "unsafe_status",
                "title": "Unsafe current status assertion",
                "front": FRONTS[0],
                "status": "open",
                "source_id": "external_import",
                "current_open_status_claimed": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="source_verified_at"):
        compile_atlas(tmp_path / "unsafe", import_paths=[bad])


def test_portfolio_budgets_are_adjustable_not_permanent_caps() -> None:
    cells = expand_research_cells(build_seed_records())
    portfolio = select_portfolio(
        cells,
        primary_budget=12,
        secondary_budget=36,
        experiment_budget=128,
    )
    assert len(portfolio["primary"]) == 12
    assert len(portfolio["secondary"]) == 36
    assert len(portfolio["experiments"]) == 128
    assert portfolio["finite_budget_is_not_permanent_cap"] is True
    assert portfolio["permanent_total_cap"] is None
