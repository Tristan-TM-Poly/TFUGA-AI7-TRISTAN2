from __future__ import annotations

from omega_capability_os_t.github_pr_generation_r04_frozen import compile_frozen_r04_hold
from omega_capability_os_t.github_pr_generation_r05 import compile_compatibility_outcomes_r05


def _seed() -> dict:
    return {
        "schema": "omega-pr-5k2n-r04-frozen-static-seed/v0.1.0",
        "source_target_head_sha": "a" * 40,
        "source_r04_fingerprint": "f" * 64,
        "source_workflow_run_id": 1,
        "source_artifact_id": 2,
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
                "python_symbol_assets": ["symbol:X.run"],
                "target_exact_path_overlap": [],
                "intent_overlap_proxy": 0.2,
                "evidence_class": "STATIC_SOURCE_TEST_SURFACE",
            }
        ],
        "boundary": "frozen integration seed",
    }


def test_stale_frozen_r04_propagates_to_zero_action_r05():
    r04 = compile_frozen_r04_hold(
        _seed(),
        target_pr_genome={
            "ref": "pr:o/r#452",
            "head_sha": "b" * 40,
            "changed_files": [],
            "named_concepts": [],
            "intent_tokens": [],
        },
    )
    assert r04["inspection_context_fresh"] is False
    assert r04["experiment_contract_count"] == 0

    r05 = compile_compatibility_outcomes_r05(r04)
    assert r05["experiment_contract_count"] == 0
    assert r05["outcome_receipt_count"] == 0
    assert r05["missing_outcome_contract_ids"] == []
    assert r05["verdict_counts"] == {
        "COMPATIBLE": 0,
        "INCOMPATIBLE": 0,
        "PARTIAL_COMPATIBLE": 0,
        "UNKNOWN": 0,
    }
    assert r05["memory_candidate_counts"] == {
        "M_PLUS_CANDIDATE": 0,
        "M_MINUS_CANDIDATE": 0,
        "M_QUERY_CANDIDATE": 0,
    }
    assert r05["automatic_reuse_authorized"] is False
    assert r05["automatic_memory_promotion_authorized"] is False
    assert r05["write_authority_granted"] is False
    assert r05["source_renderer_authorized"] is False
    assert r05["automatic_commit_allowed"] is False
    assert r05["automatic_merge_allowed"] is False
