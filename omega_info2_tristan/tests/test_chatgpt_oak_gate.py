from omega_info2 import ChatGPTOAKGate, GitHubRunContext


def test_gate_demands_merge_when_green_and_mergeable_but_not_merged():
    decision = ChatGPTOAKGate().evaluate_github_context(
        GitHubRunContext(
            requested_go_github=True,
            pr_open=True,
            ci_green=True,
            mergeable=True,
            merged=False,
            used_fresh_head_sha=True,
        )
    )
    assert not decision.passed
    assert "MCHATGPT001" in decision.failed_rules
    assert any("Merge" in step or "merge" in step for step in decision.next_steps)


def test_gate_allows_post_merge_summary_after_merge():
    decision = ChatGPTOAKGate().evaluate_github_context(
        GitHubRunContext(
            requested_go_github=True,
            pr_open=True,
            ci_green=True,
            mergeable=True,
            merged=True,
            used_fresh_head_sha=True,
            summary_after_merge=True,
        )
    )
    assert decision.passed
    assert decision.action == "POST_MERGE_SUMMARY"


def test_gate_warns_on_repeated_ci_checks():
    decision = ChatGPTOAKGate().evaluate_github_context(
        GitHubRunContext(
            requested_go_github=True,
            pr_open=True,
            ci_green=True,
            mergeable=True,
            merged=False,
            used_fresh_head_sha=True,
            checks_per_head_sha=4,
        )
    )
    assert "MCHATGPT003" in decision.failed_rules


def test_gate_reports_real_blocker_instead_of_merge():
    decision = ChatGPTOAKGate().evaluate_github_context(
        GitHubRunContext(
            requested_go_github=True,
            pr_open=True,
            ci_green=True,
            mergeable=True,
            merged=False,
            real_blocker="Missing repository permission.",
        )
    )
    assert decision.action == "REPORT_BLOCKED_REAL"
    assert not decision.passed


def test_rules_markdown_contains_known_failure_codes():
    markdown = ChatGPTOAKGate().rules_as_markdown()
    assert "MCHATGPT001" in markdown
    assert "MCHATGPT007" in markdown
