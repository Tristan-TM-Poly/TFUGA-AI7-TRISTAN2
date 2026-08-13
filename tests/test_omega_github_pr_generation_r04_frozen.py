from __future__ import annotations

from omega_capability_os_t.github_pr_generation_r04_frozen import compile_frozen_r04_hold


SOURCE_TARGET_SHA = "a" * 40


def _seed() -> dict:
    return {
        "schema": "omega-pr-5k2n-r04-frozen-static-seed/v0.1.0",
        "source_target_head_sha": SOURCE_TARGET_SHA,
        "source_r04_fingerprint": "f" * 64,
        "source_workflow_run_id": 123,
        "source_artifact_id": 456,
        "source_artifact_sha256": "e" * 64,
        "artifact_decision": "INSPECT",
        "residual_outputs": ["implementation", "tests"],
        "receipts": [
            {
                "ref": "pr:o/r#331",
                "planned_head_sha": "c" * 40,
                "hydrated_head_sha": "c" * 40,
                "hydration_status": "HYDRATED_EXACT_HEAD",
                "head_match": True,
                "changed_files": ["omega/x.py", "tests/test_x.py"],
                "source_files": ["omega/x.py"],
                "test_files": ["tests/test_x.py"],
                "workflow_files": [],
                "python_symbol_assets": ["symbol:Compiler.run"],
                "target_exact_path_overlap": [],
                "intent_overlap_proxy": 0.25,
                "evidence_class": "STATIC_SOURCE_TEST_SURFACE",
            }
        ],
        "boundary": "frozen test seed",
    }


def _target(head: str) -> dict:
    return {
        "ref": "pr:o/r#452",
        "head_sha": head,
        "changed_files": ["omega/current.py"],
        "named_concepts": ["Ω-PR-5K2N-T∞"],
        "intent_tokens": ["generation"],
    }


def test_stale_target_context_forces_hold_even_for_testable_candidate():
    report = compile_frozen_r04_hold(_seed(), target_pr_genome=_target("b" * 40))
    assert report["frozen_fallback"] is True
    assert report["current_live_history_complete"] is False
    assert report["inspection_context_fresh"] is False
    assert report["experiment_eligible_candidate_count"] == 0
    assert report["experiment_contract_count"] == 0
    receipt = report["compatibility_receipts"][0]
    assert receipt["experiment_eligible"] is False
    assert receipt["experiment_block_reason"] == "stale_target_inspection_context"
    assert receipt["compatibility_verdict"] == "UNKNOWN"
    assert receipt["reuse_authorized"] is False


def test_even_same_target_head_frozen_seed_requires_live_revalidation():
    report = compile_frozen_r04_hold(_seed(), target_pr_genome=_target(SOURCE_TARGET_SHA))
    assert report["inspection_context_fresh"] is True
    assert report["experiment_contract_count"] == 0
    receipt = report["compatibility_receipts"][0]
    assert receipt["experiment_eligible"] is False
    assert receipt["experiment_block_reason"] == "frozen_static_seed_requires_live_revalidation"


def test_frozen_fallback_never_authorizes_execution_reuse_write_or_merge():
    report = compile_frozen_r04_hold(_seed(), target_pr_genome=_target("b" * 40))
    assert report["compatibility_proven_count"] == 0
    assert report["reuse_authorized_count"] == 0
    assert report["physicalization_gate"] == "INSPECT"
    assert report["write_authority_granted"] is False
    assert report["execution_authorized"] is False
    assert report["automatic_commit_allowed"] is False
    assert report["automatic_merge_allowed"] is False
    assert len(report["fingerprint"]) == 64


def test_frozen_seed_provenance_is_retained_in_current_hold_report():
    report = compile_frozen_r04_hold(_seed(), target_pr_genome=_target("b" * 40))
    assert report["source_r04_fingerprint"] == "f" * 64
    assert report["source_workflow_run_id"] == 123
    assert report["source_artifact_id"] == 456
    assert report["source_artifact_sha256"] == "e" * 64
    assert report["inspection_context_source_head_sha"] == SOURCE_TARGET_SHA
