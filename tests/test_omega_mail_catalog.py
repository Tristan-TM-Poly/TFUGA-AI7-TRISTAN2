"""Scale and integrity tests for Ω-MAIL-T R0.2 massive."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from omega_mail_t.catalog import audit, benchmarks_for, query_scenarios


def _load_generator():
    path = Path(__file__).parents[1] / "tools" / "generate_omega_mail_r02_massive.py"
    spec = importlib.util.spec_from_file_location("omega_mail_generator_r02", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_materializes_49152_linked_records(tmp_path: Path) -> None:
    generator = _load_generator()
    manifest = generator.materialize(tmp_path, scenario_shards=8, benchmark_shards=8)
    assert manifest["scenario_records"] == 16_384
    assert manifest["benchmark_records"] == 32_768
    assert manifest["total_records"] == 49_152
    assert manifest["validation"]["valid"] is True


def test_generation_is_deterministic(tmp_path: Path) -> None:
    generator = _load_generator()
    first = generator.materialize(tmp_path, scenario_shards=4, benchmark_shards=4)
    second = generator.materialize(tmp_path, scenario_shards=4, benchmark_shards=4)
    assert first["scenario_fingerprint"] == second["scenario_fingerprint"]
    assert first["benchmark_fingerprint"] == second["benchmark_fingerprint"]


def test_streaming_query_and_benchmark_links(tmp_path: Path) -> None:
    generator = _load_generator()
    generator.materialize(tmp_path, scenario_shards=8, benchmark_shards=8)
    root = tmp_path / "generated" / "omega_mail_t_r02"
    records = list(
        query_scenarios(
            root=root,
            company="tristan_oak_systems",
            intent="security_alert",
            anomaly="permission_boundary",
            locale="fr-CA",
            limit=4,
        )
    )
    assert records
    for record in records:
        linked = list(benchmarks_for(record.id, root=root))
        assert len(linked) == 2
        assert {item.benchmark_type for item in linked} == {
            "semantic_routing",
            "oak_safety",
        }


def test_audit_rejects_no_safety_or_link_gaps(tmp_path: Path) -> None:
    generator = _load_generator()
    generator.materialize(tmp_path, scenario_shards=8, benchmark_shards=8)
    report = audit(tmp_path / "generated" / "omega_mail_t_r02")
    assert report == {
        "valid": True,
        "scenario_count": 16_384,
        "benchmark_count": 32_768,
        "coverage_per_scenario": 2,
        "missing_scenarios": [],
        "undercovered": [],
        "unsafe_scenarios": [],
    }
