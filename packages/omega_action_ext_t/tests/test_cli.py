import json

from omega_action_ext_t.cli import action_from_dict
from omega_action_ext_t import OAKGate, Decision


def test_cli_payload_parses_and_dry_runs():
    payload = {
        "name": "Professor outreach draft",
        "system": "gmail",
        "action_type": "send_email",
        "approved": False,
        "touches_humans": True,
        "touches_ip": True,
        "risk": {"ip": 2, "reputation": 2, "privacy": 1},
    }
    action = action_from_dict(json.loads(json.dumps(payload)))
    report = OAKGate().dry_run(action)
    assert report.decision == Decision.ALLOW_DRAFT
