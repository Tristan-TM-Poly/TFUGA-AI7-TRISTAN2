from __future__ import annotations

import hashlib
import json

import pytest

from omega_asm_t.cli import main
from omega_asm_t.parallax import artifact_from_descriptor, build_parallax_report


def _artifact(tmp_path, implementation_id: str, language: str, symbol: str):
    source = tmp_path / f"{implementation_id}.src"
    obj = tmp_path / f"{implementation_id}.o"
    dis = tmp_path / f"{implementation_id}.dis"
    source.write_text(f"source:{implementation_id}\n", encoding="utf-8")
    obj.write_bytes(("object:" + implementation_id).encode())
    dis.write_text(f"0000 <{symbol}>:\n  nop\n", encoding="utf-8")
    return {
        "implementation_id": implementation_id,
        "language": language,
        "symbol": symbol,
        "source_path": str(source),
        "object_path": str(obj),
        "disassembly_path": str(dis),
        "toolchain": f"{language}-compiler test",
        "flags": ["-O3", "-fno-lto"],
    }


def test_artifact_hashes_source_object_and_disassembly(tmp_path):
    item = _artifact(tmp_path, "c", "c", "omega_c")
    artifact = artifact_from_descriptor(item)
    assert artifact.source_sha256 == hashlib.sha256(b"source:c\n").hexdigest()
    assert artifact.object_sha256 == hashlib.sha256(b"object:c").hexdigest()
    assert len(artifact.disassembly_sha256) == 64
    assert artifact.object_size_bytes == len(b"object:c")


def test_missing_artifact_file_is_rejected(tmp_path):
    item = _artifact(tmp_path, "c", "c", "omega_c")
    item["object_path"] = str(tmp_path / "missing.o")
    with pytest.raises(ValueError, match="does not exist"):
        artifact_from_descriptor(item)


def test_parallax_report_requires_unique_implementation_ids(tmp_path):
    first = _artifact(tmp_path, "one", "c", "omega_one")
    second = _artifact(tmp_path, "two", "cpp", "omega_two")
    second["implementation_id"] = "one"
    with pytest.raises(ValueError, match="implementation_id"):
        build_parallax_report({
            "semantic_contract": "dot_u64_mod_2^64",
            "build_context": {},
            "artifacts": [first, second],
        })


def test_parallax_report_requires_unique_symbols(tmp_path):
    first = _artifact(tmp_path, "one", "c", "same_symbol")
    second = _artifact(tmp_path, "two", "cpp", "same_symbol")
    with pytest.raises(ValueError, match="symbols"):
        build_parallax_report({
            "semantic_contract": "dot_u64_mod_2^64",
            "build_context": {},
            "artifacts": [first, second],
        })


def test_parallax_report_is_review_only_and_non_promoting(tmp_path):
    report = build_parallax_report({
        "semantic_contract": "dot_u64_mod_2^64",
        "build_context": {"architecture": "x86_64", "separate_translation_units": True},
        "artifacts": [
            _artifact(tmp_path, "c", "c", "omega_c"),
            _artifact(tmp_path, "rust", "rust", "omega_rust"),
        ],
    })
    assert report["evidence_level"] == "compiler-parallax-artifact-ledger"
    assert report["authority"] == "review_only"
    assert report["implementation_count"] == 2
    assert report["languages"] == ["c", "rust"]
    contract = report["comparison_contract"]
    assert contract["separate_translation_units_required"] is True
    assert contract["lto_forbidden_in_reference_court"] is True
    assert contract["native_differential_correctness_required"] is True
    assert contract["performance_threshold_required"] is False
    assert contract["universal_language_claim_allowed"] is False


def test_cli_parallax_report(tmp_path, capsys):
    descriptor = {
        "semantic_contract": "dot_u64_mod_2^64",
        "build_context": {"architecture": "x86_64"},
        "artifacts": [
            _artifact(tmp_path, "c", "c", "omega_c"),
            _artifact(tmp_path, "cpp", "cpp", "omega_cpp"),
        ],
    }
    path = tmp_path / "descriptor.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")
    assert main(["parallax-report", str(path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["semantic_contract"] == "dot_u64_mod_2^64"
    assert len(payload["artifacts"]) == 2
    assert all(len(row["object_sha256"]) == 64 for row in payload["artifacts"])
