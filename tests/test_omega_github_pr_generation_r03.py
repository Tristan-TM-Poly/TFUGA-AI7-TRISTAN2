from __future__ import annotations

from omega_capability_os_t.github_pr_generation_r03 import (
    PROCESS_OUTPUTS,
    build_process_capability_request,
    compile_pr_generation_r03,
    process_request_to_dict,
)


def _genome() -> dict:
    return {
        "ref": "pr:o/r#452",
        "repository": "o/r",
        "number": 452,
        "lifecycle": "DRAFT",
        "head_sha": "h" * 40,
        "changed_files": ["omega/example.py", "tests/test_example.py"],
        "named_concepts": ["Ω-PR-5K2N-T∞", "OAK"],
        "intent_tokens": ["reuse", "generation", "tests"],
    }


def _process_capsule(*, complete: bool = True) -> dict:
    covered = list(PROCESS_OUTPUTS if complete else PROCESS_OUTPUTS[:-1])
    residual = [] if complete else [PROCESS_OUTPUTS[-1]]
    return {
        "schema": "omega-github-cumulative-intelligence/v1.2.0",
        "request": {
            "request_id": "process",
            "description": "reuse process",
            "domains": ["github", "memory"],
            "consumes": ["repository"],
            "produces": list(PROCESS_OUTPUTS),
        },
        "minimal_reuse_coalition": {
            "request_id": "process",
            "selected_capabilities": [
                "repo:github.memory.index",
                "repo:github.capability_graph.compile",
                "repo:github.reuse_before_create",
                "repo:github.residual.compile",
                "repo:github.llmt_context.compile",
            ],
            "source_refs": ["registry:capability-os"],
            "inspected_pr_candidates": [],
            "requested_outputs": list(PROCESS_OUTPUTS),
            "contract_covered_outputs": covered,
            "residual_outputs": residual,
            "reuse_coverage_ratio": len(covered) / len(PROCESS_OUTPUTS),
        },
        "repository_residual_courts": [],
        "relevant_pr_genomes": [],
        "negative_memory_hits": [],
    }


def _artifact_capsule(
    *,
    selected: tuple[str, ...] = (),
    residual: tuple[str, ...] = ("implementation", "tests", "evidence", "documentation"),
    candidates: tuple[str, ...] = ("pr:o/r#100", "pr:o/r#101"),
    negative_hits: bool = False,
    explicit_inspect: bool = False,
) -> dict:
    covered = [x for x in ("implementation", "tests", "evidence", "documentation") if x not in residual]
    residual_decision = "INSPECT" if explicit_inspect else ("EXTEND" if selected and residual else "CREATE")
    return {
        "schema": "omega-github-cumulative-intelligence/v1.2.0",
        "request": {
            "request_id": "artifact",
            "description": "build target artifact",
            "domains": ["github", "software"],
            "consumes": ["prior_pr_memory"],
            "produces": ["implementation", "tests", "evidence", "documentation"],
        },
        "minimal_reuse_coalition": {
            "request_id": "artifact",
            "selected_capabilities": list(selected),
            "source_refs": ["pr:o/r#90"] if selected else [],
            "inspected_pr_candidates": list(candidates),
            "requested_outputs": ["implementation", "tests", "evidence", "documentation"],
            "contract_covered_outputs": covered,
            "residual_outputs": list(residual),
            "reuse_coverage_ratio": len(covered) / 4,
        },
        "repository_residual_courts": [
            {
                "repository": "o/r",
                "residual": {
                    "decision": residual_decision,
                    "required_tests": ["unit", "integration"],
                    "required_provenance": ["pr:o/r#90"] if selected else [],
                },
            }
        ],
        "relevant_pr_genomes": [
            {
                "ref": ref,
                "head_sha": str(i + 1) * 40,
                "changed_files": [f"module_{i}.py"],
                "symbol_assets": [f"symbol:{i}:f"],
            }
            for i, ref in enumerate(candidates)
        ],
        "negative_memory_hits": (
            [{"ref": "pr:o/r#80", "failure_memory": ["blocked historically"]}]
            if negative_hits else []
        ),
    }


def _policy(*, action: str = "INSPECT", failures: int = 0, evidence: bool = True) -> dict:
    return {
        "schema": "omega-reuse-outcome-policy/v0.7.0",
        "receipt_count": 4,
        "actions": {
            action: {
                "n": 4,
                "successes": 4 - failures,
                "failures": failures,
                "degraded": 0,
                "mean_utility": 0.4,
                "evidence_refs": ["evidence:outcome"] if evidence else [],
            }
        },
        "capabilities": {},
        "memory_counts": {"M+": 4 - failures, "M-": failures, "M?": 0},
    }


def test_process_request_uses_real_capability_outputs_not_generic_deliverables():
    request = build_process_capability_request(_genome())
    payload = process_request_to_dict(request)
    assert tuple(payload["produces"]) == PROCESS_OUTPUTS
    assert "implementation" not in payload["produces"]
    assert "tests" not in payload["produces"]


def test_complete_process_reuse_does_not_claim_artifact_reuse():
    report = compile_pr_generation_r03(
        _artifact_capsule(),
        _process_capsule(complete=True),
        target_pr_genome=_genome(),
        candidate_budget=32,
        physical_contract_budget=8,
    )
    assert report["process_reuse_plane"]["process_reuse_complete"] is True
    assert report["artifact_residual_plane"]["decision"] == "INSPECT"
    assert report["physical_patch_contract_count"] == 0


def test_historical_candidates_without_artifact_contract_fail_closed_to_inspect():
    report = compile_pr_generation_r03(
        _artifact_capsule(candidates=("pr:o/r#100",)),
        _process_capsule(),
        target_pr_genome=_genome(),
    )
    assert report["artifact_residual_plane"]["decision"] == "INSPECT"
    assert "historical_candidates_exist" in report["artifact_residual_plane"]["decision_basis"]
    assert report["adaptive_continuation"]["next_generation_candidate"] is None
    assert report["compatibility_inspection_plan"][0]["compatibility_proven"] is False
    assert report["compatibility_inspection_plan"][0]["reuse_authorized"] is False


def test_no_contract_and_no_historical_candidate_can_create_residual():
    report = compile_pr_generation_r03(
        _artifact_capsule(candidates=()),
        _process_capsule(),
        target_pr_genome=_genome(),
        candidate_budget=64,
        physical_contract_budget=16,
    )
    assert report["artifact_residual_plane"]["decision"] == "CREATE_RESIDUAL"
    assert report["artifact_residual_plane"]["exact_inspection_required"] is False
    assert report["physical_patch_contract_count"] > 0


def test_partial_explicit_artifact_contract_routes_to_extend():
    report = compile_pr_generation_r03(
        _artifact_capsule(
            selected=("repo:artifact-cap",),
            residual=("implementation", "tests"),
            candidates=("pr:o/r#90",),
        ),
        _process_capsule(),
        target_pr_genome=_genome(),
        candidate_budget=64,
        physical_contract_budget=16,
    )
    assert report["artifact_residual_plane"]["decision"] == "EXTEND"
    assert report["physical_patch_compiler"]["artifact_decision_gate"] == "EXTEND"


def test_full_explicit_artifact_contract_routes_to_reuse():
    report = compile_pr_generation_r03(
        _artifact_capsule(
            selected=("repo:artifact-cap",),
            residual=(),
            candidates=("pr:o/r#90",),
        ),
        _process_capsule(),
        target_pr_genome=_genome(),
    )
    assert report["artifact_residual_plane"]["decision"] == "REUSE"
    assert all(row["family"] != "code" for row in report["physical_patch_contracts"])


def test_regex_failure_memory_is_inspection_lead_not_numeric_m_minus_penalty():
    report = compile_pr_generation_r03(
        _artifact_capsule(negative_hits=True),
        _process_capsule(),
        target_pr_genome=_genome(),
        outcome_policy=None,
        candidate_budget=24,
    )
    assert report["artifact_residual_plane"]["heuristic_failure_memory_refs"] == ("pr:o/r#80",)
    assert report["heuristic_failure_memory_numeric_penalty"] == 0.0
    assert report["confirmed_negative_signal"]["applied"] is False
    assert all(row["heuristic_failure_memory_penalty"] == 0.0 for row in report["evaluated_candidates"])


def test_only_evidence_bearing_observed_failures_apply_negative_numeric_term():
    no_evidence = compile_pr_generation_r03(
        _artifact_capsule(candidates=()),
        _process_capsule(),
        target_pr_genome=_genome(),
        outcome_policy=_policy(action="CREATE", failures=2, evidence=False),
        candidate_budget=24,
    )
    evidenced = compile_pr_generation_r03(
        _artifact_capsule(candidates=()),
        _process_capsule(),
        target_pr_genome=_genome(),
        outcome_policy=_policy(action="CREATE", failures=2, evidence=True),
        candidate_budget=24,
    )
    assert no_evidence["confirmed_negative_signal"]["penalty"] == 0.0
    assert no_evidence["confirmed_negative_signal"]["applied"] is False
    assert evidenced["confirmed_negative_signal"]["penalty"] > 0.0
    assert evidenced["confirmed_negative_signal"]["applied"] is True


def test_inspection_plan_is_sha_aware_but_not_compatibility_proof():
    report = compile_pr_generation_r03(
        _artifact_capsule(candidates=("pr:o/r#100", "pr:o/r#101")),
        _process_capsule(),
        target_pr_genome=_genome(),
    )
    assert len(report["compatibility_inspection_plan"]) == 2
    first = report["compatibility_inspection_plan"][0]
    assert first["head_sha"]
    assert first["changed_files"]
    assert first["symbol_assets"]
    assert first["inspection_status"] == "NOT_EXECUTED"
    assert first["compatibility_proven"] is False
    assert first["reuse_authorized"] is False


def test_r03_large_n_remains_bounded_and_deterministic():
    kwargs = dict(
        artifact_cumulative_intelligence=_artifact_capsule(candidates=()),
        process_cumulative_intelligence=_process_capsule(),
        target_pr_genome=_genome(),
        generation=128,
        candidate_budget=24,
        physical_contract_budget=8,
    )
    left = compile_pr_generation_r03(**kwargs)
    right = compile_pr_generation_r03(**kwargs)
    assert left == right
    assert left["logical_cardinality_decimal"] == str(5000 * (2**128))
    assert left["evaluated_candidate_count"] <= 24
    assert left["physical_patch_contract_count"] <= 8
    assert left["adaptive_continuation"]["architecture_hard_cap"] is False
    assert len(left["fingerprint"]) == 64


def test_explicit_inspect_overrides_selected_artifact_capability():
    report = compile_pr_generation_r03(
        _artifact_capsule(
            selected=("repo:artifact-cap",),
            residual=("implementation",),
            candidates=("pr:o/r#90",),
            explicit_inspect=True,
        ),
        _process_capsule(),
        target_pr_genome=_genome(),
        outcome_policy=_policy(action="INSPECT", failures=0),
    )
    assert report["artifact_residual_plane"]["decision"] == "INSPECT"
    assert report["physical_patch_contract_count"] == 0
