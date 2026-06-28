"""GrantForge-OAK for Omega-PROF-POLY-T."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .zero_touch_oak import OAKCompileResult, compile_oak


@dataclass(frozen=True)
class GrantInput:
    title: str
    problem: str
    objectives: Tuple[str, ...]
    methods: Tuple[str, ...]
    team_strength: float = 0.5
    impact: float = 0.5
    novelty: float = 0.5
    feasibility: float = 0.5
    reproducibility: float = 0.5


@dataclass(frozen=True)
class GrantPacket:
    title: str
    public_summary: str
    scientific_summary: str
    workpackages: Tuple[str, ...]
    risk_plan: Tuple[str, ...]
    score: float
    oak: OAKCompileResult
    next_action: str


def grant_score(grant: GrantInput, risk: float) -> float:
    score = (
        0.25 * grant.feasibility
        + 0.20 * grant.impact
        + 0.20 * grant.novelty
        + 0.15 * grant.team_strength
        + 0.10 * min(1.0, len(grant.methods) / 4.0)
        + 0.10 * grant.reproducibility
        - risk
    )
    return round(max(0.0, min(1.0, score)), 4)


def forge_grant(grant: GrantInput, evidence_count: int = 1) -> GrantPacket:
    risk = 0.18 + 0.05 * max(0, 3 - len(grant.objectives))
    score = grant_score(grant, risk)
    public_summary = f"This project addresses {grant.problem} through {grant.title}."
    scientific_summary = (
        f"{grant.title} proposes {len(grant.objectives)} objectives and "
        f"{len(grant.methods)} method families with reproducibility score "
        f"{grant.reproducibility:.2f}."
    )
    workpackages = tuple(f"WP{idx}: {objective}" for idx, objective in enumerate(grant.objectives, start=1))
    risk_plan = (
        "scope_control",
        "fallback_method",
        "reproducibility_package",
        "evidence_ledger",
    )
    benefits: Dict[str, float] = {
        "feasibility": grant.feasibility,
        "impact": grant.impact,
        "novelty": grant.novelty,
        "team": grant.team_strength,
        "reproducibility": grant.reproducibility,
        "automation": 0.78,
    }
    risks: Dict[str, float] = {
        "overclaim": risk,
        "complexity": min(0.75, 0.12 * len(grant.objectives)),
        "confidentiality": 0.15,
    }
    oak = compile_oak(grant.title, benefits, risks, evidence_count=evidence_count, external_action=True)
    return GrantPacket(
        title=grant.title,
        public_summary=public_summary,
        scientific_summary=scientific_summary,
        workpackages=workpackages,
        risk_plan=risk_plan,
        score=score,
        oak=oak,
        next_action="generate_grant_draft_sections_and_budget_stub",
    )
