from __future__ import annotations

from omega_capability_os_t.github_pr_generation_r04 import compile_compatibility_inspection_r04


def _r03(planned_head: str = "a" * 40, refs: tuple[str, ...] = ("pr:o/r#10",)) -> dict:
    return {
        "schema": "omega-pr-5k2n-generation-dual-plane/v0.3.0",
        "artifact_residual_plane": {
            "decision": "INSPECT",
            "residual_outputs": ["implementation", "tests"],
        },
        "compatibility_inspection_plan": [
            {
                "rank": i + 1,
                "ref": ref,
                "head_sha": planned_head if i == 0 else "b" * 40,
                "inspection_status": "NOT_EXECUTED",
                "compatibility_proven": False,
                "reuse_authorized": False,
            }
            for i, ref in enumerate(refs)
        ],
    }


def _index(*, head: str = "a" * 40, include_second: bool = False) -> dict:
    prs = [
        {
            "repository": "o/r",
            "number": 10,
            "state": "closed",
            "title": "reuse generation compiler",
            "body": "tests and workflow evidence",
            "head_sha": head,
            "head_ref": "feat/x",
            "base_ref": "main",
            "draft": False,
            "merged": True,
            "files": [
                "omega/compiler.py",
                "tests/test_compiler.py",
                ".github/workflows/compiler.yml",
            ],
            "updated_at": "2026-08-01T00:00:00Z",
            "url": "https://example.invalid/pr/10",
        }
    ]
    if include_second:
        prs.append(
            {
                "repository": "o/r",
                "number": 11,
                "state": "closed",
                "title": "second historical candidate",
                "body": "metadata only",
                "head_sha": "b" * 40,
                "head_ref": "feat/y",
                "base_ref": "main",
                "draft": False,
                "merged": True,
                "files": ["README.md"],
                "updated_at": "2026-08-02T00:00:00Z",
                "url": "https://example.invalid/pr/11",
            }
        )
    assets = [
        {
            "asset_id": "symbol:pr:o/r#10:omega/compiler.py:Compiler.run",
            "source_ref": "pr:o/r#10",
            "source_kind": "pr_head_python_ast_symbol",
            "label": "omega/compiler.py::Compiler.run",
            "keywords": ["compiler", "run"],
            "confidence": 0.8,
            "boundary": "static only",
        }
    ]
    return {
        "schema": "omega-github-memory-index/v0.1.0",
        "capabilities": [],
        "prs": prs,
        "assets": assets,
        "edges": [],
        "atlas_receipts": [],
    }


def _hydration(*, hydrated: tuple[str, ...] = ("pr:o/r#10",), errors: tuple[dict, ...] = ()) -> dict:
    return {
        "schema": "omega-github-progressive-retrieval/v0.3.0",
        "request_id": "r04",
        "candidate_prs": ["pr:o/r#10"],
        "hydrated_prs": list(hydrated),
        "changed_file_count": 3,
        "symbol_count": 1,
        "errors": list(errors),
        "boundary": "inspection only",
    }


def _target() -> dict:
    return {
        "ref": "pr:o/r#452",
        "head_sha": "t" * 40,
        "changed_files": ["omega/compiler.py"],
        "named_concepts": ["Ω-PR-5K2N-T∞"],
        "intent_tokens": ["compiler", "reuse", "generation"],
    }


def test_exact_head_hydration_emits_static_receipt_not_compatibility_proof():
    report = compile_compatibility_inspection_r04(
        _r03(), _index(), _hydration(), target_pr_genome=_target()
    )
    receipt = report["compatibility_receipts"][0]
    assert receipt["hydration_status"] == "HYDRATED_EXACT_HEAD"
    assert receipt["head_match"] is True
    assert receipt["compatibility_verdict"] == "UNKNOWN"
    assert receipt["compatibility_proven"] is False
    assert receipt["reuse_authorized"] is False
    assert receipt["execution_authorized"] is False


def test_static_surface_detects_source_test_workflow_symbol_and_path_overlap():
    report = compile_compatibility_inspection_r04(
        _r03(), _index(), _hydration(), target_pr_genome=_target()
    )
    receipt = report["compatibility_receipts"][0]
    assert receipt["evidence_class"] == "STATIC_SOURCE_TEST_CI_SURFACE"
    assert receipt["source_files"] == ("omega/compiler.py",)
    assert receipt["test_files"] == ("tests/test_compiler.py",)
    assert receipt["workflow_files"] == (".github/workflows/compiler.yml",)
    assert receipt["python_symbol_assets"]
    assert receipt["target_exact_path_overlap"] == ("omega/compiler.py",)


def test_exact_head_hydration_compiles_experiment_contract_without_execution_authority():
    report = compile_compatibility_inspection_r04(
        _r03(), _index(), _hydration(), target_pr_genome=_target()
    )
    assert report["experiment_contract_count"] == 1
    exp = report["compatibility_experiment_contracts"][0]
    assert exp["candidate_head_sha"] == "a" * 40
    assert exp["execution_authorized"] is False
    assert exp["source_mutation_authorized"] is False
    assert exp["reuse_authorized_before_experiment"] is False
    assert exp["human_review_required"] is True
    assert "tests_executed" in exp["expected_receipt_fields"]


def test_stale_head_blocks_experiment_contract():
    report = compile_compatibility_inspection_r04(
        _r03(planned_head="a" * 40),
        _index(head="c" * 40),
        _hydration(),
        target_pr_genome=_target(),
    )
    receipt = report["compatibility_receipts"][0]
    assert receipt["hydration_status"] == "STALE_HEAD"
    assert receipt["head_match"] is False
    assert report["stale_candidate_count"] == 1
    assert report["experiment_contract_count"] == 0


def test_unhydrated_candidate_stays_unknown_and_unusable():
    report = compile_compatibility_inspection_r04(
        _r03(), _index(), _hydration(hydrated=()), target_pr_genome=_target()
    )
    receipt = report["compatibility_receipts"][0]
    assert receipt["hydration_status"] == "NOT_HYDRATED"
    assert receipt["evidence_class"] == "UNHYDRATED"
    assert receipt["reuse_authorized"] is False
    assert report["experiment_contract_count"] == 0


def test_hydration_errors_are_preserved_as_evidence_not_hidden():
    err = {"ref": "pr:o/r#10", "path": "bad.py", "error": "SyntaxError: x"}
    report = compile_compatibility_inspection_r04(
        _r03(), _index(), _hydration(errors=(err,)), target_pr_genome=_target()
    )
    assert report["hydration_errors"] == [err]


def test_candidate_budget_bounds_inspection_even_if_plan_is_larger():
    report = compile_compatibility_inspection_r04(
        _r03(refs=("pr:o/r#10", "pr:o/r#11")),
        _index(include_second=True),
        _hydration(hydrated=("pr:o/r#10", "pr:o/r#11")),
        target_pr_genome=_target(),
        max_candidates=1,
    )
    assert report["planned_candidate_count"] == 1
    assert len(report["compatibility_receipts"]) == 1


def test_r04_never_promotes_static_inspection_to_reuse_or_write_authority():
    report = compile_compatibility_inspection_r04(
        _r03(), _index(), _hydration(), target_pr_genome=_target()
    )
    assert report["compatibility_proven_count"] == 0
    assert report["reuse_authorized_count"] == 0
    assert report["physicalization_gate"] == "INSPECT"
    assert report["write_authority_granted"] is False
    assert report["execution_authorized"] is False
    assert report["automatic_commit_allowed"] is False
    assert report["automatic_merge_allowed"] is False
    assert len(report["fingerprint"]) == 64
