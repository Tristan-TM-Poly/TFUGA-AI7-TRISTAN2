"""PR Genome and dependency/conflict orchestration."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

from .models import ExperimentPlan, PRGene, SynergyCandidate, stable_id


def compile_pr_gene(candidate: SynergyCandidate, experiment: ExperimentPlan, paths: list[str] | None = None) -> PRGene:
    paths = paths or [
        f"experiments/{candidate.id}/experiment.json",
        f"reports/{candidate.id}/oak-report.json",
        f"registry/synergies/{candidate.id}.json",
    ]
    return PRGene(
        id=stable_id("PRG", candidate.id, paths),
        title=f"experiment: validate {' × '.join(candidate.systems)}",
        intention=experiment.hypothesis,
        candidate_id=candidate.id,
        paths=sorted(set(paths)),
        capabilities_added=candidate.transformations,
        needs_resolved=candidate.matched_needs,
        interfaces_provided=[contract.id for contract in candidate.proposed_interfaces],
        interfaces_consumed=[contract.target_type for contract in candidate.proposed_interfaces],
        tests=experiment.metrics + experiment.oak_gates,
        risks={
            "integration": candidate.tensor.integration_cost,
            "epistemic": candidate.tensor.uncertainty,
            "operational": candidate.tensor.risk,
            "debt": candidate.tensor.debt,
        },
        rollback=experiment.rollback,
        option_value=candidate.tensor.option_value,
    )


def infer_pr_relations(genes: Iterable[PRGene]) -> list[PRGene]:
    items = list(genes)
    for left in items:
        left_paths = set(left.paths)
        left_provided = set(left.interfaces_provided)
        for right in items:
            if left.id == right.id:
                continue
            if left_provided & set(right.interfaces_consumed):
                if left.id not in right.dependencies:
                    right.dependencies.append(left.id)
            shared_paths = left_paths & set(right.paths)
            incompatible_interfaces = left_provided & set(right.interfaces_provided)
            if shared_paths or incompatible_interfaces:
                if right.id not in left.conflicts:
                    left.conflicts.append(right.id)
        left.dependencies.sort()
        left.conflicts.sort()
    return items


def orchestration_waves(genes: Iterable[PRGene]) -> list[list[str]]:
    items = {item.id: item for item in infer_pr_relations(genes)}
    indegree = {item_id: 0 for item_id in items}
    outgoing: dict[str, set[str]] = defaultdict(set)
    for item in items.values():
        for dependency in item.dependencies:
            if dependency in items:
                indegree[item.id] += 1
                outgoing[dependency].add(item.id)
    ready = deque(sorted(item_id for item_id, degree in indegree.items() if degree == 0))
    waves: list[list[str]] = []
    scheduled: set[str] = set()
    while ready:
        current = list(ready)
        ready.clear()
        wave: list[str] = []
        for item_id in current:
            if item_id in scheduled:
                continue
            if any(conflict in wave for conflict in items[item_id].conflicts):
                ready.append(item_id)
                continue
            wave.append(item_id)
            scheduled.add(item_id)
        if not wave:
            item_id = current[0]
            wave = [item_id]
            scheduled.add(item_id)
        waves.append(wave)
        for item_id in wave:
            for target in outgoing.get(item_id, set()):
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
        ready = deque(sorted(set(ready)))
    remaining = sorted(set(items) - scheduled)
    waves.extend([[item_id] for item_id in remaining])
    return waves


def orchestra_manifest(genes: Iterable[PRGene]) -> dict:
    items = infer_pr_relations(list(genes))
    return {
        "schema_version": "1.0",
        "authority": "review_only_plan",
        "genes": [item.to_dict() for item in sorted(items, key=lambda item: item.id)],
        "waves": orchestration_waves(items),
        "rules": [
            "Each PR remains independently reviewable.",
            "Conflicting PRs are never scheduled in the same wave.",
            "No merge is authorized by this manifest.",
            "Rollback and evidence artifacts are mandatory before promotion.",
        ],
    }
