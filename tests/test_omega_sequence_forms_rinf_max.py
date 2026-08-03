"""OAKBench for Ω-SUITE-FORM-T∞ R∞ MAX layers."""
from __future__ import annotations

from fractions import Fraction
from itertools import islice
import json
from pathlib import Path

import pytest

from omega_sequence_forms_t.rinf.benchmark_matrix import (
    BenchmarkCoordinate,
    BenchmarkOutcome,
    FAMILY_IDS,
    MUTATION_IDS,
    VALIDATION_IDS,
    benchmark_atlas_receipt,
    coordinate_stream,
    plan_coordinate,
    plan_stream,
    select_campaign,
    shell_parameters,
)
from omega_sequence_forms_t.rinf.distributed import (
    BackendManifest if False else WorkLedger,
)
from omega_sequence_forms_t.rinf.distributed import (
    ShardSpec,
    WorkResult,
    WorkStatus,
    WorkerManifest,
    assign_work,
    deterministic_estimate,
    iter_shard_work,
    merge_ledgers,
    partition_ranks,
    shard_manifest,
    strided_shards,
)
from omega_sequence_forms_t.rinf.max_report import (
    EvidenceReference,
    MaxReport,
    ReportSection,
    build_rinf_max_report,
    evidence_from_payload,
)
from omega_sequence_forms_t.rinf.native_codegen import (
    NativeKernelSpec,
    cross_language_fixture,
    generate_cpp_project,
    generate_rust_project,
    project_bundle,
)
from omega_sequence_forms_t.rinf.theorem_miner import (
    MiningLimits,
    RelationKind,
    SequenceRecord,
    cauchy_prefix,
    exponent_vectors,
    first_counterexample,
    mine_cauchy_convolution,
    mine_linear_combination,
    mine_pointwise_product,
    mine_polynomial_relation,
    mine_relations,
    mine_shift_identity,
)


def _record(identifier: str, values) -> SequenceRecord:
    return SequenceRecord.create(identifier, values, provenance="unit-test")


def test_sequence_record_digest_is_deterministic() -> None:
    first = _record("squares", [n * n for n in range(20)])
    second = _record("squares", [n * n for n in range(20)])
    assert first.digest == second.digest
    assert len(first.digest) == 64


def test_linear_combination_discovery_with_holdout() -> None:
    a = _record("a", [n for n in range(40)])
    b = _record("b", [n * n for n in range(40)])
    target = _record("target", [3 * n - 2 * n * n for n in range(40)])
    relation = mine_linear_combination((a, b), target, holdout=10)
    assert relation is not None
    assert relation.kind == RelationKind.LINEAR_COMBINATION
    assert relation.evidence.exact_on_tested
    assert relation.evidence.predicts_holdout
    assert relation.parameters["coefficients"] == ["3", "-2"]
    assert relation.global_identity_proved is False


def test_affine_combination_discovers_intercept() -> None:
    a = _record("a", [n for n in range(32)])
    target = _record("target", [5 * n + 7 for n in range(32)])
    relation = mine_linear_combination((a,), target, affine=True, holdout=8)
    assert relation is not None
    assert relation.kind == RelationKind.AFFINE_COMBINATION
    assert relation.parameters["coefficients"] == ["5"]
    assert relation.parameters["intercept"] == "7"
    assert relation.evidence.predicts_holdout


def test_wrong_linear_combination_is_rejected() -> None:
    a = _record("a", [n for n in range(30)])
    b = _record("b", [n * n for n in range(30)])
    target = _record("target", [n**3 + (1 if n == 29 else 0) for n in range(30)])
    assert mine_linear_combination((a, b), target, holdout=6) is None


def test_shift_identity_with_scale() -> None:
    source = _record("source", [2**n for n in range(40)])
    target = _record("target", [3 * 2 ** (n + 2) for n in range(40)])
    relations = mine_shift_identity(source, target, maximum_shift=4, holdout=8)
    assert relations
    assert any(relation.evidence.predicts_holdout for relation in relations)
    assert all(relation.kind == RelationKind.SHIFT_IDENTITY for relation in relations)


def test_pointwise_product_identity() -> None:
    a = _record("a", [n + 1 for n in range(40)])
    b = _record("b", [2 * n - 1 for n in range(40)])
    target = _record("target", [(n + 1) * (2 * n - 1) for n in range(40)])
    relation = mine_pointwise_product(a, b, target, holdout=8)
    assert relation is not None
    assert relation.evidence.predicts_holdout


def test_cauchy_convolution_identity() -> None:
    left_values = tuple(Fraction(1) for _ in range(30))
    right_values = tuple(Fraction(1) for _ in range(30))
    target_values = cauchy_prefix(left_values, right_values, 40)
    left = _record("left", left_values)
    right = _record("right", right_values)
    target = _record("target", target_values)
    relation = mine_cauchy_convolution(left, right, target, holdout=8)
    assert relation is not None
    assert relation.kind == RelationKind.CAUCHY_CONVOLUTION
    assert relation.evidence.predicts_holdout


def test_polynomial_relation_xy_minus_z() -> None:
    x = _record("x", [n + 1 for n in range(50)])
    y = _record("y", [n + 2 for n in range(50)])
    z = _record("z", [(n + 1) * (n + 2) for n in range(50)])
    relations = mine_polynomial_relation((x, y, z), maximum_degree=2, maximum_monomials=20, holdout=10)
    assert relations
    assert any(relation.evidence.predicts_holdout for relation in relations)
    assert all(relation.kind == RelationKind.POLYNOMIAL_RELATION for relation in relations)


def test_monomial_basis_is_degree_bounded() -> None:
    vectors = exponent_vectors(3, 4, 1000)
    assert vectors
    assert all(sum(vector) <= 4 for vector in vectors)
    assert vectors[0] == (0, 0, 0)


def test_counterexample_search_returns_first_failure() -> None:
    relation = mine_linear_combination(
        (_record("a", range(20)),),
        _record("b", [2 * n for n in range(20)]),
        holdout=4,
    )
    assert relation is not None
    counterexample = first_counterexample(
        relation,
        lambda n: (Fraction(2 * n), Fraction(2 * n + (1 if n == 99 else 0))),
        range(20, 120),
    )
    assert counterexample is not None
    assert counterexample["index"] == 99


def test_full_relation_miner_is_deterministic() -> None:
    records = (
        _record("n", range(40)),
        _record("square", [n * n for n in range(40)]),
        _record("combo", [2 * n + n * n for n in range(40)]),
    )
    limits = MiningLimits(maximum_sources=4, maximum_shift=3, maximum_polynomial_degree=2, maximum_monomials=20, maximum_relations=64, holdout=8)
    first = mine_relations(records, limits=limits).to_dict()
    second = mine_relations(records, limits=limits).to_dict()
    assert first == second
    assert first["relation_count"] > 0
    assert first["global_identity_proved"] is False


def test_contiguous_partition_covers_requested_ranks() -> None:
    shards = partition_ranks(10_003, 17, seed=42)
    assert len(shards) == 17
    assert sum(shard.planned_cells for shard in shards) == 10_003
    assert shards[0].start_rank == 0
    assert shards[-1].stop_rank == 10_003
    manifest = shard_manifest(shards, campaign_id="fixture")
    assert manifest["planned_cells"] == 10_003
    assert len(manifest["manifest_digest"]) == 64


def test_strided_shards_are_disjoint_and_complete() -> None:
    shards = strided_shards(1000, 13, seed=7)
    ranks = []
    for shard in shards:
        ranks.extend(range(shard.start_rank, shard.stop_rank, shard.stride))
    assert sorted(ranks) == list(range(1000))
    assert len(ranks) == len(set(ranks))


def test_shard_work_is_deterministic_and_unique() -> None:
    shard = partition_ranks(512, 4, seed=11)[2]
    first = tuple(iter_shard_work(shard, campaign_id="campaign"))
    second = tuple(iter_shard_work(shard, campaign_id="campaign"))
    assert first == second
    assert len({unit.work_id for unit in first}) == len(first)
    assert len({unit.address for unit in first}) == len(first)
    assert len({unit.flat_index for unit in first}) == len(first)


def test_worker_assignment_respects_capabilities() -> None:
    units = tuple(islice(iter_shard_work(partition_ranks(200, 1, seed=3)[0], campaign_id="assign"), 100))
    workers = (
        WorkerManifest("even", "a" * 64, "b" * 64, tuple(range(0, 256, 2)), (), 4, 2048, True),
        WorkerManifest("odd", "c" * 64, "d" * 64, tuple(range(1, 256, 2)), (), 4, 2048, True),
    )
    assignments = assign_work(units, workers)
    assert sum(len(items) for items in assignments.values()) == len(units)
    assert all(unit.address.family % 2 == 0 for unit in assignments["even"])
    assert all(unit.address.family % 2 == 1 for unit in assignments["odd"])


def _complete_result(unit, worker="worker") -> WorkResult:
    return WorkResult(
        work_id=unit.work_id,
        worker_id=worker,
        status=WorkStatus.COMPLETED,
        input_digest="1" * 64,
        output_digest="2" * 64,
        evidence_ids=(f"evidence.{unit.sequence_number}",),
        candidate_ids=(),
        counterexample_ids=(),
        failure_codes=(),
        compute_spent=unit.estimated_compute,
        storage_bytes=unit.estimated_storage_bytes,
    )


def test_work_ledger_and_merge() -> None:
    units = tuple(islice(iter_shard_work(partition_ranks(20, 1, seed=1)[0], campaign_id="merge"), 20))
    left = WorkLedger("merge")
    right = WorkLedger("merge")
    for unit in units[:10]:
        left.add_work(unit)
        left.add_result(_complete_result(unit, "left"))
    for unit in units[10:]:
        right.add_work(unit)
        right.add_result(_complete_result(unit, "right"))
    merged = merge_ledgers("merge", (left, right))
    receipt = merged.receipt()
    assert receipt["planned_work"] == 20
    assert receipt["completed_work"] == 20
    assert receipt["validation_errors"] == []
    assert receipt["permanent_total_cap"] is None


def test_ledger_detects_nondeterministic_retries() -> None:
    unit = next(iter_shard_work(partition_ranks(1, 1)[0], campaign_id="nondeterministic"))
    ledger = WorkLedger("nondeterministic")
    ledger.add_work(unit)
    ledger.add_result(_complete_result(unit))
    ledger.add_result(
        WorkResult(
            work_id=unit.work_id,
            worker_id="worker",
            status=WorkStatus.COMPLETED,
            input_digest="1" * 64,
            output_digest="3" * 64,
            evidence_ids=(),
            candidate_ids=(),
            counterexample_ids=(),
            failure_codes=(),
            compute_spent=1,
            storage_bytes=1,
            attempt=2,
        )
    )
    assert any("nondeterministic" in error for error in ledger.validate())


def test_native_kernel_spec_and_rust_generation(tmp_path: Path) -> None:
    spec = NativeKernelSpec.create("fibonacci", [1, 1], [0, 1], signed_bits=128)
    project = generate_rust_project(spec)
    assert project.language == "rust"
    assert "pub const ORDER: usize = 2" in project.files["src/lib.rs"]
    assert project.manifest()["compilation_verified"] is False
    receipt = project.write(tmp_path / "rust")
    assert len(receipt["manifest_digest"]) == 64
    assert (tmp_path / "rust" / "Cargo.toml").exists()


def test_cpp_generation_contains_checked_kernel(tmp_path: Path) -> None:
    spec = NativeKernelSpec.create("lucas", [1, 1], [2, 1], signed_bits=64, checked_arithmetic=True)
    project = generate_cpp_project(spec)
    assert project.language == "cpp"
    assert "std::optional" in project.files["include/omega_kernel.hpp"]
    project.write(tmp_path / "cpp")
    assert (tmp_path / "cpp" / "CMakeLists.txt").exists()


def test_fractional_native_kernel_is_rejected() -> None:
    spec = NativeKernelSpec.create("fractional", [Fraction(1, 2)], [1])
    with pytest.raises(ValueError):
        generate_rust_project(spec)
    with pytest.raises(ValueError):
        generate_cpp_project(spec)


def test_cross_language_fixture_and_bundle() -> None:
    spec = NativeKernelSpec.create("geometric", [2], [3])
    fixture = cross_language_fixture(spec, expected_terms=[3, 6, 12, 24, 48])
    assert fixture["required_backends"] == ["python", "rust", "cpp"]
    assert fixture["backend_validation_completed"] is False
    assert fixture["global_identity_proved"] is False
    bundle = project_bundle(spec)
    assert set(bundle) == {"rust", "cpp"}


def test_benchmark_coordinate_and_shell_growth() -> None:
    coordinate = BenchmarkCoordinate(0, 0, 0, 0, 42)
    assert coordinate.family_id == FAMILY_IDS[0]
    assert coordinate.mutation_id == MUTATION_IDS[0]
    assert coordinate.validation_id == VALIDATION_IDS[0]
    assert len(coordinate.digest()) == 64
    first = shell_parameters(0)
    later = shell_parameters(64)
    assert later["term_count"] > first["term_count"]
    assert later["precision_bits"] > first["precision_bits"]


def test_benchmark_stream_is_unbounded_and_deterministic() -> None:
    first = tuple(islice(coordinate_stream(seed=17), 20_000))
    second = tuple(islice(coordinate_stream(seed=17), 20_000))
    assert first == second
    assert len({item.digest() for item in first}) == 20_000


def test_benchmark_plan_has_remote_indices_and_metrics() -> None:
    plan = plan_coordinate(BenchmarkCoordinate(5, 7, 9, 12, 3))
    assert plan.term_count > 0
    assert plan.holdout_count > 0
    assert max(plan.remote_indices) >= plan.term_count
    assert plan.value_cost_ratio > 0
    assert "false_discovery_rate" in plan.success_metrics


def test_campaign_selection_respects_finite_resources_without_permanent_cap() -> None:
    campaign = select_campaign(
        campaign_id="matrix",
        seed=2,
        compute_budget=500,
        storage_budget_bytes=10_000_000,
        maximum_materialized_cases=128,
        scouting_window=5000,
    )
    assert 0 < len(campaign.plans) <= 128
    assert sum(plan.expected_compute_units for plan in campaign.plans) <= 500 + 1e-9
    assert sum(plan.expected_storage_bytes for plan in campaign.plans) <= 10_000_000
    receipt = campaign.receipt()
    assert receipt["permanent_total_cap"] is None
    assert receipt["global_identity_proved"] is False


def test_benchmark_outcome_accounting() -> None:
    campaign = select_campaign(
        campaign_id="outcomes",
        seed=4,
        compute_budget=100,
        storage_budget_bytes=1_000_000,
        maximum_materialized_cases=4,
        scouting_window=100,
    )
    plan = campaign.plans[0]
    outcome = BenchmarkOutcome(
        coordinate_digest=plan.coordinate.digest(),
        passed=True,
        metrics={"heldout_accuracy": 1.0},
        failure_codes=(),
        candidate_ids=("candidate.1",),
        counterexample_ids=(),
        compute_spent=plan.expected_compute_units,
        storage_bytes=plan.expected_storage_bytes,
    )
    campaign.add_outcome(outcome)
    receipt = campaign.receipt()
    assert receipt["executed_cases"] == 1
    assert receipt["passed_cases"] == 1


def test_benchmark_atlas_has_no_shell_cap() -> None:
    receipt = benchmark_atlas_receipt()
    assert receipt["base_cells_per_shell"] == len(FAMILY_IDS) * len(MUTATION_IDS)
    assert receipt["shell_count"] is None
    assert receipt["permanent_total_cap"] is None
    assert len(receipt["atlas_digest"]) == 64


def test_report_rejects_automatic_proof_flags() -> None:
    with pytest.raises(ValueError):
        MaxReport("bad", "Bad", "1", "scope", global_identity_proved=True)
    with pytest.raises(ValueError):
        MaxReport("bad", "Bad", "1", "scope", formal_proof_completed=True)


def test_report_evidence_and_markdown(tmp_path: Path) -> None:
    report = MaxReport("fixture", "Fixture report", "1", "unit test")
    evidence = evidence_from_payload(
        evidence_id="evidence.fixture",
        kind="test",
        payload={"passed": True},
        provenance="pytest",
        statement="Fixture passed.",
    )
    report.add_evidence(evidence)
    report.add_section(
        ReportSection(
            section_id="fixture",
            title="Fixture",
            status="validated_fixture",
            summary="A deterministic fixture was executed.",
            facts=("The payload is reproducible.",),
            limitations=("This is not a mathematical proof.",),
            evidence_ids=(evidence.evidence_id,),
            metrics={"passed": True, "cases": 1},
            tables=(("Cases", ({"name": "fixture", "passed": True},)),),
        )
    )
    payload = report.to_dict()
    assert payload["validation_errors"] == []
    assert payload["global_identity_proved"] is False
    markdown = report.markdown()
    assert "# Fixture report" in markdown
    assert "Epistemic boundary" in markdown
    receipt = report.write(tmp_path)
    assert len(receipt["report_digest"]) == 64
    assert (tmp_path / "REPORT.md").exists()


def test_max_report_compiler() -> None:
    catalog = {
        "counts": {"families": 256, "transformations": 512, "antipatterns": 1024},
        "catalog_digest": "a" * 64,
    }
    benchmark = {"passed": True, "global_identity_proved": False, "benchmark_digest": "b" * 64}
    campaign = {"executed_cells": 128, "stop_reason": "campaign_cell_cap", "permanent_total_cap": None}
    theorem = {"relation_count": 7, "global_identity_proved": False}
    report = build_rinf_max_report(
        catalog_receipt=catalog,
        benchmark_receipt=benchmark,
        campaign_receipt=campaign,
        theorem_report=theorem,
    )
    payload = report.to_dict()
    assert len(payload["sections"]) == 4
    assert payload["validation_errors"] == []
    assert payload["global_identity_proved"] is False
    assert payload["formal_proof_completed"] is False
