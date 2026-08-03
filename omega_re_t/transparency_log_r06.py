"""Small append-only Merkle transparency log for software evidence receipts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def leaf_hash(value: Any) -> str:
    return hashlib.sha256(b"\x00" + _canonical(value)).hexdigest()


def node_hash(left: str, right: str) -> str:
    return hashlib.sha256(b"\x01" + bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()


@dataclass(frozen=True)
class LogEntry:
    sequence: int
    kind: str
    payload_digest: str
    provenance: str


@dataclass(frozen=True)
class InclusionStep:
    sibling_hash: str
    sibling_side: str


@dataclass(frozen=True)
class TransparencyCheckpoint:
    tree_size: int
    root_hash: str
    previous_checkpoint_digest: str
    checkpoint_digest: str
    claim: str = "software_append_only_integrity_only"


def merkle_root(hashes: Iterable[str]) -> str:
    level = tuple(hashes)
    if not level:
        return hashlib.sha256(b"").hexdigest()
    if any(len(item) != 64 for item in level):
        raise ValueError("hashes must be lowercase SHA-256 hex strings")
    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else left
            next_level.append(node_hash(left, right))
        level = tuple(next_level)
    return level[0]


def inclusion_proof(hashes: Iterable[str], index: int) -> tuple[InclusionStep, ...]:
    level = tuple(hashes)
    if not 0 <= index < len(level):
        raise IndexError("leaf index outside tree")
    cursor = index
    proof: list[InclusionStep] = []
    while len(level) > 1:
        if cursor % 2 == 0:
            sibling_index = cursor + 1 if cursor + 1 < len(level) else cursor
            proof.append(InclusionStep(level[sibling_index], "right"))
        else:
            proof.append(InclusionStep(level[cursor - 1], "left"))
        next_level: list[str] = []
        for position in range(0, len(level), 2):
            left = level[position]
            right = level[position + 1] if position + 1 < len(level) else left
            next_level.append(node_hash(left, right))
        level = tuple(next_level)
        cursor //= 2
    return tuple(proof)


def verify_inclusion(leaf: str, proof: Iterable[InclusionStep], expected_root: str) -> bool:
    current = leaf
    try:
        for step in proof:
            if step.sibling_side == "left":
                current = node_hash(step.sibling_hash, current)
            elif step.sibling_side == "right":
                current = node_hash(current, step.sibling_hash)
            else:
                return False
    except ValueError:
        return False
    return current == expected_root


class TransparencyLog:
    def __init__(self) -> None:
        self._entries: list[LogEntry] = []
        self._payloads: list[Mapping[str, Any]] = []
        self._checkpoints: list[TransparencyCheckpoint] = []

    def append(self, *, kind: str, payload: Mapping[str, Any], provenance: str) -> LogEntry:
        if not kind.strip() or not provenance.strip():
            raise ValueError("kind and provenance cannot be blank")
        entry = LogEntry(len(self._entries), kind, "sha256:" + hashlib.sha256(_canonical(payload)).hexdigest(), provenance)
        self._entries.append(entry)
        self._payloads.append(dict(payload))
        return entry

    @property
    def entries(self) -> tuple[LogEntry, ...]:
        return tuple(self._entries)

    def leaf_hashes(self) -> tuple[str, ...]:
        return tuple(leaf_hash(asdict(entry)) for entry in self._entries)

    def checkpoint(self) -> TransparencyCheckpoint:
        root = merkle_root(self.leaf_hashes())
        previous = self._checkpoints[-1].checkpoint_digest if self._checkpoints else "sha256:" + "0" * 64
        unsigned = {"tree_size": len(self._entries), "root_hash": root, "previous_checkpoint_digest": previous}
        digest = "sha256:" + hashlib.sha256(_canonical(unsigned)).hexdigest()
        checkpoint = TransparencyCheckpoint(len(self._entries), root, previous, digest)
        if self._checkpoints and checkpoint.tree_size < self._checkpoints[-1].tree_size:
            raise RuntimeError("tree size cannot decrease")
        self._checkpoints.append(checkpoint)
        return checkpoint

    def prove(self, index: int) -> tuple[LogEntry, tuple[InclusionStep, ...], TransparencyCheckpoint]:
        if not self._checkpoints or self._checkpoints[-1].tree_size != len(self._entries):
            checkpoint = self.checkpoint()
        else:
            checkpoint = self._checkpoints[-1]
        return self._entries[index], inclusion_proof(self.leaf_hashes(), index), checkpoint

    def audit_checkpoints(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []
        previous = "sha256:" + "0" * 64
        previous_size = 0
        for index, checkpoint in enumerate(self._checkpoints):
            if checkpoint.tree_size < previous_size:
                errors.append(f"size:{index}")
            if checkpoint.previous_checkpoint_digest != previous:
                errors.append(f"previous:{index}")
            unsigned = {
                "tree_size": checkpoint.tree_size,
                "root_hash": checkpoint.root_hash,
                "previous_checkpoint_digest": checkpoint.previous_checkpoint_digest,
            }
            expected = "sha256:" + hashlib.sha256(_canonical(unsigned)).hexdigest()
            if checkpoint.checkpoint_digest != expected:
                errors.append(f"digest:{index}")
            previous = checkpoint.checkpoint_digest
            previous_size = checkpoint.tree_size
        return not errors, tuple(errors)
