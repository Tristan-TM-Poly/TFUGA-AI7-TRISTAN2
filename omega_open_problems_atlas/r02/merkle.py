"""Small dependency-free Merkle utilities for evidence manifests."""
from __future__ import annotations

from hashlib import sha256
from typing import Iterable


def digest_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def digest_text(payload: str) -> str:
    return digest_bytes(payload.encode("utf-8"))


def _pair_hash(left: str, right: str) -> str:
    return digest_text(f"{left}:{right}")


def merkle_root(leaves: Iterable[str]) -> str:
    level = list(leaves)
    if not level:
        return digest_text("")
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [_pair_hash(level[i], level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def inclusion_proof(leaves: list[str], index: int) -> tuple[tuple[str, str], ...]:
    if index < 0 or index >= len(leaves):
        raise IndexError(index)
    proof: list[tuple[str, str]] = []
    level = list(leaves)
    cursor = index
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        sibling = cursor - 1 if cursor % 2 else cursor + 1
        side = "left" if sibling < cursor else "right"
        proof.append((side, level[sibling]))
        cursor //= 2
        level = [_pair_hash(level[i], level[i + 1]) for i in range(0, len(level), 2)]
    return tuple(proof)


def verify_inclusion(leaf: str, proof: Iterable[tuple[str, str]], root: str) -> bool:
    current = leaf
    for side, sibling in proof:
        if side == "left":
            current = _pair_hash(sibling, current)
        elif side == "right":
            current = _pair_hash(current, sibling)
        else:
            return False
    return current == root
