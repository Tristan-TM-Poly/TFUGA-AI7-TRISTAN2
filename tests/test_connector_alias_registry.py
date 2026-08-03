from tools.connector_alias_registry import default_alias_registry


def test_default_alias_resolves_known_mapping():
    registry = default_alias_registry()
    assert registry.resolve("safe_fork_engine") == "tools/option_selector.py"
    assert registry.resolve("progress_trace") == "schemas/progress_log.schema.json"


def test_unknown_alias_returns_none():
    registry = default_alias_registry()
    assert registry.resolve("unknown") is None
