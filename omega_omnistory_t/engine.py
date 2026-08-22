"""Continuity and residual checks for Ω-OMNISTORY R6."""
from __future__ import annotations

from dataclasses import replace

from .models import CanonStatus, NarrativeResidual, StoryIR


def causal_cycle(story: StoryIR) -> tuple[str, ...]:
    graph = {event.event_id: tuple(event.causes) for event in story.events}
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def walk(node: str) -> tuple[str, ...] | None:
        if node in visiting:
            start = stack.index(node)
            return tuple(stack[start:] + [node])
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for parent in graph.get(node, ()):
            found = walk(parent)
            if found:
                return found
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in graph:
        found = walk(node)
        if found:
            return found
    return ()


def continuity_errors(story: StoryIR) -> list[str]:
    errors = story.validate()
    cycle = causal_cycle(story)
    if cycle:
        errors.append("causal_graph: cycle " + " -> ".join(cycle))
    facts = {fact.fact_id: fact for fact in story.canon}
    for fact in story.canon:
        for old in fact.supersedes:
            if old not in facts:
                errors.append(f"fact.{fact.fact_id}: supersedes unknown fact {old}")
        if fact.status is CanonStatus.RETCON and not fact.supersedes:
            errors.append(f"fact.{fact.fact_id}: RETCON requires a prior fact")
    return errors


def derive_residuals(story: StoryIR) -> tuple[NarrativeResidual, ...]:
    residuals = list(story.residuals)
    known = {item.residual_id for item in residuals}
    for event in story.events:
        if event.irreversible and not event.consequences:
            rid = f"R-CONSEQUENCE-{event.event_id}"
            if rid not in known:
                residuals.append(NarrativeResidual(
                    rid, "causality", "event",
                    f"Irreversible event {event.event_id} has no explicit consequence.",
                    4, (event.event_id,), "ConsequenceCompiler"
                ))
                known.add(rid)
    for fact in story.canon:
        if fact.status is CanonStatus.CONTRADICTED:
            rid = f"R-CANON-{fact.fact_id}"
            if rid not in known:
                residuals.append(NarrativeResidual(
                    rid, "canon", "fact",
                    f"Fact {fact.fact_id} is contradicted and needs resolution.",
                    5, (fact.fact_id,), "CanonRepairCompiler"
                ))
                known.add(rid)
    return tuple(sorted(residuals, key=lambda item: (-item.severity, item.residual_id)))


def with_derived_residuals(story: StoryIR) -> StoryIR:
    return replace(story, residuals=derive_residuals(story))


def projection_plan(story: StoryIR, backend: str) -> dict[str, object]:
    if backend not in story.presentation_backends:
        raise ValueError(f"backend {backend!r} is not enabled")
    errors = continuity_errors(story)
    if errors:
        raise ValueError("StoryIR validation failed: " + "; ".join(errors))
    return {
        "story_id": story.story_id,
        "backend": backend,
        "event_order": [event.event_id for event in story.events],
        "character_ids": [character.character_id for character in story.characters],
        "canon_ids": [fact.fact_id for fact in story.canon if fact.status is CanonStatus.CANON],
        "residual_ids": [item.residual_id for item in derive_residuals(story)],
        "invariant": "same-canon-not-same-presentation",
    }
