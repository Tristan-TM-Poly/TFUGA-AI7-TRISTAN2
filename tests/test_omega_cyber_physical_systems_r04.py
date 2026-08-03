from __future__ import annotations

import pytest

from omega_cyber_physical_systems_t.integration import (
    ADAPTER_TYPES,
    EXTERNAL_ADAPTER_TYPES,
    ExecutionSpec,
    IntegrationLedger,
    assess_activation,
    default_adapter_registry,
    execute_connector,
    normalize_exchange,
    probe_capabilities,
)
from omega_cyber_physical_systems_t.r04_fixtures import (
    invalid_json_loopback_spec,
    missing_executable_spec,
    nonzero_loopback_spec,
    normalized_demo_payloads,
    successful_loopback_spec,
    timeout_loopback_spec,
)
from omega_cyber_physical_systems_t.r04_oak import run_cps_r04_benchmarks


def test_adapter_registry_covers_all_declared_types() -> None:
    registry = default_adapter_registry()
    assert tuple(item.adapter_type for item in registry) == ADAPTER_TYPES
    assert len(EXTERNAL_ADAPTER_TYPES) == 6


def test_invalid_adapter_descriptor_is_rejected() -> None:
    from omega_cyber_physical_systems_t.integration import AdapterDescriptor

    with pytest.raises(ValueError):
        AdapterDescriptor("UNKNOWN", "invalid")


def test_execution_spec_requires_supported_adapter() -> None:
    with pytest.raises(ValueError):
        ExecutionSpec("bad", "UNKNOWN", ("python",))


def test_execution_spec_requires_argv() -> None:
    with pytest.raises(ValueError):
        ExecutionSpec("bad", "REFERENCE_LOOPBACK", ())


def test_execution_spec_requires_positive_timeout() -> None:
    with pytest.raises(ValueError):
        ExecutionSpec("bad", "REFERENCE_LOOPBACK", ("python",), timeout_s=0)


def test_capability_probe_does_not_activate_integrations() -> None:
    probes = probe_capabilities()
    assert len(probes) == len(ADAPTER_TYPES)
    assert all(not item.integration_active for item in probes)
    assert all(not item.execution_proven for item in probes)
    assert all(not item.hardware_validated for item in probes)


def test_capability_probe_hash_is_stable() -> None:
    first = probe_capabilities()
    second = probe_capabilities()
    assert [item.evidence_hash for item in first] == [item.evidence_hash for item in second]


def test_successful_loopback_executes_real_subprocess() -> None:
    receipt = execute_connector(successful_loopback_spec())
    assert receipt.process_started is True
    assert receipt.exit_code == 0
    assert receipt.success is True
    assert receipt.integration_active is True
    assert receipt.execution_proven_for_this_run is True
    assert receipt.output_json is not None
    assert receipt.output_json["samples"] == 3


def test_successful_receipt_hash_excludes_runtime_jitter() -> None:
    first = execute_connector(successful_loopback_spec())
    second = execute_connector(successful_loopback_spec())
    assert first.duration_s >= 0
    assert second.duration_s >= 0
    assert first.evidence_hash == second.evidence_hash


def test_nonzero_exit_is_blocked() -> None:
    receipt = execute_connector(nonzero_loopback_spec())
    assert receipt.exit_code == 7
    assert receipt.status == "NONZERO_EXIT"
    assert receipt.success is False
    assert receipt.integration_active is False


def test_invalid_json_is_blocked() -> None:
    receipt = execute_connector(invalid_json_loopback_spec())
    assert receipt.status == "INVALID_JSON"
    assert receipt.output_valid is False
    assert receipt.success is False


def test_timeout_is_blocked() -> None:
    receipt = execute_connector(timeout_loopback_spec())
    assert receipt.status == "TIMEOUT"
    assert receipt.timed_out is True
    assert receipt.success is False


def test_missing_executable_is_blocked() -> None:
    receipt = execute_connector(missing_executable_spec())
    assert receipt.status == "EXECUTABLE_NOT_FOUND"
    assert receipt.process_started is False
    assert receipt.success is False


def test_missing_required_json_key_is_blocked() -> None:
    import sys

    spec = ExecutionSpec(
        connector_id="missing-key",
        adapter_type="REFERENCE_LOOPBACK",
        argv=(sys.executable, "-c", "import json; print(json.dumps({'status':'ok'}))"),
        required_json_keys=("status", "samples"),
    )
    receipt = execute_connector(spec)
    assert receipt.missing_required_keys == ("samples",)
    assert receipt.output_valid is False
    assert receipt.success is False


def test_missing_artifact_is_blocked(tmp_path) -> None:
    import sys

    spec = ExecutionSpec(
        connector_id="missing-artifact",
        adapter_type="REFERENCE_LOOPBACK",
        argv=(sys.executable, "-c", "import json; print(json.dumps({'status':'ok'}))"),
        cwd=str(tmp_path),
        required_json_keys=("status",),
        expected_artifacts=("not-created.json",),
    )
    receipt = execute_connector(spec)
    assert receipt.status == "MISSING_ARTIFACT"
    assert receipt.artifacts[0].exists is False
    assert receipt.success is False


def test_existing_artifact_is_hashed(tmp_path) -> None:
    import sys

    artifact = tmp_path / "receipt.txt"
    artifact.write_text("evidence", encoding="utf-8")
    spec = ExecutionSpec(
        connector_id="artifact",
        adapter_type="REFERENCE_LOOPBACK",
        argv=(sys.executable, "-c", "import json; print(json.dumps({'status':'ok'}))"),
        cwd=str(tmp_path),
        required_json_keys=("status",),
        expected_artifacts=("receipt.txt",),
    )
    receipt = execute_connector(spec)
    assert receipt.success is True
    assert receipt.artifacts[0].size_bytes == 8
    assert len(receipt.artifacts[0].sha256 or "") == 64


@pytest.mark.parametrize("adapter_type", ADAPTER_TYPES)
def test_all_declared_exchange_fixtures_normalize(adapter_type: str) -> None:
    payload = normalized_demo_payloads()[adapter_type]
    exchange = normalize_exchange(adapter_type, payload, source_id=f"test-{adapter_type}")
    assert exchange.valid is True
    assert exchange.missing_keys == ()
    assert len(exchange.evidence_hash) == 64


def test_invalid_exchange_reports_missing_keys() -> None:
    exchange = normalize_exchange("FMI_FMU", {"time_s": [0.0]}, source_id="invalid-fmi")
    assert exchange.valid is False
    assert exchange.missing_keys == ("variables",)


def test_external_exchange_defaults_to_replay_only() -> None:
    exchange = normalize_exchange(
        "OPCUA",
        normalized_demo_payloads()["OPCUA"],
        source_id="opcua-replay",
    )
    assert exchange.replay_only is True
    assert exchange.live_connection_claim is False
    assert exchange.hardware_validated is False


def test_activation_requires_receipt() -> None:
    result = assess_activation("FMI_FMU", "fmi-a", None)
    assert result.active is False
    assert "missing_execution_receipt" in result.reasons


def test_activation_rejects_failed_receipt() -> None:
    receipt = execute_connector(nonzero_loopback_spec())
    result = assess_activation("REFERENCE_LOOPBACK", receipt.connector_id, receipt)
    assert result.active is False
    assert "execution_not_successful" in result.reasons


def test_activation_accepts_matching_success_receipt_for_that_run() -> None:
    receipt = execute_connector(successful_loopback_spec())
    result = assess_activation("REFERENCE_LOOPBACK", receipt.connector_id, receipt)
    assert result.active is True
    assert result.reasons == ()


def test_activation_rejects_adapter_mismatch() -> None:
    receipt = execute_connector(successful_loopback_spec())
    result = assess_activation("FMI_FMU", receipt.connector_id, receipt)
    assert result.active is False
    assert "adapter_type_mismatch" in result.reasons


def test_ledger_counts_active_failed_and_valid_items() -> None:
    registry = default_adapter_registry()
    capabilities = probe_capabilities(registry)
    success = execute_connector(successful_loopback_spec())
    failure = execute_connector(nonzero_loopback_spec())
    exchanges = tuple(
        normalize_exchange(adapter, payload, source_id=f"ledger-{adapter}")
        for adapter, payload in normalized_demo_payloads().items()
    )
    ledger = IntegrationLedger(
        registry=registry,
        capabilities=capabilities,
        receipts=(success, failure),
        exchanges=exchanges,
        activations=(
            assess_activation("REFERENCE_LOOPBACK", success.connector_id, success),
            assess_activation("REFERENCE_LOOPBACK", failure.connector_id, failure),
        ),
    )
    assert ledger.active_connector_count == 1
    assert ledger.failed_receipt_count == 1
    assert ledger.valid_exchange_count == len(ADAPTER_TYPES)
    assert ledger.physics_certified is False
    assert ledger.hardware_validated is False
    assert ledger.permanent_total_cap is None


def test_r04_oakbench_passes_all_gates() -> None:
    report = run_cps_r04_benchmarks()
    assert report.passed is True
    assert report.status == "CERTIFIED_COMPUTATIONAL_EXTERNAL_ADAPTER_RECEIPTS_R0_4"
    assert len(report.gates) == 13
    assert all(gate.passed for gate in report.gates)
    assert report.live_external_connection_proven is False
    assert report.physics_certified is False
    assert report.hardware_validated is False
    assert report.standards_compliance_claim is False
