"""Adversarial Axiom Arena for bounded candidate generation and comparison."""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .core import AxiomGenome, stable_digest


def mutate_axiom(seed: AxiomGenome) -> tuple[AxiomGenome, ...]:
    """Create bounded *candidate* mutations. These are not semantic truths."""
    p = seed.passport
    mutations: list[AxiomGenome] = []

    negated = replace(
        p,
        claim_id=f"{p.claim_id}:NEG",
        statement=f"NOT ({p.statement})",
        dependencies=tuple(dict.fromkeys((*p.dependencies, p.claim_id))),
        version=f"{p.version}+neg",
    )
    mutations.append(replace(seed, passport=negated, parent_ids=(p.claim_id,), mutation_label="NEGATE", generated_candidate=True))

    if len(p.scope) > 1:
        narrowed_scope = p.scope[:-1]
        narrowed = replace(
            p,
            claim_id=f"{p.claim_id}:NARROW",
            scope=narrowed_scope,
            statement=f"[NARROWED to {', '.join(narrowed_scope)}] {p.statement}",
            version=f"{p.version}+narrow",
        )
        mutations.append(replace(seed, passport=narrowed, parent_ids=(p.claim_id,), mutation_label="NARROW_SCOPE", generated_candidate=True))

    boundary = replace(
        p,
        claim_id=f"{p.claim_id}:BOUNDARY",
        statement=f"Boundary candidate: determine where ({p.statement}) ceases to hold",
        version=f"{p.version}+boundary",
    )
    mutations.append(replace(
        seed,
        passport=boundary,
        boundary_conditions=tuple(dict.fromkeys((*seed.boundary_conditions, "OUTSIDE_DECLARED_SCOPE"))),
        parent_ids=(p.claim_id,),
        mutation_label="BOUNDARY_HUNT",
        generated_candidate=True,
    ))
    return tuple(mutations)


def heuristic_support_score(genome: AxiomGenome) -> float:
    """Non-authoritative triage score; never a truth score."""
    p = genome.passport
    support = sum(e.strength * (1.25 if e.independent else 1.0) for e in p.evidence)
    counter = sum(e.strength * (1.25 if e.independent else 1.0) for e in p.counterevidence)
    return round((support - counter) / max(1, len(p.scope)), 6)


def rank_candidates(candidates: Iterable[AxiomGenome]) -> list[dict[str, object]]:
    ranked = [{
        "claim_id": g.passport.claim_id,
        "score": heuristic_support_score(g),
        "authoritative": False,
        "generated_candidate": g.generated_candidate,
        "digest": g.digest(),
    } for g in candidates]
    ranked.sort(key=lambda item: (-float(item["score"]), str(item["claim_id"])))
    return ranked


def discriminating_predictions(left: AxiomGenome, right: AxiomGenome) -> list[dict[str, str]]:
    """Return prediction pairs that disagree under the same variable/condition."""
    out: list[dict[str, str]] = []
    for lp in left.predictions:
        for rp in right.predictions:
            if lp.variable == rp.variable and lp.condition == rp.condition and lp.expected != rp.expected:
                payload = {
                    "left_prediction": lp.prediction_id,
                    "right_prediction": rp.prediction_id,
                    "variable": lp.variable,
                    "condition": lp.condition,
                    "left_expected": lp.expected,
                    "right_expected": rp.expected,
                }
                payload["experiment_key"] = stable_digest(payload)[:16]
                out.append(payload)
    return out
