"""Deterministic exact and near-duplicate detection for problem leads."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re
from typing import Iterable

from .models import ProblemLead

_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


@dataclass(frozen=True)
class DuplicateFinding:
    left_id: str
    right_id: str
    relation: str
    similarity: float
    reason: str


def normalize_text(text: str) -> str:
    return " ".join(_TOKEN.findall(text.casefold()))


def token_set(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall(text.casefold()))


def jaccard(left: str, right: str) -> float:
    a, b = token_set(left), token_set(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def exact_duplicate_groups(leads: Iterable[ProblemLead]) -> tuple[tuple[str, ...], ...]:
    groups: dict[str, list[str]] = defaultdict(list)
    for lead in leads:
        groups[lead.statement_hash()].append(lead.lead_id)
    return tuple(
        tuple(sorted(ids))
        for _, ids in sorted(groups.items())
        if len(ids) > 1
    )


def near_duplicate_findings(
    leads: Iterable[ProblemLead],
    threshold: float = 0.82,
    max_bucket_size: int = 200,
) -> tuple[DuplicateFinding, ...]:
    """Find likely duplicates using conservative lexical buckets.

    This is a review heuristic, not a mathematical-equivalence detector. Leads
    are bucketed by source-independent domain and leading normalized token to
    avoid a quadratic all-pairs pass across the entire atlas.
    """
    materialized = tuple(leads)
    buckets: dict[tuple[str, str], list[ProblemLead]] = defaultdict(list)
    for lead in materialized:
        normalized = normalize_text(f"{lead.title} {lead.statement_summary}")
        head = normalized.split(" ", 1)[0] if normalized else ""
        domains = lead.domains or ("unknown",)
        for domain in domains:
            buckets[(domain, head)].append(lead)

    findings: dict[tuple[str, str], DuplicateFinding] = {}
    for key in sorted(buckets):
        bucket = sorted(buckets[key], key=lambda item: item.lead_id)[:max_bucket_size]
        for index, left in enumerate(bucket):
            for right in bucket[index + 1 :]:
                if left.lead_id == right.lead_id:
                    continue
                similarity = jaccard(
                    f"{left.title} {left.statement_summary}",
                    f"{right.title} {right.statement_summary}",
                )
                if similarity < threshold:
                    continue
                pair = tuple(sorted((left.lead_id, right.lead_id)))
                relation = (
                    "EXACT_STATEMENT_DUPLICATE"
                    if left.statement_hash() == right.statement_hash()
                    else "LIKELY_LEXICAL_DUPLICATE"
                )
                findings[pair] = DuplicateFinding(
                    left_id=pair[0],
                    right_id=pair[1],
                    relation=relation,
                    similarity=round(similarity, 6),
                    reason=f"shared bucket {key[0]}::{key[1]}",
                )
    return tuple(findings[key] for key in sorted(findings))
