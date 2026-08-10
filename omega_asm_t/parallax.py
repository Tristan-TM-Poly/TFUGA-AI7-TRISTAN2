from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
from typing import Iterable


@dataclass(frozen=True)
class ParallaxArtifact:
    implementation_id: str
    language: str
    symbol: str
    source_path: str
    source_sha256: str
    object_path: str
    object_sha256: str
    object_size_bytes: int
    disassembly_path: str
    disassembly_sha256: str
    toolchain: str
    flags: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["flags"] = list(self.flags)
        return data


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_text(item: dict[str, object], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"artifact {key} must be a non-empty string")
    return value.strip()


def artifact_from_descriptor(item: object) -> ParallaxArtifact:
    if not isinstance(item, dict):
        raise ValueError("artifact descriptor must be an object")
    implementation_id = _required_text(item, "implementation_id")
    language = _required_text(item, "language")
    symbol = _required_text(item, "symbol")
    source_path = _required_text(item, "source_path")
    object_path = _required_text(item, "object_path")
    disassembly_path = _required_text(item, "disassembly_path")
    toolchain = _required_text(item, "toolchain")
    flags_raw = item.get("flags", [])
    if not isinstance(flags_raw, list) or not all(isinstance(flag, str) for flag in flags_raw):
        raise ValueError("artifact flags must be a list of strings")

    source = Path(source_path)
    obj = Path(object_path)
    disassembly = Path(disassembly_path)
    for label, path in (("source", source), ("object", obj), ("disassembly", disassembly)):
        if not path.is_file():
            raise ValueError(f"artifact {implementation_id}: {label} file does not exist: {path}")

    return ParallaxArtifact(
        implementation_id=implementation_id,
        language=language,
        symbol=symbol,
        source_path=str(source),
        source_sha256=_sha256(source),
        object_path=str(obj),
        object_sha256=_sha256(obj),
        object_size_bytes=obj.stat().st_size,
        disassembly_path=str(disassembly),
        disassembly_sha256=_sha256(disassembly),
        toolchain=toolchain,
        flags=tuple(flags_raw),
    )


def build_parallax_report(descriptor: object) -> dict[str, object]:
    if not isinstance(descriptor, dict):
        raise ValueError("parallax descriptor must be a JSON object")
    semantic_contract = descriptor.get("semantic_contract")
    if not isinstance(semantic_contract, str) or not semantic_contract.strip():
        raise ValueError("semantic_contract must be a non-empty string")
    build_context = descriptor.get("build_context")
    if not isinstance(build_context, dict):
        raise ValueError("build_context must be an object")
    artifacts_raw = descriptor.get("artifacts")
    if not isinstance(artifacts_raw, list) or len(artifacts_raw) < 2:
        raise ValueError("parallax descriptor requires at least two artifacts")

    artifacts = [artifact_from_descriptor(item) for item in artifacts_raw]
    ids = [artifact.implementation_id for artifact in artifacts]
    if len(ids) != len(set(ids)):
        raise ValueError("implementation_id values must be unique")
    symbols = [artifact.symbol for artifact in artifacts]
    if len(symbols) != len(set(symbols)):
        raise ValueError("symbols must be unique across parallax implementations")

    languages = sorted({artifact.language for artifact in artifacts})
    return {
        "schema_version": 1,
        "evidence_level": "compiler-parallax-artifact-ledger",
        "semantic_contract": semantic_contract.strip(),
        "claim_scope": "one_build_context_only",
        "authority": "review_only",
        "warning": (
            "artifact and disassembly diversity is descriptive provenance; it does not establish language superiority"
        ),
        "build_context": dict(build_context),
        "implementation_count": len(artifacts),
        "languages": languages,
        "artifacts": [artifact.to_dict() for artifact in sorted(artifacts, key=lambda row: row.implementation_id)],
        "comparison_contract": {
            "separate_translation_units_required": True,
            "lto_forbidden_in_reference_court": True,
            "native_differential_correctness_required": True,
            "performance_threshold_required": False,
            "source_object_disassembly_hashes_required": True,
            "universal_language_claim_allowed": False,
            "automatic_authority_promotion": False,
        },
    }
