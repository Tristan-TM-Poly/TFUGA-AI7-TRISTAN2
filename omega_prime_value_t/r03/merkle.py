from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .canonical import canonical_json


def _hash_leaf(payload: Any) -> str:
    encoded = canonical_json(payload).encode("utf-8")
    return hashlib.sha256(b"\x00" + encoded).hexdigest()


def _hash_pair(left: str, right: str) -> str:
    return hashlib.sha256(b"\x01" + bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()


@dataclass(frozen=True, slots=True)
class MerkleStep:
    sibling: str
    side: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MerkleProof:
    leaf_hash: str
    index: int
    leaf_count: int
    steps: tuple[MerkleStep, ...]
    root: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "leaf_hash": self.leaf_hash,
            "index": self.index,
            "leaf_count": self.leaf_count,
            "steps": [step.to_dict() for step in self.steps],
            "root": self.root,
        }


class MerkleTree:
    def __init__(self, leaves: Iterable[Any]):
        payloads = list(leaves)
        if not payloads:
            raise ValueError("Merkle tree requires at least one leaf")
        self._payloads = payloads
        self._levels: list[list[str]] = [[_hash_leaf(payload) for payload in payloads]]
        while len(self._levels[-1]) > 1:
            current = self._levels[-1]
            if len(current) % 2:
                current = current + [current[-1]]
            self._levels.append(
                [_hash_pair(current[index], current[index + 1]) for index in range(0, len(current), 2)]
            )

    @property
    def root(self) -> str:
        return self._levels[-1][0]

    @property
    def leaf_count(self) -> int:
        return len(self._payloads)

    def proof(self, index: int) -> MerkleProof:
        if not 0 <= index < self.leaf_count:
            raise IndexError(index)
        steps: list[MerkleStep] = []
        cursor = index
        for original_level in self._levels[:-1]:
            level = original_level if len(original_level) % 2 == 0 else original_level + [original_level[-1]]
            if cursor % 2 == 0:
                sibling_index = cursor + 1
                side = "right"
            else:
                sibling_index = cursor - 1
                side = "left"
            steps.append(MerkleStep(level[sibling_index], side))
            cursor //= 2
        return MerkleProof(self._levels[0][index], index, self.leaf_count, tuple(steps), self.root)


def verify_merkle_proof(payload: Any, proof: MerkleProof | dict[str, Any]) -> bool:
    raw = proof.to_dict() if isinstance(proof, MerkleProof) else dict(proof)
    current = _hash_leaf(payload)
    if current != raw.get("leaf_hash"):
        return False
    try:
        steps = list(raw["steps"])
        expected_root = str(raw["root"])
    except (KeyError, TypeError):
        return False
    for step in steps:
        sibling = str(step.get("sibling", ""))
        side = step.get("side")
        if len(sibling) != 64 or side not in {"left", "right"}:
            return False
        current = _hash_pair(sibling, current) if side == "left" else _hash_pair(current, sibling)
    return current == expected_root
