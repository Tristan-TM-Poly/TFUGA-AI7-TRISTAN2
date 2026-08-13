from __future__ import annotations

from omega_capability_os_t.github_pr_generation_r02 import compile_pr_generation_r02


def _capsule(
    *,
    selected: tuple[str, ...] = ("repo:cap-existing",),
    sources: tuple[str, ...] = ("pr:o/r#10",),
    residual: tuple[str, ...] = ("implementation",),
    coverage: float = 0.5,
    residual_decision: str = "EXTEND",
    negative_hits: bool = False,
) -> dict:
    return {
        "schema": "omega-github-cumulative-intelligence/v1.2.0",
        "request": {
            "request_id": "req-r02",
            "description": "Extend an existing reusable PR capability with tests and evidence",
            "domains": ["github", "generation"],
            "consumes": ["historical-memory"],
            "produces": ["implementation", "tests", "evidence"],
        },
        "minimal_reuse_coalition": {
            "request_id": "req-r02",
            "selected_capabilities": list(selected),
            "source_refs": list(sources),
            "inspected_pr_candidates": ["pr:o/r#10", "pr:o/r#8"],
            "requested_outputs": ["implementation", "tests", "evidence"],
            "contract_covered_outputs": ["tests", "evidence"] if residual else ["implementation", "tests", "evidence"],
            "residual_outputs": list(residual),
            "reuse_coverage_ratio": coverage,
        },
        "repository_residual_courts": [
            {
                "repository": "o/r",
                "residual": {
                    "decision": residual_decision,
                    "required_tests": [
                        "unit tests for every residual output",
                        "integration test against selected reused capabilities",
                    ],
                    "required_provenance": ["pr:o/r#10"],
                },
            }
        ],
        "relevant_pr_genomes": [],
        "negative_memory_hits": (
            [{"ref": "pr:o/r#3", "failure_memory": ["M- prior duplicated interface"]}]
            if negative_hits else []
        ),
    }


def _genome() -> dict:
    return {
        "ref": "pr:o/r#452",
        "repository": "o/r",
        "number": 452,
        "lifecycle": "DRAFT",
        "changed_files": ["omega/example.py", "tests/test_example.py"],
        "named_concepts": ["Ω-PR-5K2N-T∞", "OAK"],
        "intent_tokens": ["reuse", "generation", "tests"],
    }


def _policy(action: str = "EXTEND", *, evidence: bool = True, utility: float = 0.8) -> dict:
    return {
        "schema": "omega-reuse-outcome-policy/v0.7.0",
        "receipt_count": 4,
        "actions": {
            action: {
                "n": 4,
                "successes": 3,
                "failures": 1,
                "degraded": 0,
                "mean_utility": utility,
                "evidence_refs": ["evidence:reuse-bench"] if evidence else [],
            }
        },
        "capabilities": {},
        "memory_counts": {"M+": 3, "M-": 1, "M?": 0},
    }


def test_r02_extends_partial_reuse_and_preserves_exact_logical_law():
    report = compile_pr_generation_r02(
        _capsule(),
        target_pr_genome=_genome(),
        generation=20,
        candidate_budget=48,
        physical_contract_budget=12,
    )
    assert report["historical_context"]["decision"] == "EXTEND"
    assert report["historical_context"]["history_enriched"] is True
    assert report["logical_cardinality_decimal"] == str(5000 * (2**20))
    assert report["logical_population_materialized"] is False
    assert report["physical_patch_contract_count"] <= 12
    assert len(report["fingerprint"]) == 64


def test_full_single_capability_coverage_routes_to_reuse_and_blocks_new_code():
    report = compile_pr_generation_r02(
        _capsule(residual=(), coverage=1.0, residual_decision="REUSE"),
        target_pr_genome=_genome(),
        candidate_budget=64,
        physical_contract_budget=32,
    )
    assert report["historical_context"]["decision"] == "REUSE"
    assert report["historical_context"]["physical_code_generation_allowed"] is False
    assert all(row["family"] != "code" for row in report["physical_patch_contracts"])


def test_multiple_full_coverage_capabilities_route_to_compose():
    report = compile_pr_generation_r02(
        _capsule(
            selected=("repo:cap-a", "repo:cap-b"),
            sources=("pr:o/r#10", "pr:o/r#11"),
            residual=(),
            coverage=1.0,
            residual_decision="COMPOSE",
        ),
        target_pr_genome=_genome(),
    )
    assert report["historical_context"]["decision"] == "COMPOSE"
    assert all(row["family"] != "code" for row in report["physical_patch_contracts"])


def test_no_reuse_with_residual_routes_to_create_residual():
    report = compile_pr_generation_r02(
        _capsule(
            selected=(),
            sources=(),
            residual=("implementation", "tests"),
            coverage=0.0,
            residual_decision="CREATE",
        ),
        target_pr_genome=_genome(),
        candidate_budget=64,
        physical_contract_budget=32,
    )
    assert report["historical_context"]["decision"] == "CREATE_RESIDUAL"
    assert report["historical_context"]["physical_code_generation_allowed"] is True
    assert report["physical_patch_contract_count"] > 0


def test_inspect_is_fail_closed_even_with_high_empirical_history():
    capsule = _capsule(residual=("implementation",), residual_decision="INSPECT")
    report = compile_pr_generation_r02(
        capsule,
        target_pr_genome=_genome(),
        outcome_policy=_policy("INSPECT", utility=2.0),
        candidate_budget=64,
        physical_contract_budget=32,
    )
    assert report["historical_context"]["decision"] == "INSPECT"
    assert report["physical_patch_contracts"] == []
    assert report["physical_patch_contract_count"] == 0
    assert report["adaptive_continuation"]["next_generation_candidate"] is None


def test_empirical_outcome_adjustment_requires_evidence_refs():
    baseline = compile_pr_generation_r02(
        _capsule(),
        target_pr_genome=_genome(),
        outcome_policy=None,
        candidate_budget=32,
    )
    missing_evidence = compile_pr_generation_r02(
        _capsule(),
        target_pr_genome=_genome(),
        outcome_policy=_policy(evidence=False, utility=1.5),
        candidate_budget=32,
    )
    evidenced = compile_pr_generation_r02(
        _capsule(),
        target_pr_genome=_genome(),
        outcome_policy=_policy(evidence=True, utility=1.5),
        candidate_budget=32,
    )
    assert baseline["empirical_outcome_signal_used"] is False
    assert missing_evidence["empirical_outcome_signal_used"] is False
    assert evidenced["empirical_outcome_signal_used"] is True
    assert missing_evidence["evaluated_candidates"][0]["empirical_outcome_term"] == 0.0
    assert evidenced["evaluated_candidates"][0]["empirical_outcome_term"] > 0.0


def test_negative_memory_is_a_visible_penalty_not_a_hidden_veto():
    clean = compile_pr_generation_r02(
        _capsule(negative_hits=False),
        target_pr_genome=_genome(),
        candidate_budget=24,
    )
    warned = compile_pr_generation_r02(
        _capsule(negative_hits=True),
        target_pr_genome=_genome(),
        candidate_budget=24,
    )
    assert clean["evaluated_candidates"][0]["negative_memory_penalty"] == 0.0
    assert warned["evaluated_candidates"][0]["negative_memory_penalty"] > 0.0
    assert warned["historical_context"]["negative_memory_refs"] == ["pr:o/r#3"]


def test_physical_patch_compiler_emits_review_contracts_not_code_or_authority():
    report = compile_pr_generation_r02(
        _capsule(),
        target_pr_genome=_genome(),
        outcome_policy=_policy(),
        candidate_budget=64,
        physical_contract_budget=20,
    )
    assert report["physical_patch_contracts"]
    for contract in report["physical_patch_contracts"]:
        assert contract["materialization_status"] == "REVIEW_CONTRACT_ONLY"
        assert contract["code_change_generated"] is False
        assert contract["write_authority_granted"] is False
        assert contract["automatic_commit_allowed"] is False
        assert contract["automatic_merge_allowed"] is False
        assert contract["human_review_required"] is True
        assert contract["rollback_required"] is True
        assert contract["required_tests"]
        assert contract["required_evidence"]


def test_synergy_pairs_remain_noncausal_planning_proxies():
    report = compile_pr_generation_r02(
        _capsule(),
        target_pr_genome=_genome(),
        candidate_budget=64,
        physical_contract_budget=16,
    )
    assert len(report["synergy_pairs"]) <= 16
    assert all(row["causal_synergy_proven"] is False for row in report["synergy_pairs"])


def test_r02_is_deterministic_and_large_n_remains_bounded():
    kwargs = dict(
        cumulative_intelligence=_capsule(),
        target_pr_genome=_genome(),
        outcome_policy=_policy(),
        generation=128,
        candidate_budget=24,
        physical_contract_budget=8,
    )
    left = compile_pr_generation_r02(**kwargs)
    right = compile_pr_generation_r02(**kwargs)
    assert left == right
    assert left["logical_cardinality_decimal"] == str(5000 * (2**128))
    assert left["evaluated_candidate_count"] <= 24
    assert left["physical_patch_contract_count"] <= 8
    assert left["adaptive_continuation"]["architecture_hard_cap"] is False


def test_outcome_policy_does_not_change_structural_reuse_decision():
    capsule = _capsule(residual=(), coverage=1.0, residual_decision="REUSE")
    hostile_policy = _policy("REUSE", utility=-2.0)
    report = compile_pr_generation_r02(
        capsule,
        target_pr_genome=_genome(),
        outcome_policy=hostile_policy,
        candidate_budget=32,
    )
    assert report["historical_context"]["decision"] == "REUSE"
    assert report["outcome_signal"]["observational_only"] is True
    assert all(row["family"] != "code" for row in report["physical_patch_contracts"])


def test_changed_capsule_content_changes_fingerprint():
    left = compile_pr_generation_r02(
        _capsule(), target_pr_genome=_genome(), candidate_budget=16
    )
    changed = _capsule()
    changed["request"]["description"] += " with an additional falsifier"
    right = compile_pr_generation_r02(
        changed, target_pr_genome=_genome(), candidate_budget=16
    )
    assert left["fingerprint"] != right["fingerprint"]
