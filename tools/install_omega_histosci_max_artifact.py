#!/usr/bin/env python3
"""Verify and safely extract the Ω-HISTOSCI-HG-T∞ R0.2–R0.3 MAX artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

DEFAULT_ARTIFACT = Path("artifacts/omega-histoscience-r02-r03-max-materialized.tar.gz")
EXPECTED_SHA256 = "4d1a9ae79d33b27a7c24ef429dd302f68899fc711609163edb1d36fac849dae9"
EXPECTED_BYTES = 404_679
EXPECTED_FILE_COUNT = 85


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validated_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    files = [member for member in members if member.isfile()]
    if len(files) != EXPECTED_FILE_COUNT:
        raise RuntimeError(
            f"artifact file-count mismatch: {len(files)} != {EXPECTED_FILE_COUNT}"
        )
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"unsafe archive path: {member.name!r}")
        if member.issym() or member.islnk():
            raise RuntimeError(f"links are forbidden in the artifact: {member.name!r}")
    return members


def verify(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    if size != EXPECTED_BYTES:
        raise RuntimeError(f"artifact size mismatch: {size} != {EXPECTED_BYTES}")
    digest = sha256_file(path)
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"artifact SHA-256 mismatch: {digest}")
    with tarfile.open(path, "r:gz") as archive:
        members = validated_members(archive)
    return {
        "artifact": str(path),
        "sha256": digest,
        "bytes": size,
        "file_count": sum(member.isfile() for member in members),
        "status": "VERIFIED_MAX_ARTIFACT",
        "historical_truth_certified": False,
        "global_exhaustiveness_claimed": False,
        "permanent_total_cap": None,
    }


def extract(path: Path, destination: Path, *, force: bool) -> dict[str, object]:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "r:gz") as archive:
        members = validated_members(archive)
        for member in members:
            relative = Path(*PurePosixPath(member.name).parts)
            target = destination / relative
            if member.isfile() and target.exists() and not force:
                raise FileExistsError(
                    f"refusing to overwrite {target}; pass --force explicitly"
                )
        archive.extractall(destination, members=members, filter="data")
    result = verify(path)
    result.update({"extracted_to": str(destination), "force": force})
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-only", action="store_true")
    action.add_argument("--extract-to", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = verify(args.artifact)
    if args.extract_to is not None:
        report = extract(args.artifact, args.extract_to, force=args.force)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
