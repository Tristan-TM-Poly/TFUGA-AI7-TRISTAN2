"""Opportunity ranking for Ω-ABSORB-POLY-PROF-T v0.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .research_opportunity_compiler import ResearchOpportunityBundle, ResearchOpportunityCompilation


@dataclass(frozen=True)
class RankedOpportunity:
    rank: int
    atom_id: str
    score: float
    value_score: float
    risk_penalty: float
    reproducibility_bonus: float
    recommended_path: str
    next_action: str


@dataclass(frozen=True)
class OpportunityRanking:
    ranked: Tuple[RankedOpportunity, ...]
    top_next_action: str


def score_bundle(bundle: ResearchOpportunityBundle) -> RankedOpportunity:
    course_score = bundle.course_packet.oak.score
    project_score = bundle.project_packet.oak.score
    grant_score = bundle.grant_packet.score
    ip_value = bundle.ip_packet.value_score
    value_score = round((course_score + project_score + grant_score + ip_value) / 4.0, 4)
    risk_penalty = round(
        (
            sum(bundle.course_packet.oak.risks.values())
            + sum(bundle.project_packet.oak.risks.values())
            + sum(bundle.grant_packet.oak.risks.values())
            + sum(bundle.ip_packet.oak.risks.values())
        )
        / max(1, len(bundle.course_packet.oak.risks) + len(bundle.project_packet.oak.risks) + len(bundle.grant_packet.oak.risks) + len(bundle.ip_packet.oak.risks)),
        4,
    )
    reproducibility_bonus = round(
        0.10 * (bundle.course_packet.oak.benefits.get("reproducibility", 0.0))
        + 0.10 * (bundle.ip_packet.oak.benefits.get("reproducibility", 0.0)),
        4,
    )
    final_score = round(max(0.0, min(1.0, value_score - 0.35 * risk_penalty + reproducibility_bonus)), 4)
    if bundle.ip_packet.commercial_value >= 0.65 and bundle.ip_packet.disclosure_risk < 0.55:
        recommended_path = "ip_and_partner_packet"
    elif bundle.project_packet.publication_potential >= 0.55:
        recommended_path = "project_to_publication_packet"
    elif bundle.course_packet.oak.score >= 0.60:
        recommended_path = "course_module_packet"
    else:
        recommended_path = "hold_for_more_evidence"
    return RankedOpportunity(
        rank=0,
        atom_id=bundle.atom_id,
        score=final_score,
        value_score=value_score,
        risk_penalty=risk_penalty,
        reproducibility_bonus=reproducibility_bonus,
        recommended_path=recommended_path,
        next_action="generate_ranked_backlog_item",
    )


def rank_opportunity_bundles(compilation: ResearchOpportunityCompilation | Iterable[ResearchOpportunityBundle]) -> OpportunityRanking:
    bundles = compilation.bundles if isinstance(compilation, ResearchOpportunityCompilation) else tuple(compilation)
    scored = sorted((score_bundle(bundle) for bundle in bundles), key=lambda item: item.score, reverse=True)
    ranked = tuple(
        RankedOpportunity(
            rank=index,
            atom_id=item.atom_id,
            score=item.score,
            value_score=item.value_score,
            risk_penalty=item.risk_penalty,
            reproducibility_bonus=item.reproducibility_bonus,
            recommended_path=item.recommended_path,
            next_action=item.next_action,
        )
        for index, item in enumerate(scored, start=1)
    )
    top_next_action = ranked[0].recommended_path if ranked else "collect_more_public_research_atoms"
    return OpportunityRanking(ranked=ranked, top_next_action=top_next_action)
