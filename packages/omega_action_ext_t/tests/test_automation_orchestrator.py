from omega_action_ext_t import AutomationOrchestrator, ConnectorRouter, ActionDNA, ActionManifest, RiskTensor


def test_orchestrator_prepares_manifest_plan_queue_and_ledger(tmp_path):
    payload = {
        "name": "Professor outreach",
        "system": "gmail",
        "action_type": "send_email",
        "approved": False,
        "touches_humans": True,
        "touches_ip": True,
        "risk": {"ip": 2, "reputation": 2, "privacy": 1},
    }
    orchestrator = AutomationOrchestrator(
        queue_path=tmp_path / "queue.json",
        ledger_path=tmp_path / "ledger.jsonl",
    )
    result = orchestrator.prepare(payload)
    data = result.to_dict()
    assert data["manifest"]["manifest_hash"].startswith("sha256:")
    assert data["connector_plan"]["would_call"] == "gmail.create_draft"
    assert data["approval_item"] is not None
    assert data["ledger_hash"].startswith("sha256:")


def test_router_unknown_system_never_executes():
    action = ActionDNA(name="Unknown", system="unknown", action_type="do", risk=RiskTensor())
    manifest = ActionManifest.compile(action)
    plan = ConnectorRouter().plan(manifest)
    assert plan.connector == "unknown_dryrun"
    assert plan.would_call == "review_required"
