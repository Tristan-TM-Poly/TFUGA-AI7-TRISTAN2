from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_open_problems_atlas.cli import _load_clay
from omega_open_problems_atlas.generator import (
    DOMAINS,
    RESEARCH_OPERATORS,
    generate_seed_cells,
    seed_manifest,
)
from omega_open_problems_atlas.models import (
    EpistemicStatus,
    OpenStatus,
    ProblemGenome,
    ProblemKind,
)
from omega_open_problems_atlas.oak import OAKDecision, evaluate_problem
from omega_open_problems_atlas.registry import DuplicateProblemError, ProblemRegistry


def test_seed_1024_is_deterministic_and_not_false_problem_count() -> None:
    cells = generate_seed_cells()
    assert len(DOMAINS) == 32
    assert len(RESEARCH_OPERATORS) == 32
    assert len(cells) == 1024
    assert len({cell.cell_id for cell in cells}) == 1024
    assert all(not cell.is_verified_open_problem for cell in cells)
    assert all(not cell.solution_claimed for cell in cells)
    first = seed_manifest(cells)
    second = seed_manifest(cells)
    assert first == second
    assert first["research_cell_count"] == 1024
    assert first["verified_open_problem_count"] == 0
    assert first["permanent_total_cap"] is None


def test_clay_seed_has_six_source_reported_open_and_poincare_resolved() -> None:
    registry = _load_clay(Path("data/open_problems_atlas/clay_seed.json"))
    summary = registry.summary()
    assert summary["problem_count"] == 7
    assert summary["open_status_counts"]["SOURCE_REPORTED_OPEN"] == 6
    assert summary["open_status_counts"]["RESOLVED"] == 1
    assert summary["solution_claimed_count"] == 0
    assert summary["all_finite_computation_boundaries_present"] is True
    assert registry.get("CLAY-POINCARE").metadata["role"] == "resolved_benchmark"


def test_source_reported_open_remains_discovery_only() -> None:
    registry = _load_clay(Path("data/open_problems_atlas/clay_seed.json"))
    report = evaluate_problem(registry.get("CLAY-RH"))
    assert report.decision is OAKDecision.DISCOVERY_ONLY
    assert "independent_status_check_required" in report.findings


def test_independently_checked_record_can_be_research_ready() -> None:
    problem = ProblemGenome(
        problem_id="TEST-OPEN-1",
        title="Synthetic sourced research problem",
        statement="For every object in class C, determine whether property P holds.",
        source_id="TEST",
        source_locator="urn:test:1",
        kind=ProblemKind.RESEARCH_PROBLEM,
        domains=("logic",),
        open_status=OpenStatus.INDEPENDENTLY_CHECKED_OPEN,
        epistemic_status=EpistemicStatus.LITERATURE_BASELINED,
        last_status_check="2026-08-03",
    )
    assert evaluate_problem(problem).decision is OAKDecision.RESEARCH_READY


def test_oak_blocks_removed_finite_computation_boundary() -> None:
    problem = ProblemGenome(
        problem_id="BAD-1",
        title="Unsafe record",
        statement="A statement.",
        source_id="TEST",
        source_locator="urn:test:bad",
        kind=ProblemKind.CONJECTURE,
        domains=("analysis",),
        finite_computation_is_not_proof=False,
    )
    report = evaluate_problem(problem)
    assert report.decision is OAKDecision.BLOCK
    assert "finite_computation_boundary_removed" in report.findings


def test_registry_rejects_duplicate_statement() -> None:
    one = ProblemGenome(
        problem_id="DUP-1",
        title="One",
        statement="The same normalized statement.",
        source_id="TEST",
        source_locator="urn:test:dup1",
        kind=ProblemKind.CONJECTURE,
        domains=("algebra",),
    )
    two = ProblemGenome(
        problem_id="DUP-2",
        title="Two",
        statement="  The same   normalized statement. ",
        source_id="TEST",
        source_locator="urn:test:dup2",
        kind=ProblemKind.CONJECTURE,
        domains=("algebra",),
    )
    registry = ProblemRegistry([one])
    with pytest.raises(DuplicateProblemError):
        registry.add(two)


def test_clay_json_contract_fields_are_present() -> None:
    payload = json.loads(Path("data/open_problems_atlas/clay_seed.json").read_text())
    required = {
        "problem_id",
        "title",
        "statement",
        "source_locator",
        "kind",
        "domains",
        "open_status",
        "epistemic_status",
        "human_review_required",
        "finite_computation_is_not_proof",
        "solution_claimed",
    }
    for record in payload["records"]:
        assert required <= set(record)
        assert record["human_review_required"] is True
        assert record["finite_computation_is_not_proof"] is True
        assert record["solution_claimed"] is False
