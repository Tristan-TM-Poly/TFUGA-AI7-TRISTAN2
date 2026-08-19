from omega_action_ext_t import ActionDNA, ActionManifest, OAKGate, RiskTensor, incident_rules, score_report
from omega_action_ext_t.connectors.github_dryrun import GitHubDryRunConnector


def test_incident_codex_contains_anti_rules():
    rules = incident_rules()
    codes = {rule["code"] for rule in rules}
    assert "email_without_confirmation" in codes
    assert "destructive_no_rollback" in codes


def test_oakbench_penalizes_bad_auto_public_ip():
    action = ActionDNA(
        name="Public IP action",
        system="github",
        action_type="publish_release",
        public=True,
        touches_ip=True,
        approved=False,
        risk=RiskTensor(ip=3),
    )
    report = OAKGate().dry_run(action)
    score = score_report(report)
    assert score.total >= 0
    assert report.decision.value == "needs_approval"


def test_github_dryrun_connector_never_executes():
    action = ActionDNA(
        name="Open draft PR",
        system="github",
        action_type="open_pr",
        approved=True,
        reversible=True,
        rollback="close_pr",
        risk=RiskTensor(ip=1),
    )
    manifest = ActionManifest.compile(action)
    plan = GitHubDryRunConnector().plan(manifest)
    assert plan.connector == "github_dryrun"
    assert plan.would_call == "github.open_pr"
    assert any("dry-run only" in note for note in plan.safety_notes)
