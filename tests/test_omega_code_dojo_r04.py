from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import jsonschema

from omega_code_dojo_t.r04.analyzer import ResolutionAnalyzer
from omega_code_dojo_t.r04.benchmark import run_r04_benchmark
from omega_code_dojo_t.r04.cli import main
from omega_code_dojo_t.r04.engine import ResolutionEngine
from omega_code_dojo_t.r04.families import FAMILIES, FAMILY_BY_ID, solve
from omega_code_dojo_t.r04.models import ResolutionPolicy
from omega_code_dojo_t.r04.portfolio import DEFAULT_PORTFOLIO


def test_family_catalog_has_seventeen_original_families() -> None:
    assert len(FAMILIES) == 17
    assert len(FAMILY_BY_ID) == 17
    assert all(len(family.strategies) == 2 for family in FAMILIES)


def test_logical_problem_space_is_large_but_not_materialized() -> None:
    assert DEFAULT_PORTFOLIO.logical_problem_space == 2_336_462_209_024
    problems = list(DEFAULT_PORTFOLIO.materialize(ResolutionPolicy(problem_budget=17)))
    assert len(problems) == 17
    assert len({problem.family_id for problem in problems}) == 17


def test_problem_generation_is_deterministic() -> None:
    family = FAMILY_BY_ID["coin_change_min"]
    first = family.generate(123, 5)
    second = family.generate(123, 5)
    assert first == second
    assert first.expected_output == family.oracle(first.input_payload)


def test_exact_strategy_solves_each_family_fixture() -> None:
    for family in FAMILIES:
        problem = family.generate(99, 6)
        exact = family.strategies[-1]
        assert exact.exact is True
        assert solve(exact.strategy_id, problem.input_payload) == problem.expected_output


def test_full_portfolio_uses_fallbacks_and_solves_all() -> None:
    receipt = ResolutionEngine().run(ResolutionPolicy(problem_budget=512, max_attempts_per_problem=2))
    assert receipt.materialized_problems == 512
    assert receipt.solved_problems == 512
    assert receipt.unresolved_problems == 0
    assert receipt.solve_rate == 1.0
    assert sum(metric.fallback_solves for metric in receipt.family_metrics) > 0
    assert receipt.verify_hash()


def test_restricted_portfolio_exposes_unresolved_problems() -> None:
    receipt = ResolutionEngine().run(ResolutionPolicy(problem_budget=512, max_attempts_per_problem=1))
    assert receipt.unresolved_problems > 0
    assert receipt.solve_rate < 1.0
    assert receipt.claims["general_algorithm_correctness_claimed"] is False


def test_resolution_receipt_hash_detects_tampering() -> None:
    receipt = ResolutionEngine().run(ResolutionPolicy(problem_budget=32, max_attempts_per_problem=2))
    assert receipt.verify_hash()
    tampered = replace(receipt, solved_problems=receipt.solved_problems - 1)
    assert tampered.verify_hash() is False


def test_analysis_prioritizes_failures_and_has_falsifiers() -> None:
    receipt = ResolutionEngine().run(ResolutionPolicy(problem_budget=256, max_attempts_per_problem=2))
    report = ResolutionAnalyzer().analyze(receipt)
    assert report["fallback_solutions"] > 0
    assert report["unique_counterexamples"] > 0
    assert report["claims"]["maximum_problem_resolution_claimed"] is False
    assert all(item["falsifier"] for item in report["insights"])


def test_benchmark_is_deterministic_and_certified() -> None:
    first = run_r04_benchmark(512)
    second = run_r04_benchmark(512)
    assert first == second
    assert first["status"] == "CERTIFIED_SYNTHETIC_PROBLEM_RESOLUTION_FIXTURES_R0_4"
    assert first["solved_problems"] == 512
    assert first["restricted_unresolved"] > 0


def test_schemas_are_valid_and_accept_benchmark_summary() -> None:
    root = Path(__file__).resolve().parents[1]
    receipt_schema = json.loads((root / "schemas/omega_code_dojo_resolution_receipt_v4.schema.json").read_text())
    analysis_schema = json.loads((root / "schemas/omega_code_dojo_resolution_analysis_v4.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(receipt_schema)
    jsonschema.Draft202012Validator.check_schema(analysis_schema)
    receipt = ResolutionEngine().run(ResolutionPolicy(problem_budget=64, max_attempts_per_problem=2))
    analysis = ResolutionAnalyzer().analyze(receipt)
    jsonschema.validate(receipt.to_dict(include_records=False), receipt_schema)
    jsonschema.validate(analysis, analysis_schema)


def test_cli_catalog_resolve_and_benchmark(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.json"
    resolved = tmp_path / "resolved.json"
    benchmark = tmp_path / "benchmark.json"
    assert main(["catalog", "--output", str(catalog)]) == 0
    assert main(["resolve", "--problems", "64", "--summary-only", "--output", str(resolved)]) == 0
    assert main(["benchmark", "--problems", "128", "--output", str(benchmark)]) == 0
    assert json.loads(catalog.read_text())["families"]
    assert json.loads(resolved.read_text())["solve_rate"] == 1.0
    assert json.loads(benchmark.read_text())["status"].endswith("R0_4")


def test_no_external_platform_content_is_required() -> None:
    receipt = ResolutionEngine().run(ResolutionPolicy(problem_budget=32))
    assert all(record.problem.source_kind == "omega_original_synthetic" for record in receipt.records)
    assert receipt.claims["codewars_affiliation_claimed"] is False
    assert receipt.claims["open_problem_solution_claimed"] is False
