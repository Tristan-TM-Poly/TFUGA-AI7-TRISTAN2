from __future__ import annotations

import re
from typing import Iterable

from omega_depth_t.registry import CREATION_ROOTS

from .models import CreationRecord, PullRequestSnapshot


_CANONICAL_REPOSITORY = "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2"
_SPECIAL_TITLE_TOKENS: dict[str, frozenset[str]] = {
    "omega-doc-t": frozenset({"doc", "docs", "document", "documentation"}),
    "oakgate-github-factory": frozenset({"oakgate", "github", "factory", "mycelium"}),
    "omega-space-systems-t": frozenset({"space", "spatial", "satellite", "mission"}),
    "omega-energy-t": frozenset({"energy", "energie", "energetic", "pefa"}),
}


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", value.lower().replace("²", "2").replace("∞", ""))
        if len(token) >= 3
    }


def _related_prs(root_slug: str, root_name: str, pull_requests: Iterable[PullRequestSnapshot]) -> tuple[str, ...]:
    target = _tokens(f"{root_slug} {root_name}")
    special = _SPECIAL_TITLE_TOKENS.get(root_slug, frozenset())
    matches: list[str] = []
    for pull_request in pull_requests:
        lowered = pull_request.title.lower()
        candidate = _tokens(lowered)
        overlap = target.intersection(candidate)
        if root_slug in lowered or len(overlap) >= 2 or special.intersection(candidate):
            matches.append(pull_request.pr_id)
    return tuple(sorted(dict.fromkeys(matches)))


def build_creation_registry(
    pull_requests: Iterable[PullRequestSnapshot] = (),
    *,
    canonical_repository: str = _CANONICAL_REPOSITORY,
) -> tuple[CreationRecord, ...]:
    pull_requests = tuple(pull_requests)
    records: list[CreationRecord] = []
    for root in CREATION_ROOTS:
        canonical_path = f"docs/creations/{root.index:02d}_{root.slug.replace('-', '_')}.md"
        related = _related_prs(root.slug, root.name, pull_requests)
        code_status = "present" if root.status.value in {"coded", "tested", "benchmarked", "measured", "validated"} else "absent"
        test_status = "present" if root.status.value in {"tested", "benchmarked", "measured", "validated"} else "planned"
        records.append(
            CreationRecord(
                creation_id=root.node_id,
                name=root.name,
                category=root.category,
                canonical_repository=canonical_repository,
                canonical_path=canonical_path,
                aliases=(root.slug, root.node_id, root.name),
                implementations=(),
                related_prs=related,
                parents=("tfuga", "hgfm") if root.node_id not in {"hgfm", "log", "cvcd", "exp", "oak"} else (),
                truth_status=root.status.value,
                code_status=code_status,
                test_status=test_status,
                product_status="hypothesis",
                ip_status="review_required",
                metadata={"registry_index": root.index, "depth_root": 0},
            )
        )
    return tuple(records)


def find_creation(records: Iterable[CreationRecord], identifier: str) -> CreationRecord:
    normalized = identifier.lower().replace("-", "_")
    for record in records:
        candidates = {record.creation_id.lower(), *(alias.lower().replace("-", "_") for alias in record.aliases)}
        if normalized in candidates:
            return record
    raise KeyError(f"unknown creation: {identifier}")
