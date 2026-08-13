from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from omega_capability_os_t.github_memory import CapabilityRequest
from omega_capability_os_t.github_pr_generation_forest import (
    DEFAULT_SEED_COUNT,
    FractalPRGenerationCompiler,
    compile_pr_generation_campaign,
    compile_pr_generation_forest,
    logical_cardinality,
)


def _request() -> CapabilityRequest:
    return CapabilityRequest(
        request_id="req-pr-5k2n",
        description="Improve a new PR using reuse-first bounded fractal generation",
        domains=("github", "code-generation", "oak"),
        consumes=("pr-genome", "historical-memory"),
        produces=("implementation", "tests", "evidence"),
    )


def _genome() -> dict:
    return {
        "ref": "pr:Tristan-TM-Poly/example#451",
        "repository": "Tristan-TM-Poly/example",
        "number": 451,
        "lifecycle": "DRAFT",
        "changed_files": ["omega/example.py", "tests/test_example.py"],
        "named_concepts": ["Ω-PR-5K2N-T∞", "OAK"],
        "intent_tokens": ["generation", "reuse", "pr"],
    }


def test_exact_5k_times_two_to_n_law():
    assert logical_cardinality(DEFAULT_SEED_COUNT, 0) == 5_000
    assert logical_cardinality(DEFAULT_SEED_COUNT, 1) == 10_000
    assert logical_cardinality(DEFAULT_SEED_COUNT, 10) == 5_120_000
    assert logical_cardinality(DEFAULT_SEED_COUNT, 20) == 5_242_880_000


def test_binary_route_is_explorer_prosecutor_pair():
    compiler = FractalPRGenerationCompiler(materialization_budget=4)
    left = compiler.address(0, generation=1)
    right = compiler.address(1, generation=1)
    assert left.seed_id == right.seed_id == 0
    assert left.polarity == "explorer"
    assert right.polarity == "prosecutor"


def test_all_seed_families_exist_in_the_5000_seed_genome():
    compiler = FractalPRGenerationCompiler(materialization_budget=4)
    families = {compiler.address(i, generation=0).family for i in range(DEFAULT_SEED_COUNT)}
    assert families == {
        "reuse", "code", "test", "benchmark", "contract", "documentation",
        "provenance", "oak", "simplify", "alternative",
    }


def test_compile_is_deterministic_bounded_and_virtual():
    left = compile_pr_generation_forest(
        _request(), _genome(), generation=12,
        residual_outputs=("implementation", "tests"),
        reuse_coverage_ratio=0.5,
        materialization_budget=24,
    )
    right = compile_pr_generation_forest(
        _request(), _genome(), generation=12,
        residual_outputs=("implementation", "tests"),
        reuse_coverage_ratio=0.5,
        materialization_budget=24,
    )
    assert left == right
    assert left["logical_cardinality_decimal"] == str(5_000 * (2**12))
    assert left["logical_population_materialized"] is False
    assert left["sampled_candidate_count"] <= 24 * 8
    assert left["compiled_addition_count"] <= 24
    assert len(left["fingerprint"]) == 64


def test_large_generation_has_no_architectural_hard_cap_but_finite_run():
    report = compile_pr_generation_forest(
        _request(), _genome(), generation=128, materialization_budget=8,
    )
    assert report["logical_cardinality_decimal"] == str(5_000 * (2**128))
    assert report["adaptive_continuation"]["architecture_hard_cap"] is False
    assert report["physical_patch_compiler"]["materialization_budget"] == 8
    assert report["physical_patch_compiler"]["automatic_commit_allowed"] is False
    assert report["physical_patch_compiler"]["automatic_merge_allowed"] is False
    assert report["physical_patch_compiler"]["write_authority_granted"] is False
    assert all(row["materialization_status"] == "SPEC_ONLY" for row in report["compiled_additions"])


def test_cvcd_compresses_only_bounded_sample_and_says_so():
    report = compile_pr_generation_forest(
        _request(), _genome(), generation=5, materialization_budget=16,
    )
    assert report["cvcd_sample_patterns"]
    assert report["cvcd_sample_compression_ratio"] >= 1.0
    assert all(
        "bounded deterministic sample" in row["boundary"]
        for row in report["cvcd_sample_patterns"]
    )


def test_high_go_threshold_stops_without_fake_nmax():
    report = compile_pr_generation_forest(
        _request(), _genome(), generation=7,
        materialization_budget=8, min_go_gradient=99.0,
    )
    assert report["compiled_addition_count"] == 0
    assert report["adaptive_continuation"]["continue"] is False
    assert report["adaptive_continuation"]["next_generation_candidate"] is None
    assert report["adaptive_continuation"]["architecture_hard_cap"] is False


def test_oak_boundaries_reject_volume_as_progress():
    report = compile_pr_generation_forest(
        _request(), _genome(), generation=3, materialization_budget=8,
    )
    assert "many additions != progress" in report["oak_boundaries"]
    assert "compiled addition spec != tested patch" in report["oak_boundaries"]
    assert report["physical_patch_compiler"]["human_review_required"] is True


def test_campaign_covers_n_to_runtime_budget_without_turning_budget_into_nmax():
    campaign = compile_pr_generation_campaign(
        _request(), _genome(), start_generation=0,
        generation_budget=4, materialization_budget=6,
    )
    assert campaign["architecture_hard_cap"] is False
    assert campaign["generation_budget_is_runtime_budget"] is True
    assert 1 <= campaign["generation_count"] <= 4
    assert [row["generation"] for row in campaign["generations"]] == list(range(campaign["generation_count"]))
    assert campaign["generations"][0]["logical_cardinality_decimal"] == "5000"
    assert len(campaign["fingerprint"]) == 64


def test_direct_event_script_resolves_repository_package(tmp_path):
    """M− regression: direct tools/ execution must not lose the repository package root."""
    repo_root = Path(__file__).resolve().parents[1]
    event_path = tmp_path / "event.json"
    output_path = tmp_path / "receipt.json"
    event_path.write_text(
        json.dumps(
            {
                "number": 452,
                "repository": {"full_name": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2"},
                "pull_request": {
                    "number": 452,
                    "title": "5K2N direct-script regression",
                    "body": "Ω-PR-5K2N-T∞",
                    "state": "open",
                    "draft": True,
                    "head": {"sha": "candidate-head"},
                },
            }
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "compile_pr_5k2n_event.py"),
            "--event", str(event_path),
            "--output", str(output_path),
            "--generation", "0",
            "--budget", "4",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["event_context"]["physical_materialization_blocked_until_reuse_inspection"] is True
    assert report["physical_patch_compiler"]["write_authority_granted"] is False
