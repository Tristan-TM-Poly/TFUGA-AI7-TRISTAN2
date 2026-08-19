from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

_ALLOWED_FORMATS = {"primo", "ecpp", "pocklington-external", "generic-primality-certificate"}


@dataclass(frozen=True, slots=True)
class ExternalArtifactReceipt:
    format: str
    source_label: str
    size_bytes: int
    sha256: str
    status: str
    oak: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExternalVerifierReceipt:
    artifact: dict[str, Any]
    executable: str
    executable_sha256: str
    arguments: tuple[str, ...]
    returncode: int
    stdout_sha256: str
    stderr_sha256: str
    output_marker: str
    marker_matched: bool
    verified_by_declared_tool: bool
    oak: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["arguments"] = list(self.arguments)
        return payload


def import_external_artifact(data: bytes, *, format: str, source_label: str) -> ExternalArtifactReceipt:
    normalized = format.strip().lower()
    if normalized not in _ALLOWED_FORMATS:
        raise ValueError(f"unsupported external certificate format: {format}")
    if not source_label.strip():
        raise ValueError("source_label is required")
    digest = hashlib.sha256(data).hexdigest()
    return ExternalArtifactReceipt(
        format=normalized,
        source_label=source_label,
        size_bytes=len(data),
        sha256=digest,
        status="IMPORTED_UNVERIFIED_EXTERNAL_ARTIFACT_R0_4",
        oak={
            "artifact_import_is_not_proof_verification": True,
            "external_tool_trust_required": True,
            "institutional_independence_claimed": False,
            "novelty_claimed": False,
        },
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_with_external_command(
    data: bytes,
    artifact_receipt: ExternalArtifactReceipt,
    *,
    executable: str | os.PathLike[str],
    arguments: Iterable[str] = ("{artifact}",),
    output_marker: str = "PRIME",
    timeout_seconds: float = 30.0,
) -> ExternalVerifierReceipt:
    executable_path = Path(executable).resolve()
    if not executable_path.is_absolute() or not executable_path.is_file():
        raise ValueError("verifier executable must be an existing absolute file")
    if timeout_seconds <= 0 or timeout_seconds > 300:
        raise ValueError("timeout_seconds must be in (0, 300]")
    if hashlib.sha256(data).hexdigest() != artifact_receipt.sha256:
        raise ValueError("artifact bytes do not match import receipt")
    argument_templates = tuple(str(value) for value in arguments)
    if not any("{artifact}" in value for value in argument_templates):
        raise ValueError("arguments must include an {artifact} placeholder")
    with tempfile.TemporaryDirectory(prefix="omega-prime-external-") as directory:
        artifact_path = Path(directory) / "certificate.bin"
        artifact_path.write_bytes(data)
        expanded = tuple(value.replace("{artifact}", str(artifact_path)) for value in argument_templates)
        completed = subprocess.run(
            [str(executable_path), *expanded],
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
    stdout = completed.stdout
    stderr = completed.stderr
    marker_matched = output_marker.encode("utf-8") in stdout
    verified = completed.returncode == 0 and marker_matched
    return ExternalVerifierReceipt(
        artifact=artifact_receipt.to_dict(),
        executable=str(executable_path),
        executable_sha256=_file_sha256(executable_path),
        arguments=argument_templates,
        returncode=completed.returncode,
        stdout_sha256=hashlib.sha256(stdout).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr).hexdigest(),
        output_marker=output_marker,
        marker_matched=marker_matched,
        verified_by_declared_tool=verified,
        oak={
            "tool_execution_is_not_institutional_independence": True,
            "tool_semantics_are_external_to_this_repository": True,
            "shell_invocation_used": False,
            "artifact_hash_bound": True,
            "global_novelty_claimed": False,
        },
    )
