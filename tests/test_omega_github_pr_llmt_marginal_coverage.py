from __future__ import annotations

from omega_capability_os_t.github_pr_llmt_inspection import compile_inspection_plan


def _packet(target_ref: str, number: int, candidates: list[tuple[str, int, str]]):
    return {
        "target": {
            "ref": target_ref,
            "number": number,
            "head_sha": f"target-{number}",
        },
        "historical_retrieval": {
            "candidates": [
                {"ref": ref, "rank": rank, "head_sha": head_sha}
                for ref, rank, head_sha in candidates
            ]
        },
        "known_later_descendants": [],
    }


def test_checkpoint_marginal_coverage_beats_redundant_total_fanout():
    portfolio = {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "m" * 64,
        "packets": [
            _packet("pr:o/r#10", 10, [("pr:o/r#1", 1, "sha1"), ("pr:o/r#2", 2, "sha2")]),
            _packet("pr:o/r#11", 11, [("pr:o/r#1", 1, "sha1"), ("pr:o/r#2", 2, "sha2")]),
            _packet("pr:o/r#12", 12, [("pr:o/r#3", 1, "sha3")]),
        ],
    }
    checkpoint = {
        "schema": "omega-pr-llmt-inspection-checkpoint/v0.1.0",
        "fingerprint": "c" * 64,
        "completed_heads": {"pr:o/r#1": "sha1"},
    }

    plan = compile_inspection_plan(portfolio, checkpoint=checkpoint, max_candidates=1)

    assert plan["selection_policy"] == "greedy_marginal_uncovered_packet_coverage/v0.1"
    assert plan["completed_packet_coverage_count"] == 2
    assert plan["remaining_uncovered_packet_count_before_selection"] == 1
    assert plan["selected_refs"] == ["pr:o/r#3"]
    assert plan["selected_new_packet_coverage_count"] == 1
    assert plan["selected_marginal_pair_count"] == 1
    assert plan["projected_packet_coverage_after_selection_count"] == 3
    assert plan["remaining_uncovered_packet_count_after_selection"] == 0
    assert plan["selection_trace"][0]["marginal_uncovered_targets"] == ["pr:o/r#12"]


def test_greedy_selection_avoids_redundant_second_pick_inside_same_wave():
    portfolio = {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "g" * 64,
        "packets": [
            _packet("pr:o/r#20", 20, [("pr:o/r#5", 1, "sha5"), ("pr:o/r#6", 2, "sha6")]),
            _packet("pr:o/r#21", 21, [("pr:o/r#5", 1, "sha5"), ("pr:o/r#6", 2, "sha6")]),
            _packet("pr:o/r#22", 22, [("pr:o/r#5", 1, "sha5")]),
            _packet("pr:o/r#23", 23, [("pr:o/r#7", 1, "sha7")]),
        ],
    }

    plan = compile_inspection_plan(portfolio, max_candidates=2)

    assert plan["selected_refs"] == ["pr:o/r#5", "pr:o/r#7"]
    assert [row["marginal_uncovered_fanout"] for row in plan["selection_trace"]] == [3, 1]
    assert plan["selected_new_packet_coverage_count"] == 4
    assert plan["remaining_uncovered_packet_count_after_selection"] == 0
    assert "pr:o/r#6" not in plan["selected_refs"]


def test_marginal_policy_remains_deterministic_and_budget_is_not_hard_cap():
    portfolio = {
        "schema": "omega-pr-llmt-portfolio/v0.1.0",
        "fingerprint": "d" * 64,
        "packets": [
            _packet("pr:o/r#30", 30, [("pr:o/r#8", 1, "sha8")]),
            _packet("pr:o/r#31", 31, [("pr:o/r#9", 1, "sha9")]),
        ],
    }
    left = compile_inspection_plan(portfolio, max_candidates=1)
    right = compile_inspection_plan(portfolio, max_candidates=1)
    assert left == right
    assert left["operational_budget"]["architecture_hard_cap"] is False
    assert len(left["fingerprint"]) == 64
