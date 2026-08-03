"""Ω-CPS R0.4: execution receipts and external adapter evidence boundaries.

This module deliberately separates four ideas that are often conflated:

1. an adapter is described;
2. a dependency or executable is discoverable;
3. a process was actually executed and produced evidence;
4. a physical, hardware, safety, or standards claim was validated.

Only item 3 can activate an integration for one declared run. Item 4 always remains
false in this software layer unless an external qualified process supplies evidence
outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time
from typing import Any, Iterable, Mapping, Sequence


ADAPTER_TYPES = (
    "FMI_FMU",
    "MODELICA",
    "SPICE",
    "ROS2",
    "CAN",
    "OPCUA",
    "REFERENCE_LOOPBACK",
)

EXTERNAL_ADAPTER_TYPES = ADAPTER_TYPES[:-1]


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class AdapterDescriptor:
    adapter_type: str
    interface_family: str
    candidate_executables: tuple[str, ...] = ()
    candidate_modules: tuple[str, ...] = ()
    hardware_or_runtime_required: bool = False
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.adapter_type not in ADAPTER_TYPES:
            raise ValueError(f"unsupported adapter type: {self.adapter_type}")
        if not self.interface_family:
            raise ValueError("interface_family must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_type": self.adapter_type,
            "interface_family": self.interface_family,
            "candidate_executables": list(self.candidate_executables),
            "candidate_modules": list(self.candidate_modules),
            "hardware_or_runtime_required": self.hardware_or_runtime_required,
            "notes": list(self.notes),
        }


def default_adapter_registry() -> tuple[AdapterDescriptor, ...]:
    return (
        AdapterDescriptor(
            "FMI_FMU",
            "Functional Mock-up Interface / Functional Mock-up Unit",
            candidate_executables=("fmpy",),
            candidate_modules=("fmpy",),
            notes=("availability is not evidence that an FMU was executed",),
        ),
        AdapterDescriptor(
            "MODELICA",
            "Modelica toolchain",
            candidate_executables=("omc",),
            candidate_modules=("OMPython",),
            notes=("a compiler discovery probe is not a compiled or simulated model",),
        ),
        AdapterDescriptor(
            "SPICE",
            "electronic circuit simulation",
            candidate_executables=("ngspice", "xyce"),
            candidate_modules=(),
            notes=("a simulator executable is not a converged circuit analysis",),
        ),
        AdapterDescriptor(
            "ROS2",
            "robot middleware",
            candidate_executables=("ros2",),
            candidate_modules=("rclpy",),
            hardware_or_runtime_required=True,
            notes=("a ROS installation is not evidence of a live graph or hardware",),
        ),
        AdapterDescriptor(
            "CAN",
            "Controller Area Network",
            candidate_executables=("candump", "cansend"),
            candidate_modules=("can",),
            hardware_or_runtime_required=True,
            notes=("SocketCAN tooling is not evidence of a live bus",),
        ),
        AdapterDescriptor(
            "OPCUA",
            "OPC Unified Architecture",
            candidate_executables=("opcua-client",),
            candidate_modules=("asyncua", "opcua"),
            hardware_or_runtime_required=True,
            notes=("client availability is not evidence of a server session",),
        ),
        AdapterDescriptor(
            "REFERENCE_LOOPBACK",
            "local deterministic subprocess reference",
            candidate_executables=(),
            candidate_modules=(),
            notes=("used only to prove the receipt machinery itself",),
        ),
    )


@dataclass(frozen=True)
class CapabilityProbe:
    adapter_type: str
    executable_hits: tuple[str, ...]
    module_hits: tuple[str, ...]
    available: bool
    integration_active: bool = False
    execution_proven: bool = False
    hardware_validated: bool = False
    standards_compliance_claim: bool = False
    limitations: tuple[str, ...] = ()

    @property
    def evidence_hash(self) -> str:
        return _canonical_hash(
            {
                "adapter_type": self.adapter_type,
                "executable_hits": list(self.executable_hits),
                "module_hits": list(self.module_hits),
                "available": self.available,
                "integration_active": self.integration_active,
                "execution_proven": self.execution_proven,
                "hardware_validated": self.hardware_validated,
                "standards_compliance_claim": self.standards_compliance_claim,
                "limitations": list(self.limitations),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_type": self.adapter_type,
            "executable_hits": list(self.executable_hits),
            "module_hits": list(self.module_hits),
            "available": self.available,
            "integration_active": self.integration_active,
            "execution_proven": self.execution_proven,
            "hardware_validated": self.hardware_validated,
            "standards_compliance_claim": self.standards_compliance_claim,
            "limitations": list(self.limitations),
            "evidence_hash": self.evidence_hash,
        }


def probe_capabilities(
    registry: Sequence[AdapterDescriptor] | None = None,
) -> tuple[CapabilityProbe, ...]:
    descriptors = tuple(registry or default_adapter_registry())
    probes: list[CapabilityProbe] = []
    for descriptor in descriptors:
        executable_hits = tuple(
            sorted(
                path
                for executable in descriptor.candidate_executables
                if (path := shutil.which(executable)) is not None
            )
        )
        module_hits = tuple(
            sorted(
                module
                for module in descriptor.candidate_modules
                if importlib.util.find_spec(module) is not None
            )
        )
        available = descriptor.adapter_type == "REFERENCE_LOOPBACK" or bool(executable_hits or module_hits)
        probes.append(
            CapabilityProbe(
                adapter_type=descriptor.adapter_type,
                executable_hits=executable_hits,
                module_hits=module_hits,
                available=available,
                limitations=(
                    "discovery_only",
                    "no_process_execution_implied",
                    "no_hardware_validation_implied",
                    "no_standards_compliance_implied",
                ),
            )
        )
    return tuple(probes)


@dataclass(frozen=True)
class ExecutionSpec:
    connector_id: str
    adapter_type: str
    argv: tuple[str, ...]
    timeout_s: float = 10.0
    cwd: str | None = None
    environment: tuple[tuple[str, str], ...] = ()
    expect_json_stdout: bool = True
    required_json_keys: tuple[str, ...] = ()
    expected_artifacts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.connector_id:
            raise ValueError("connector_id must not be empty")
        if self.adapter_type not in ADAPTER_TYPES:
            raise ValueError(f"unsupported adapter type: {self.adapter_type}")
        if not self.argv or not self.argv[0]:
            raise ValueError("argv must contain an executable")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        for key, _ in self.environment:
            if not key or "=" in key:
                raise ValueError(f"invalid environment key: {key!r}")

    @property
    def spec_hash(self) -> str:
        return _canonical_hash(
            {
                "connector_id": self.connector_id,
                "adapter_type": self.adapter_type,
                "argv": list(self.argv),
                "timeout_s": self.timeout_s,
                "cwd": self.cwd,
                "environment_keys": sorted(key for key, _ in self.environment),
                "expect_json_stdout": self.expect_json_stdout,
                "required_json_keys": list(self.required_json_keys),
                "expected_artifacts": list(self.expected_artifacts),
            }
        )


@dataclass(frozen=True)
class ArtifactReceipt:
    path: str
    exists: bool
    size_bytes: int | None
    sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ExecutionReceipt:
    connector_id: str
    adapter_type: str
    spec_hash: str
    argv: tuple[str, ...]
    status: str
    process_started: bool
    exit_code: int | None
    timed_out: bool
    duration_s: float
    stdout: str
    stderr: str
    output_json: Mapping[str, Any] | None
    output_valid: bool
    missing_required_keys: tuple[str, ...]
    artifacts: tuple[ArtifactReceipt, ...]
    success: bool
    integration_active: bool
    execution_proven_for_this_run: bool
    environment_fingerprint: Mapping[str, str]
    physics_certified: bool = False
    hardware_validated: bool = False
    safety_certified: bool = False
    standards_compliance_claim: bool = False
    permanent_total_cap: None = None
    limitations: tuple[str, ...] = ()

    @property
    def evidence_hash(self) -> str:
        return _canonical_hash(
            {
                "connector_id": self.connector_id,
                "adapter_type": self.adapter_type,
                "spec_hash": self.spec_hash,
                "argv": list(self.argv),
                "status": self.status,
                "process_started": self.process_started,
                "exit_code": self.exit_code,
                "timed_out": self.timed_out,
                "stdout": self.stdout,
                "stderr": self.stderr,
                "output_json": self.output_json,
                "output_valid": self.output_valid,
                "missing_required_keys": list(self.missing_required_keys),
                "artifacts": [item.to_dict() for item in self.artifacts],
                "success": self.success,
                "integration_active": self.integration_active,
                "execution_proven_for_this_run": self.execution_proven_for_this_run,
                "environment_fingerprint": dict(sorted(self.environment_fingerprint.items())),
                "physics_certified": self.physics_certified,
                "hardware_validated": self.hardware_validated,
                "safety_certified": self.safety_certified,
                "standards_compliance_claim": self.standards_compliance_claim,
                "permanent_total_cap": self.permanent_total_cap,
                "limitations": list(self.limitations),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "adapter_type": self.adapter_type,
            "spec_hash": self.spec_hash,
            "argv": list(self.argv),
            "status": self.status,
            "process_started": self.process_started,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "duration_s": self.duration_s,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "output_json": self.output_json,
            "output_valid": self.output_valid,
            "missing_required_keys": list(self.missing_required_keys),
            "artifacts": [item.to_dict() for item in self.artifacts],
            "success": self.success,
            "integration_active": self.integration_active,
            "execution_proven_for_this_run": self.execution_proven_for_this_run,
            "environment_fingerprint": dict(self.environment_fingerprint),
            "physics_certified": self.physics_certified,
            "hardware_validated": self.hardware_validated,
            "safety_certified": self.safety_certified,
            "standards_compliance_claim": self.standards_compliance_claim,
            "permanent_total_cap": self.permanent_total_cap,
            "limitations": list(self.limitations),
            "evidence_hash": self.evidence_hash,
        }


def _artifact_receipts(paths: Iterable[str], cwd: str | None) -> tuple[ArtifactReceipt, ...]:
    root = Path(cwd or os.getcwd())
    receipts: list[ArtifactReceipt] = []
    for value in paths:
        path = Path(value)
        resolved = path if path.is_absolute() else root / path
        if resolved.is_file():
            receipts.append(
                ArtifactReceipt(
                    path=value,
                    exists=True,
                    size_bytes=resolved.stat().st_size,
                    sha256=_sha256_file(resolved),
                )
            )
        else:
            receipts.append(ArtifactReceipt(path=value, exists=False, size_bytes=None, sha256=None))
    return tuple(receipts)


def execute_connector(spec: ExecutionSpec) -> ExecutionReceipt:
    environment = os.environ.copy()
    environment.update(dict(spec.environment))
    fingerprint = {
        "python_version": platform.python_version(),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
    }
    started = time.perf_counter()
    process_started = False
    exit_code: int | None = None
    timed_out = False
    stdout = ""
    stderr = ""
    status = "NOT_STARTED"

    try:
        completed = subprocess.run(
            list(spec.argv),
            cwd=spec.cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=spec.timeout_s,
            check=False,
            shell=False,
        )
        process_started = True
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        status = "PROCESS_EXITED"
    except FileNotFoundError as exc:
        stderr = str(exc)
        status = "EXECUTABLE_NOT_FOUND"
    except subprocess.TimeoutExpired as exc:
        process_started = True
        timed_out = True
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        status = "TIMEOUT"

    duration_s = time.perf_counter() - started
    output_json: Mapping[str, Any] | None = None
    output_valid = not spec.expect_json_stdout
    missing_required_keys: tuple[str, ...] = ()

    if spec.expect_json_stdout and stdout.strip():
        try:
            decoded = json.loads(stdout)
            if isinstance(decoded, Mapping):
                output_json = dict(decoded)
                missing_required_keys = tuple(key for key in spec.required_json_keys if key not in output_json)
                output_valid = not missing_required_keys
            else:
                status = "INVALID_JSON_OBJECT"
        except json.JSONDecodeError:
            status = "INVALID_JSON"
    elif spec.expect_json_stdout:
        status = "MISSING_JSON_OUTPUT" if status == "PROCESS_EXITED" else status

    artifacts = _artifact_receipts(spec.expected_artifacts, spec.cwd)
    artifacts_valid = all(item.exists for item in artifacts)
    success = (
        process_started
        and not timed_out
        and exit_code == 0
        and output_valid
        and artifacts_valid
    )
    if success:
        status = "SUCCESS"
    elif status == "PROCESS_EXITED" and exit_code != 0:
        status = "NONZERO_EXIT"
    elif status == "PROCESS_EXITED" and not artifacts_valid:
        status = "MISSING_ARTIFACT"

    return ExecutionReceipt(
        connector_id=spec.connector_id,
        adapter_type=spec.adapter_type,
        spec_hash=spec.spec_hash,
        argv=spec.argv,
        status=status,
        process_started=process_started,
        exit_code=exit_code,
        timed_out=timed_out,
        duration_s=duration_s,
        stdout=stdout,
        stderr=stderr,
        output_json=output_json,
        output_valid=output_valid,
        missing_required_keys=missing_required_keys,
        artifacts=artifacts,
        success=success,
        integration_active=success,
        execution_proven_for_this_run=success,
        limitations=(
            "receipt_applies_only_to_this_declared_process_run",
            "dependency_discovery_is_not_execution",
            "successful_execution_is_not_physical_validation",
            "successful_execution_is_not_hardware_validation",
            "successful_execution_is_not_standards_compliance",
        ),
        environment_fingerprint=fingerprint,
    )


_NORMALIZED_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "FMI_FMU": ("time_s", "variables"),
    "MODELICA": ("time_s", "variables"),
    "SPICE": ("analysis", "vectors"),
    "ROS2": ("topic", "message_count"),
    "CAN": ("channel", "frames"),
    "OPCUA": ("endpoint_id", "nodes"),
    "REFERENCE_LOOPBACK": ("status", "samples"),
}


@dataclass(frozen=True)
class NormalizedExchange:
    adapter_type: str
    source_id: str
    payload: Mapping[str, Any]
    required_keys: tuple[str, ...]
    valid: bool
    missing_keys: tuple[str, ...]
    source_execution_receipt_hash: str | None = None
    replay_only: bool = True
    live_connection_claim: bool = False
    hardware_validated: bool = False
    standards_compliance_claim: bool = False

    @property
    def evidence_hash(self) -> str:
        return _canonical_hash(
            {
                "adapter_type": self.adapter_type,
                "source_id": self.source_id,
                "payload": self.payload,
                "required_keys": list(self.required_keys),
                "valid": self.valid,
                "missing_keys": list(self.missing_keys),
                "source_execution_receipt_hash": self.source_execution_receipt_hash,
                "replay_only": self.replay_only,
                "live_connection_claim": self.live_connection_claim,
                "hardware_validated": self.hardware_validated,
                "standards_compliance_claim": self.standards_compliance_claim,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_type": self.adapter_type,
            "source_id": self.source_id,
            "payload": self.payload,
            "required_keys": list(self.required_keys),
            "valid": self.valid,
            "missing_keys": list(self.missing_keys),
            "source_execution_receipt_hash": self.source_execution_receipt_hash,
            "replay_only": self.replay_only,
            "live_connection_claim": self.live_connection_claim,
            "hardware_validated": self.hardware_validated,
            "standards_compliance_claim": self.standards_compliance_claim,
            "evidence_hash": self.evidence_hash,
        }


def normalize_exchange(
    adapter_type: str,
    payload: Mapping[str, Any],
    *,
    source_id: str,
    source_execution_receipt_hash: str | None = None,
) -> NormalizedExchange:
    if adapter_type not in ADAPTER_TYPES:
        raise ValueError(f"unsupported adapter type: {adapter_type}")
    if not source_id:
        raise ValueError("source_id must not be empty")
    required = _NORMALIZED_REQUIREMENTS[adapter_type]
    missing = tuple(key for key in required if key not in payload)
    return NormalizedExchange(
        adapter_type=adapter_type,
        source_id=source_id,
        payload=dict(payload),
        required_keys=required,
        valid=not missing,
        missing_keys=missing,
        source_execution_receipt_hash=source_execution_receipt_hash,
        replay_only=source_execution_receipt_hash is None,
    )


@dataclass(frozen=True)
class ActivationAssessment:
    adapter_type: str
    connector_id: str
    active: bool
    reasons: tuple[str, ...]
    receipt_hash: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_type": self.adapter_type,
            "connector_id": self.connector_id,
            "active": self.active,
            "reasons": list(self.reasons),
            "receipt_hash": self.receipt_hash,
        }


def assess_activation(
    adapter_type: str,
    connector_id: str,
    receipt: ExecutionReceipt | None,
) -> ActivationAssessment:
    reasons: list[str] = []
    if receipt is None:
        reasons.append("missing_execution_receipt")
    else:
        if receipt.adapter_type != adapter_type:
            reasons.append("adapter_type_mismatch")
        if receipt.connector_id != connector_id:
            reasons.append("connector_id_mismatch")
        if not receipt.success:
            reasons.append("execution_not_successful")
        if not receipt.execution_proven_for_this_run:
            reasons.append("execution_not_proven")
        if not receipt.output_valid:
            reasons.append("output_contract_invalid")
    active = not reasons
    return ActivationAssessment(
        adapter_type=adapter_type,
        connector_id=connector_id,
        active=active,
        reasons=tuple(reasons),
        receipt_hash=receipt.evidence_hash if receipt is not None else None,
    )


@dataclass(frozen=True)
class IntegrationLedger:
    registry: tuple[AdapterDescriptor, ...]
    capabilities: tuple[CapabilityProbe, ...]
    receipts: tuple[ExecutionReceipt, ...]
    exchanges: tuple[NormalizedExchange, ...]
    activations: tuple[ActivationAssessment, ...]
    permanent_total_cap: None = None
    physics_certified: bool = False
    hardware_validated: bool = False
    safety_certified: bool = False
    standards_compliance_claim: bool = False

    @property
    def active_connector_count(self) -> int:
        return sum(item.active for item in self.activations)

    @property
    def failed_receipt_count(self) -> int:
        return sum(not item.success for item in self.receipts)

    @property
    def valid_exchange_count(self) -> int:
        return sum(item.valid for item in self.exchanges)

    @property
    def evidence_hash(self) -> str:
        return _canonical_hash(
            {
                "registry": [item.to_dict() for item in self.registry],
                "capabilities": [item.to_dict() for item in self.capabilities],
                "receipt_hashes": [item.evidence_hash for item in self.receipts],
                "exchange_hashes": [item.evidence_hash for item in self.exchanges],
                "activations": [item.to_dict() for item in self.activations],
                "permanent_total_cap": self.permanent_total_cap,
                "physics_certified": self.physics_certified,
                "hardware_validated": self.hardware_validated,
                "safety_certified": self.safety_certified,
                "standards_compliance_claim": self.standards_compliance_claim,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry": [item.to_dict() for item in self.registry],
            "capabilities": [item.to_dict() for item in self.capabilities],
            "receipts": [item.to_dict() for item in self.receipts],
            "exchanges": [item.to_dict() for item in self.exchanges],
            "activations": [item.to_dict() for item in self.activations],
            "active_connector_count": self.active_connector_count,
            "failed_receipt_count": self.failed_receipt_count,
            "valid_exchange_count": self.valid_exchange_count,
            "permanent_total_cap": self.permanent_total_cap,
            "physics_certified": self.physics_certified,
            "hardware_validated": self.hardware_validated,
            "safety_certified": self.safety_certified,
            "standards_compliance_claim": self.standards_compliance_claim,
            "evidence_hash": self.evidence_hash,
        }
