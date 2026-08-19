from omega_action_ext_t.core import Decision
from omega_action_ext_t.green_builder import PRGreenState
from omega_action_ext_t.pr_green_pipeline import (
    build_green_packet,
    build_green_packets,
    render_batch_report,
    summarize_packets,
)


def test_clean_packet_builds_manifest_but_requires_expected_sha():
    state = PRGreenState(
        number=2,
        title="clean packet",
        draft=False,
        mergeable=True,
        checks_state="clean",
        metadata={"head_sha": "abc123", "url": "https://example.test/pull/2"},
    )

    packet = build_green_packet(state)

    assert packet.plan.decision == "merge_now"
    assert packet.manifest.action.system == "github"
    assert packet.manifest.action.action_type == "merge_pull_request_when_clean"
    assert packet.manifest.action.metadata["expected_head_sha_required"] == "true"
    assert packet.manifest.dry_run.decision in {Decision.NEEDS_APPROVAL, Decision.ALLOW_AUTO}


def test_failing_packet_routes_to_enrichment_not_merge():
    state = PRGreenState(
        number=45,
        title="failing Daily Omega",
        draft=False,
        mergeable=True,
        checks_state="failure",
        changed_files=("sage_tristan/daily_omega.py",),
    )

    packet = build_green_packet(state)

    assert packet.plan.decision == "auto_enrich"
    assert packet.manifest.action.action_type == "enrich_pull_request_to_green"
    assert not packet.should_execute_without_review
    assert "PR #45 build-to-green plan" in packet.report_markdown


def test_conflicted_packet_writes_repair_report_path():
    state = PRGreenState(
        number=9,
        title="conflicted",
        draft=False,
        mergeable=False,
        checks_state="success",
        has_conflicts=True,
    )

    packet = build_green_packet(state)

    assert packet.plan.decision == "manual_required"
    assert packet.manifest.action.action_type == "write_repair_report"
    assert packet.manifest.action.risk.irreversibility == 2


def test_batch_summary_and_report_are_deterministic():
    states = (
        PRGreenState(number=45, title="failing", draft=False, mergeable=True, checks_state="failure"),
        PRGreenState(number=2, title="clean", draft=False, mergeable=True, checks_state="clean"),
        PRGreenState(number=165, title="draft", draft=True, mergeable=True, checks_state="clean"),
    )

    packets = build_green_packets(states)
    summary = summarize_packets(packets)
    report = render_batch_report(packets)

    assert [packet.state.number for packet in packets] == [2, 45, 165]
    assert summary["merge_now"] == [2]
    assert summary["auto_enrich"] == [45]
    assert summary["manual_required"] == [165]
    assert "PR Build-To-Green batch report" in report
    assert "#2" in report and "#45" in report and "#165" in report
