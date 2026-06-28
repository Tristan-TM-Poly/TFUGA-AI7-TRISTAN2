import pytest

from omega_info2 import GitHubRunContext, build_post_merge_report


def test_reporter_refuses_final_summary_before_merge():
    context = GitHubRunContext(
        requested_go_github=True,
        pr_open=True,
        ci_green=True,
        mergeable=True,
        merged=False,
        used_fresh_head_sha=True,
    )
    with pytest.raises(ValueError, match="before merge"):
        build_post_merge_report(context, pr_number=1, pr_url="https://example.test/pr/1")


def test_reporter_builds_merged_report_after_merge():
    context = GitHubRunContext(
        requested_go_github=True,
        pr_open=True,
        ci_green=True,
        mergeable=True,
        merged=True,
        used_fresh_head_sha=True,
        summary_after_merge=True,
    )
    report = build_post_merge_report(
        context,
        pr_number=144,
        pr_url="https://example.test/pr/144",
        merge_sha="abc123",
        files_changed=["src/example.py", "tests/test_example.py"],
        notes=["CI green", "Merged automatically"],
    )
    payload = report.to_dict()
    assert payload["status"] == "MERGED"
    assert "Go GitHub completed and merged" in payload["body"]
    assert "abc123" in payload["body"]
    assert "src/example.py" in payload["body"]


def test_reporter_allows_real_blocker_report():
    context = GitHubRunContext(
        requested_go_github=True,
        pr_open=True,
        ci_green=True,
        mergeable=True,
        merged=False,
        real_blocker="Missing permission.",
    )
    report = build_post_merge_report(context, pr_number=2)
    assert report.status == "BLOCKED_REAL"
    assert "Missing permission" in report.body
