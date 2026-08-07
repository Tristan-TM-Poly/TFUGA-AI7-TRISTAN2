from __future__ import annotations

import hashlib
import json

import pytest

from omega_asm_t.cli import main
from omega_asm_t.counters import (
    DEFAULT_PERF_EVENTS,
    build_p5_report,
    derive_counter_metrics,
    parse_perf_stat_csv,
)
from omega_asm_t.microarch import (
    file_sha256,
    microarchitecture_manifest,
    normalize_architecture,
    parse_size_bytes,
    toolchain_manifest,
)


PERF_SAMPLE = """1000;;cycles;1000000;100.00;;
2000;;instructions;1000000;100.00;;
100;;branches;1000000;100.00;;
10;;branch-misses;1000000;100.00;;
50;;cache-references;1000000;100.00;;
5;;cache-misses;1000000;100.00;;
3.5;msec;task-clock;1000000;100.00;;
"""


def test_architecture_aliases_are_canonical():
    assert normalize_architecture("AMD64") == "x86_64"
    assert normalize_architecture("arm64") == "aarch64"
    assert normalize_architecture("riscv64") == "riscv64"


def test_cache_size_parser_is_binary_and_conservative():
    assert parse_size_bytes("48K") == 48 * 1024
    assert parse_size_bytes("2M") == 2 * 1024**2
    assert parse_size_bytes("1024") == 1024
    assert parse_size_bytes("nonsense") is None
    assert parse_size_bytes(None) is None


def test_microarchitecture_manifest_declares_observational_scope():
    manifest = microarchitecture_manifest()
    assert manifest["schema_version"] == 1
    assert manifest["architecture"]
    assert manifest["claim_scope"] == "observational_hardware_context_only"
    assert isinstance(manifest["isa_features"], list)
    assert isinstance(manifest["caches"], list)
    assert manifest["sources"]["proc_cpuinfo"] in {True, False}


def test_missing_toolchain_is_explicitly_unavailable():
    manifest = toolchain_manifest(["omega-asm-tool-that-does-not-exist-xyz"])
    row = manifest["omega-asm-tool-that-does-not-exist-xyz"]
    assert row["available"] is False
    assert row["path"] is None
    assert row["version"] is None


def test_file_sha256_is_replayable(tmp_path):
    path = tmp_path / "binary.bin"
    path.write_bytes(b"omega-asm-r2")
    assert file_sha256(path) == hashlib.sha256(b"omega-asm-r2").hexdigest()


def test_perf_parser_preserves_counter_values_and_running_fraction():
    parsed = parse_perf_stat_csv(PERF_SAMPLE)
    assert not parsed.diagnostics
    rows = {counter.event: counter for counter in parsed.counters}
    assert rows["cycles"].value == 1000.0
    assert rows["instructions"].value == 2000.0
    assert rows["task-clock"].unit == "msec"
    assert rows["cycles"].running_percentage == 100.0


def test_perf_parser_never_turns_unsupported_events_into_zero():
    parsed = parse_perf_stat_csv("<not supported>;;cycles;0;0.00;;\n")
    assert parsed.counters == ()
    assert parsed.skipped_events["cycles"] == "not supported"


def test_perf_parser_records_plain_permission_errors():
    parsed = parse_perf_stat_csv("Error:\nNo permission to enable cycles event.\n")
    assert parsed.counters == ()
    assert any("permission" in item.lower() for item in parsed.diagnostics)


def test_duplicate_perf_event_is_not_double_counted():
    parsed = parse_perf_stat_csv("10;;cycles;1;100;;\n20;;cycles;1;100;;\n")
    assert len(parsed.counters) == 1
    assert parsed.counters[0].value == 10.0
    assert any("duplicate" in item for item in parsed.diagnostics)


def test_derived_counter_metrics_are_dimensionless_ratios():
    parsed = parse_perf_stat_csv(PERF_SAMPLE)
    derived = derive_counter_metrics(parsed.counters)
    assert derived["ipc"] == pytest.approx(2.0)
    assert derived["cycles_per_instruction"] == pytest.approx(0.5)
    assert derived["branch_miss_rate"] == pytest.approx(0.1)
    assert derived["cache_miss_rate"] == pytest.approx(0.1)


def test_p5_report_is_available_with_hardware_counters_and_binary_hash(tmp_path):
    binary = tmp_path / "bench"
    binary.write_bytes(b"trusted-fixture")
    report = build_p5_report(
        PERF_SAMPLE,
        source_exit_code=0,
        binary_path=binary,
        machine={"architecture": "x86_64", "claim_scope": "test"},
    )
    assert report["evidence_level"] == "P5-hardware-counters"
    assert report["availability"] == "available"
    assert report["authority"] == "review_only"
    assert report["hardware_event_count"] == 6
    assert report["derived"]["ipc"] == pytest.approx(2.0)
    assert report["binary"]["sha256"] == hashlib.sha256(b"trusted-fixture").hexdigest()
    assert report["collection_contract"]["arbitrary_command_execution_by_package"] is False


def test_p5_report_permission_failure_is_unavailable_not_zero():
    report = build_p5_report(
        "Error:\nNo permission to enable cycles event.\n",
        source_exit_code=255,
        machine={"architecture": "x86_64"},
    )
    assert report["availability"] == "unavailable"
    assert report["counters"] == {}
    assert report["hardware_event_count"] == 0
    assert "permission" in report["reason"].lower()


def test_p5_report_with_only_software_counter_is_partial():
    report = build_p5_report(
        "3.5;msec;task-clock;1000;100.00;;\n",
        source_exit_code=0,
        machine={"architecture": "x86_64"},
    )
    assert report["availability"] == "partial"
    assert report["hardware_event_count"] == 0


def test_default_perf_events_are_stable_and_include_core_ratios():
    assert DEFAULT_PERF_EVENTS[:4] == (
        "cycles",
        "instructions",
        "branches",
        "branch-misses",
    )
    assert "cache-misses" in DEFAULT_PERF_EVENTS


def test_cli_p5_events_is_json(capsys):
    assert main(["p5-events"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["events"] == list(DEFAULT_PERF_EVENTS)


def test_cli_microarch_is_json(capsys):
    assert main(["microarch"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert payload["claim_scope"] == "observational_hardware_context_only"


def test_cli_p5_report_parses_external_evidence(tmp_path, capsys):
    path = tmp_path / "perf.csv"
    path.write_text(PERF_SAMPLE, encoding="utf-8")
    assert main(["p5-report", str(path), "--exit-code", "0"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["availability"] == "available"
    assert payload["derived"]["ipc"] == pytest.approx(2.0)
