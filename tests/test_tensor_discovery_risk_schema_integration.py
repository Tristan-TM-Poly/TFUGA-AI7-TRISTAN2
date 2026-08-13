import json
from pathlib import Path


def test_r07_schema_requires_cumulative_risk_meta_routing():
    schema = json.loads(Path("schemas/tensor_discovery_bench_r07.schema.json").read_text(encoding="utf-8"))
    assert "meta_routing_uses_cumulative_risk_gate" in schema["required"]
    assert schema["properties"]["meta_routing_uses_cumulative_risk_gate"]["const"] is True
