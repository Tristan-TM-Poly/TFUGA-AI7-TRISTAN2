"""PriorArtPacket generator for IP-OAK triage.

This is not a legal opinion. It builds a structured search/triage packet from
public metadata and keywords so the system can preserve zero-touch flow without
claiming legal authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .research_atom import ResearchAtom


@dataclass(frozen=True)
class PriorArtPacket:
    result_name: str
    novelty_axes: Tuple[str, ...]
    search_queries: Tuple[str, ...]
    closest_public_references: Tuple[str, ...]
    disclosure_risk_notes: Tuple[str, ...]
    next_action: str


def generate_prior_art_packet(
    result_name: str,
    keywords: Iterable[str],
    atoms: Iterable[ResearchAtom] = (),
) -> PriorArtPacket:
    keywords_tuple = tuple(str(keyword).strip() for keyword in keywords if str(keyword).strip())
    novelty_axes = tuple(f"novelty_axis:{keyword}" for keyword in keywords_tuple[:8]) or ("novelty_axis:undefined",)
    search_queries = tuple(
        f"{result_name} {keyword} patent publication prior art" for keyword in keywords_tuple[:8]
    ) or (f"{result_name} patent publication prior art",)
    references = tuple(
        f"{atom.title} | {atom.link or atom.source}" for atom in atoms if atom.title
    )
    disclosure_risk_notes = (
        "Do not disclose implementation details before IP-OAK classification.",
        "Separate public metadata from confidential invention details.",
        "Use this packet as search planning, not legal advice.",
    )
    return PriorArtPacket(
        result_name=result_name,
        novelty_axes=novelty_axes,
        search_queries=search_queries,
        closest_public_references=references,
        disclosure_risk_notes=disclosure_risk_notes,
        next_action="run_public_prior_art_search_and_update_ip_oak_gate",
    )
