"""Deterministic R0.4 fixtures for adapter receipts and normalized exchanges."""

from __future__ import annotations

import json
import sys
from typing import Any

from .integration import ExecutionSpec


def successful_loopback_spec() -> ExecutionSpec:
    payload = {
        "status": "ok",
        "samples": 3,
        "values": [1.0, 2.0, 3.0],
        "source": "reference-loopback",
    }
    return ExecutionSpec(
        connector_id="reference-loopback-success",
        adapter_type="REFERENCE_LOOPBACK",
        argv=(
            sys.executable,
            "-c",
            f"import json; print(json.dumps({payload!r}, sort_keys=True))",
        ),
        timeout_s=5.0,
        required_json_keys=("status", "samples", "values"),
    )


def nonzero_loopback_spec() -> ExecutionSpec:
    return ExecutionSpec(
        connector_id="reference-loopback-nonzero",
        adapter_type="REFERENCE_LOOPBACK",
        argv=(
            sys.executable,
            "-c",
            "import json,sys; print(json.dumps({'status':'failed','samples':0}, sort_keys=True)); sys.exit(7)",
        ),
        timeout_s=5.0,
        required_json_keys=("status", "samples"),
    )


def invalid_json_loopback_spec() -> ExecutionSpec:
    return ExecutionSpec(
        connector_id="reference-loopback-invalid-json",
        adapter_type="REFERENCE_LOOPBACK",
        argv=(sys.executable, "-c", "print('not-json')"),
        timeout_s=5.0,
        required_json_keys=("status",),
    )


def timeout_loopback_spec() -> ExecutionSpec:
    return ExecutionSpec(
        connector_id="reference-loopback-timeout",
        adapter_type="REFERENCE_LOOPBACK",
        argv=(sys.executable, "-c", "import time; time.sleep(0.25); print('{}')"),
        timeout_s=0.01,
    )


def missing_executable_spec() -> ExecutionSpec:
    return ExecutionSpec(
        connector_id="reference-loopback-missing-executable",
        adapter_type="REFERENCE_LOOPBACK",
        argv=("omega-cps-r04-definitely-missing-executable",),
        timeout_s=1.0,
    )


def normalized_demo_payloads() -> dict[str, dict[str, Any]]:
    return {
        "FMI_FMU": {
            "time_s": [0.0, 0.1, 0.2],
            "variables": {"shaft_speed_rad_s": [0.0, 2.0, 3.5]},
            "fmi_version": "declared-fixture-2.0",
        },
        "MODELICA": {
            "time_s": [0.0, 0.1, 0.2],
            "variables": {"temperature_k": [293.15, 293.2, 293.3]},
            "tool": "declared-fixture",
        },
        "SPICE": {
            "analysis": "transient",
            "vectors": {"time_s": [0.0, 1e-3], "voltage_v": [0.0, 4.9]},
            "converged_claim": False,
        },
        "ROS2": {
            "topic": "/fixture/joint_state",
            "message_count": 4,
            "start_ns": 0,
            "end_ns": 3000000,
            "live_graph_claim": False,
        },
        "CAN": {
            "channel": "fixture-can0",
            "frames": [
                {"timestamp_s": 0.0, "arbitration_id": 256, "data_hex": "01020304"},
                {"timestamp_s": 0.01, "arbitration_id": 257, "data_hex": "A0B0"},
            ],
            "live_bus_claim": False,
        },
        "OPCUA": {
            "endpoint_id": "fixture-redacted-endpoint",
            "nodes": [
                {"node_id": "ns=2;s=Axis.Position", "value": 0.125, "unit": "m"},
                {"node_id": "ns=2;s=Axis.Ready", "value": True, "unit": "1"},
            ],
            "live_session_claim": False,
        },
        "REFERENCE_LOOPBACK": {
            "status": "ok",
            "samples": 3,
            "values": [1, 2, 3],
        },
    }


def payload_json(adapter_type: str) -> str:
    payloads = normalized_demo_payloads()
    if adapter_type not in payloads:
        raise ValueError(f"unsupported adapter fixture: {adapter_type}")
    return json.dumps(payloads[adapter_type], sort_keys=True)
