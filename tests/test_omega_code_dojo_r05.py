from __future__ import annotations

import pytest

from omega_code_dojo_t.r05 import (
    AccessRequest,
    ContaminationError,
    Decision,
    MultiJudgeEngine,
    MultiJudgePolicy,
    Normalizer,
    PLATFORMS,
    PlatformMode,
    PolicyGate,
    ProblemRef,
    fixture_references,
    run_r05_benchmark,
)


def test_platform_registry() -> None:
    assert len(PLATFORMS) == 9
    assert len({item.platform_id for item in PLATFORMS}) == 9
    assert all(set(item.allow) | set(item.review) | set(item.block) == set(PlatformMode) for item in PLATFORMS)


def test_dmoj_training_blocked() -> None:
    verdict = PolicyGate().evaluate(AccessRequest("dmoj", PlatformMode.TRAIN, "problem_metadata", automated=True))
    assert verdict.decision is Decision.BLOCK


def test_automated_submission_requires_review() -> None:
    verdict = PolicyGate().evaluate(AccessRequest("codewars", PlatformMode.SUBMIT, "user_owned_solution", automated=True, user_owned=True, license_id="MIT"))
    assert verdict.decision is not Decision.ALLOW
    assert "human_submission_required" in verdict.controls


def test_normalizer_rejects_statement() -> None:
    with pytest.raises(ContaminationError):
        Normalizer().normalize(({"platform_id": "codeforces", "external_id": "x", "statement": "forbidden"},))


def test_normalizer_deduplicates() -> None:
    refs = (
        ProblemRef("codeforces", "1A", "A", ("graph",), 0.4),
        ProblemRef("codeforces", "1A", "A", ("bfs",), 0.6, attempted=True),
    )
    normalized = Normalizer().normalize(refs)
    assert len(normalized) == 1
    assert normalized[0].difficulty == 0.6
    assert set(normalized[0].skills) == {"graph", "graph_traversal"}


def test_engine_resolves_shadow_budget() -> None:
    receipt = MultiJudgeEngine().run(
        fixture_references(8),
        MultiJudgePolicy(reference_budget=64, shadow_budget=32, max_attempts=2),
    )
    assert receipt["materialized_shadow_problems"] == 32
    assert receipt["solved_shadow_problems"] == 32
    assert receipt["shadow_solve_rate"] == 1.0


def test_no_external_solution_claim() -> None:
    receipt = MultiJudgeEngine().run(
        fixture_references(2),
        MultiJudgePolicy(reference_budget=8, shadow_budget=4),
    )
    assert receipt["claims"]["external_problem_solution_claimed"] is False
    assert all(item["manual_submission_required"] for item in receipt["resolutions"])


def test_logical_space() -> None:
    assert MultiJudgeEngine().logical_reference_space == 1_236_950_581_248


def test_benchmark_deterministic() -> None:
    first = run_r05_benchmark()
    second = run_r05_benchmark()
    assert first == second
    assert first["status"] == "CERTIFIED_MULTI_JUDGE_SHADOW_FIXTURES_R0_5"


def test_benchmark_invariants() -> None:
    payload = run_r05_benchmark()
    assert all(payload["invariants"].values())
    assert payload["materialized_shadow_problems"] == 256
    assert payload["blocked_references"] == 9
    assert payload["permanent_total_cap"] is None
