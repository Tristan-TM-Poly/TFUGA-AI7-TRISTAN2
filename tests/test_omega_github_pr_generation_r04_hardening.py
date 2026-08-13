from __future__ import annotations

from omega_capability_os_t.github_pr_generation_r04 import compile_compatibility_inspection_r04


def test_exact_head_metadata_only_candidate_is_not_experiment_eligible():
    ref = "pr:o/r#11"
    head = "b" * 40
    r03 = {
        "schema": "omega-pr-5k2n-generation-dual-plane/v0.3.0",
        "artifact_residual_plane": {"decision": "INSPECT", "residual_outputs": ["implementation"]},
        "compatibility_inspection_plan": [
            {
                "rank": 1,
                "ref": ref,
                "head_sha": head,
                "inspection_status": "NOT_EXECUTED",
                "compatibility_proven": False,
                "reuse_authorized": False,
            }
        ],
    }
    index = {
        "schema": "omega-github-memory-index/v0.1.0",
        "capabilities": [],
        "prs": [
            {
                "repository": "o/r",
                "number": 11,
                "state": "closed",
                "title": "metadata historical candidate",
                "body": "documentation only",
                "head_sha": head,
                "head_ref": "feat/meta",
                "base_ref": "main",
                "draft": False,
                "merged": True,
                "files": ["README.md", "docs/NOTE.md"],
                "updated_at": "2026-08-02T00:00:00Z",
                "url": "https://example.invalid/pr/11"
            }
        ],
        "assets": [],
        "edges": [],
        "atlas_receipts": []
    }
    hydration = {
        "schema": "omega-github-progressive-retrieval/v0.3.0",
        "request_id": "r04-meta",
        "candidate_prs": [ref],
        "hydrated_prs": [ref],
        "changed_file_count": 2,
        "symbol_count": 0,
        "errors": [],
        "boundary": "inspection only"
    }
    target = {
        "ref": "pr:o/r#452",
        "head_sha": "t" * 40,
        "changed_files": [],
        "named_concepts": ["Ω-PR-5K2N-T∞"],
        "intent_tokens": ["generation"]
    }

    report = compile_compatibility_inspection_r04(
        r03, index, hydration, target_pr_genome=target
    )

    receipt = report["compatibility_receipts"][0]
    assert receipt["hydration_status"] == "HYDRATED_EXACT_HEAD"
    assert receipt["evidence_class"] == "METADATA_ONLY"
    assert receipt["experiment_eligible"] is False
    assert receipt["experiment_block_reason"] == "no_technical_source_or_symbol_surface"
    assert report["experiment_eligible_candidate_count"] == 0
    assert report["experiment_contract_count"] == 0
    assert report["compatibility_proven_count"] == 0
    assert report["reuse_authorized_count"] == 0
