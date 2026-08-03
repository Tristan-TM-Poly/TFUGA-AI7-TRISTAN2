from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def digest_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def _pair_hash(left: str, right: str) -> str:
    return hashlib.sha256(bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()


def merkle_root(leaves: Iterable[str]) -> str:
    level = list(leaves)
    if not level:
        return hashlib.sha256(b"").hexdigest()
    for leaf in level:
        if len(leaf) != 64:
            raise ValueError("Merkle leaves must be SHA-256 hex digests")
        bytes.fromhex(leaf)
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [_pair_hash(level[index], level[index + 1]) for index in range(0, len(level), 2)]
    return level[0]


def merkle_proof(leaves: Sequence[str], index: int) -> list[tuple[str, str]]:
    if not 0 <= index < len(leaves):
        raise IndexError("Merkle leaf index out of range")
    level = list(leaves)
    proof: list[tuple[str, str]] = []
    position = index
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        sibling = position - 1 if position % 2 else position + 1
        side = "left" if sibling < position else "right"
        proof.append((side, level[sibling]))
        level = [_pair_hash(level[i], level[i + 1]) for i in range(0, len(level), 2)]
        position //= 2
    return proof


def verify_merkle_proof(leaf: str, proof: Iterable[tuple[str, str]], root: str) -> bool:
    current = leaf
    for side, sibling in proof:
        if side == "left":
            current = _pair_hash(sibling, current)
        elif side == "right":
            current = _pair_hash(current, sibling)
        else:
            raise ValueError(f"invalid Merkle side: {side}")
    return current == root


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class EvidenceManifest:
    manifest_version: str
    entries: tuple[ManifestEntry, ...]
    merkle_root: str
    manifest_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "entries": [asdict(item) for item in self.entries],
            "merkle_root": self.merkle_root,
            "manifest_hash": self.manifest_hash,
        }


def build_manifest(root: str | Path, paths: Iterable[str | Path]) -> EvidenceManifest:
    base = Path(root).resolve()
    entries: list[ManifestEntry] = []
    for candidate in paths:
        path = Path(candidate).resolve()
        try:
            relative = path.relative_to(base).as_posix()
        except ValueError as error:
            raise ValueError(f"manifest path escapes root: {path}") from error
        if not path.is_file():
            raise ValueError(f"manifest path is not a file: {path}")
        entries.append(ManifestEntry(relative, path.stat().st_size, digest_file(path)))
    entries.sort(key=lambda item: item.path)
    leaves = [digest_payload(asdict(item)) for item in entries]
    root_hash = merkle_root(leaves)
    body: Mapping[str, Any] = {
        "manifest_version": "1",
        "entries": [asdict(item) for item in entries],
        "merkle_root": root_hash,
    }
    return EvidenceManifest("1", tuple(entries), root_hash, digest_payload(body))
