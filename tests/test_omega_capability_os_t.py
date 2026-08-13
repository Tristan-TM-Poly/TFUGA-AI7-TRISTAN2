from omega_capability_os_t.core import (
    Intent,
    load_registry,
    make_evidence_receipt,
    outcome_record,
    plan,
    suggest_fallback,
    validate_registry,
)

REGISTRY = {
    "capabilities": [
        {
            "id": "read.meta", "domains": ["software"], "consumes": ["repo"],
            "produces": ["commit"], "authority": "read",
            "quality": .9, "information_gain": .8, "verifiability": .9, "reuse": .9,
            "cost": .1, "latency": .1, "risk": .1,
        },
        {
            "id": "logs.generic", "domains": ["software"], "consumes": ["commit"],
            "produces": ["log"], "authority": "read",
            "quality": .7, "information_gain": .8, "verifiability": .8, "reuse": .7,
            "cost": .1, "latency": .1, "risk": .1, "alternatives": ["logs.special"],
        },
        {
            "id": "logs.special", "domains": ["software"], "consumes": ["commit"],
            "produces": ["log"], "authority": "read",
            "quality": .98, "information_gain": .98, "verifiability": .98, "reuse": .9,
            "cost": .15, "latency": .15, "risk": .05,
        },
        {
            "id": "write.patch", "domains": ["software"], "consumes": ["repo"],
            "produces": ["mutation"], "authority": "write",
            "quality": .99, "information_gain": .1, "verifiability": .9, "reuse": .8,
            "cost": .1, "latency": .1, "risk": .9,
        },
    ]
}


def test_registry_and_deterministic_recursive_plan():
    registry = load_registry(REGISTRY)
    assert validate_registry(registry)["status"] == "PASS"
    intent = Intent("x", ("repo",), ("log",), ("software",))
    health = {"logs.generic": {"status": "DEGRADED"}, "logs.special": {"status": "PASS"}}
    first = plan(registry, intent, health)
    second = plan(registry, intent, health)
    assert first["fingerprint"] == second["fingerprint"]
    assert [step["capability_id"] for step in first["steps"]] == ["read.meta", "logs.special"]


def test_mutation_is_blocked_by_default():
    registry = load_registry(REGISTRY)
    intent = Intent("read-only", ("repo",), ("mutation",), ("software",))
    result = plan(registry, intent, {})
    assert result["status"] == "HOLD"
    assert result["unresolved_outputs"] == ["mutation"]


def test_mutation_can_be_planned_when_explicitly_allowed():
    registry = load_registry(REGISTRY)
    intent = Intent("write-ok", ("repo",), ("mutation",), ("software",), allow_mutation=True)
    result = plan(registry, intent, {})
    assert result["status"] == "READY"
    assert result["steps"][0]["capability_id"] == "write.patch"


def test_fallback_and_negative_memory():
    registry = load_registry(REGISTRY)
    health = {"logs.generic": {"status": "FAIL"}, "logs.special": {"status": "PASS"}}
    fallback = suggest_fallback(registry, "logs.generic", health)
    assert fallback["fallback"] == "logs.special"
    record = outcome_record("logs.generic", "failure", symptom="empty response", recovery_chain=["logs.special"])
    assert record["memory"] == "M-"


def test_sha_freshness_is_mandatory_for_oak_pass():
    registry = load_registry(REGISTRY)
    intent = Intent("x", ("repo",), ("log",), ("software",))
    payload = plan(registry, intent, {"logs.special": "PASS"})
    fresh = make_evidence_receipt(payload, candidate_sha="abc", evidence_sha="abc")
    stale = make_evidence_receipt(payload, candidate_sha="def", evidence_sha="abc")
    assert fresh["oak"]["status"] == "PASS"
    assert stale["oak"]["status"] == "HOLD"
    assert stale["fresh"] is False


def test_fail_health_capability_is_never_selected():
    registry = load_registry(REGISTRY)
    intent = Intent("x", ("repo",), ("log",), ("software",))
    result = plan(registry, intent, {"logs.special": "FAIL", "logs.generic": "PASS"})
    ids = [step["capability_id"] for step in result["steps"]]
    assert "logs.special" not in ids
    assert "logs.generic" in ids
