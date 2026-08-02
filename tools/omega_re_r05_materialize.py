"""Fail-closed materializer for Ω-RE-T∞ R0.5.

The transport is a deterministic tar.gz archive encoded as short base64
fragments. Every layer is content-addressed before any repository file is
written. Materialization proves byte identity only; it does not establish
external execution, scientific validity, or authorization beyond this repo.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIR = ROOT / "tools" / "omega_re_r05_payload"
MANIFEST_PATH = PAYLOAD_DIR / "manifest.json"
MANIFEST_SHA256 = "21a2f851ee6cf3807cd535bae27e45eaa728fa74f408e08775e24ec87d8abf6e"
PYPROJECT = ROOT / "pyproject.toml"
CLI_ANCHOR = 'omega-re-r04 = "omega_re_t.r04_cli:main"'
CLI_ENTRY = 'omega-re-r05 = "omega_re_t.r05_cli:main"'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def load_manifest() -> dict[str, Any]:
    raw = MANIFEST_PATH.read_bytes()
    if sha256_bytes(raw) != MANIFEST_SHA256:
        fail("manifest_sha256_mismatch")
    manifest = json.loads(raw)
    required = {
        "archive_bytes",
        "archive_sha256",
        "chunks",
        "encoded_chars",
        "encoded_sha256",
        "file_hashes",
        "paths",
    }
    if set(manifest) != required:
        fail("manifest_key_set_mismatch")
    if manifest["paths"] != sorted(manifest["paths"]):
        fail("manifest_paths_not_sorted")
    if set(manifest["paths"]) != set(manifest["file_hashes"]):
        fail("manifest_path_hash_set_mismatch")
    return manifest


def verify_transport(manifest: dict[str, Any]) -> bytes:
    expected_names = [chunk["name"] for chunk in manifest["chunks"]]
    if expected_names != sorted(expected_names):
        fail("chunk_names_not_sorted")
    actual_names = sorted(path.name for path in PAYLOAD_DIR.iterdir() if path.is_file())
    if actual_names != sorted(["manifest.json", *expected_names]):
        fail("payload_file_set_mismatch")

    encoded_parts: list[str] = []
    for chunk in manifest["chunks"]:
        path = PAYLOAD_DIR / chunk["name"]
        data = path.read_bytes()
        if len(data) != chunk["chars"]:
            fail(f"chunk_length_mismatch:{chunk['name']}")
        if sha256_bytes(data) != chunk["sha256"]:
            fail(f"chunk_sha256_mismatch:{chunk['name']}")
        try:
            encoded_parts.append(data.decode("ascii"))
        except UnicodeDecodeError:
            fail(f"chunk_not_ascii:{chunk['name']}")

    encoded = "".join(encoded_parts)
    encoded_bytes = encoded.encode("ascii")
    if len(encoded) != manifest["encoded_chars"]:
        fail("encoded_length_mismatch")
    if sha256_bytes(encoded_bytes) != manifest["encoded_sha256"]:
        fail("encoded_sha256_mismatch")
    try:
        archive = base64.b64decode(encoded_bytes, validate=True)
    except Exception as exc:  # pragma: no cover
        fail(f"base64_decode_failed:{type(exc).__name__}")
    if len(archive) != manifest["archive_bytes"]:
        fail("archive_length_mismatch")
    if sha256_bytes(archive) != manifest["archive_sha256"]:
        fail("archive_sha256_mismatch")
    return archive


def validate_member_name(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
        fail(f"unsafe_archive_path:{name}")
    if path.as_posix() != name:
        fail(f"noncanonical_archive_path:{name}")


def read_archive_files(archive: bytes, manifest: dict[str, Any]) -> dict[str, bytes]:
    expected = set(manifest["paths"])
    extracted: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        members = tar.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            fail("duplicate_archive_member")
        if set(names) != expected:
            fail("archive_member_set_mismatch")
        for member in members:
            validate_member_name(member.name)
            if not member.isfile() or member.issym() or member.islnk():
                fail(f"non_regular_archive_member:{member.name}")
            stream = tar.extractfile(member)
            if stream is None:
                fail(f"archive_member_unreadable:{member.name}")
            data = stream.read()
            if len(data) != member.size:
                fail(f"archive_member_size_mismatch:{member.name}")
            expected_hash = manifest["file_hashes"][member.name]
            if sha256_bytes(data) != expected_hash:
                fail(f"archive_member_sha256_mismatch:{member.name}")
            extracted[member.name] = data
    return extracted


def patch_pyproject(*, write: bool) -> None:
    original = PYPROJECT.read_text(encoding="utf-8")
    if original.count(CLI_ANCHOR) != 1:
        fail("pyproject_anchor_count_mismatch")
    if CLI_ENTRY in original:
        if original.count(CLI_ENTRY) != 1:
            fail("pyproject_cli_entry_count_mismatch")
        return
    updated = original.replace(CLI_ANCHOR, f"{CLI_ANCHOR}\n{CLI_ENTRY}", 1)
    if write:
        PYPROJECT.write_text(updated, encoding="utf-8")


def materialize(files: dict[str, bytes]) -> None:
    for relative, data in sorted(files.items()):
        target = ROOT / relative
        if target.exists():
            if not target.is_file():
                fail(f"target_not_regular_file:{relative}")
            if target.read_bytes() != data:
                fail(f"refuse_divergent_overwrite:{relative}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    patch_pyproject(write=True)


def require_extracted(manifest: dict[str, Any]) -> None:
    for relative in manifest["paths"]:
        target = ROOT / relative
        if not target.is_file():
            fail(f"missing_extracted_file:{relative}")
        if sha256_bytes(target.read_bytes()) != manifest["file_hashes"][relative]:
            fail(f"extracted_file_sha256_mismatch:{relative}")
    patch_pyproject(write=False)
    if CLI_ENTRY not in PYPROJECT.read_text(encoding="utf-8"):
        fail("pyproject_cli_entry_missing")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--require-extracted", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest()
    archive = verify_transport(manifest)
    files = read_archive_files(archive, manifest)
    if args.extract:
        materialize(files)
    if args.require_extracted:
        require_extracted(manifest)
    print(json.dumps({
        "archive_sha256": manifest["archive_sha256"],
        "chunks_verified": len(manifest["chunks"]),
        "files_verified": len(files),
        "extracted": args.extract,
        "required_extracted": args.require_extracted,
        "claim": "byte_identity_only",
        "external_execution_claimed": False,
        "scientific_validation_claimed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
