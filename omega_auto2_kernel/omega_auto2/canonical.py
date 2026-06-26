from __future__ import annotations

from .models import Workflow
from .workflow_synth import forge_workflow_from_task


CANONICAL_TASKS = {
    "daily_briefing": "produire un briefing quotidien OAK-safe sur IA, automation, agents, physique, énergie, matériaux, Québec Canada innovation, startups, IP, revenus, papiers, brevets et géopolitique tech",
    "github_factory": "transformer une théorie de Tristan en dépôt GitHub avec README, tests, documentation, OAKBench et roadmap",
    "maxcap_assessment": "définir mesurer et dépasser les capacités d'un workflow sans réduire OAK ni augmenter le chaos",
    "drivebrain_draft": "prévisualiser un scan DriveBrain avec index, doublons, permissions, canon et rapport sans modifier les fichiers",
}


def canonical_workflow(name: str) -> Workflow:
    if name not in CANONICAL_TASKS:
        raise KeyError(f"unknown canonical workflow: {name}")
    workflow = forge_workflow_from_task(CANONICAL_TASKS[name])
    workflow.id = f"auto2_canonical_{name}"
    workflow.name = f"AUTO2 Canonical: {name}"
    return workflow


def canonical_workflows() -> list[Workflow]:
    return [canonical_workflow(name) for name in CANONICAL_TASKS]
