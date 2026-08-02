"""Contradiction and semantic-collision detection for R0.3 knowledge cells."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .knowledge_cell import ClaimAtom, KnowledgeCell, normalize_key, stable_id


@dataclass(frozen=True)
class ClaimCollision:
    collision_id: str
    kind: str
    canonical_key: str
    claim_ids: tuple[str, ...]
    cell_ids: tuple[str, ...]
    scopes: tuple[str, ...]
    status: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _scope_overlaps(left: str, right: str) -> bool:
    a = normalize_key(left)
    b = normalize_key(right)
    return a == b or "unspecified" in {a, b} or a in b or b in a


def detect_claim_collisions(cells: Sequence[KnowledgeCell]) -> list[ClaimCollision]:
    grouped: dict[str, list[tuple[str, ClaimAtom]]] = {}
    for cell in cells:
        for claim in cell.claims:
            grouped.setdefault(normalize_key(claim.canonical_key), []).append((cell.cell_id, claim))

    collisions: list[ClaimCollision] = []
    for key, members in sorted(grouped.items()):
        if len(members) < 2:
            continue

        for index, (left_cell, left) in enumerate(members):
            for right_cell, right in members[index + 1 :]:
                scopes = tuple(sorted({left.scope, right.scope}))
                ids = tuple(sorted({left.claim_id, right.claim_id}))
                cells_ids = tuple(sorted({left_cell, right_cell}))

                if left.polarity != right.polarity and _scope_overlaps(left.scope, right.scope):
                    collisions.append(
                        ClaimCollision(
                            collision_id=stable_id("collision", "contradiction", key, *ids),
                            kind="potential_contradiction",
                            canonical_key=key,
                            claim_ids=ids,
                            cell_ids=cells_ids,
                            scopes=scopes,
                            status="requires_protocol_and_scope_review",
                            explanation=(
                                "Claims share a canonical proposition and overlapping scope but have opposing polarity. "
                                "This is a contradiction candidate, not an automatic logical refutation."
                            ),
                        )
                    )
                elif left.polarity == right.polarity and normalize_key(left.text) == normalize_key(right.text):
                    collisions.append(
                        ClaimCollision(
                            collision_id=stable_id("collision", "duplicate", key, *ids),
                            kind="probable_duplicate",
                            canonical_key=key,
                            claim_ids=ids,
                            cell_ids=cells_ids,
                            scopes=scopes,
                            status="requires_alias_or_merge_decision",
                            explanation="Claims have equivalent normalized text and polarity.",
                        )
                    )
                elif left.polarity != right.polarity:
                    collisions.append(
                        ClaimCollision(
                            collision_id=stable_id("collision", "scope", key, *ids),
                            kind="scope_tension",
                            canonical_key=key,
                            claim_ids=ids,
                            cell_ids=cells_ids,
                            scopes=scopes,
                            status="possibly_context_dependent",
                            explanation=(
                                "Claims oppose one another but their scopes do not clearly overlap. "
                                "The apparent conflict may encode context dependence."
                            ),
                        )
                    )

    unique = {item.collision_id: item for item in collisions}
    return sorted(unique.values(), key=lambda item: (item.kind, item.canonical_key, item.collision_id))
