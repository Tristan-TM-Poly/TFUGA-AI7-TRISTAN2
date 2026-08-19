from omega_action_ext_t import has_findings, scan_text, validate_payload


def test_validator_rejects_missing_required_fields():
    errors = validate_payload({"risk": {}})
    assert "missing_required_field:name" in errors
    assert "missing_required_field:system" in errors
    assert "missing_required_field:action_type" in errors


def test_validator_rejects_risk_out_of_range():
    errors = validate_payload({
        "name": "x",
        "system": "github",
        "action_type": "open_pr",
        "risk": {"ip": 9},
    })
    assert "risk_axis_out_of_range:ip" in errors


def test_validator_requires_timezone_for_calendar_like_action():
    errors = validate_payload({
        "name": "Meeting",
        "system": "calendar",
        "action_type": "create_event",
        "risk": {},
    })
    assert "calendar_like_action_requires_timezone" in errors


def test_validator_accepts_timezone_for_calendar_like_action():
    errors = validate_payload({
        "name": "Meeting",
        "system": "calendar",
        "action_type": "create_event",
        "risk": {},
        "metadata": {"timezone": "Europe/Amsterdam"},
    })
    assert errors == []


def test_leak_scan_finds_obvious_token_marker():
    text = "token = 'ghp_abcdefghijklmnopqrstuvwxyz123456'"
    findings = scan_text(text)
    assert has_findings(text)
    assert findings[0].kind in {"github_token_like", "generic_api_key"}


def test_leak_scan_ignores_plain_text():
    assert not has_findings("ordinary public roadmap text")
