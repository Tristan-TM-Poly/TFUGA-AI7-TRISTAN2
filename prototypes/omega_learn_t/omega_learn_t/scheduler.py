from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Iterable, List, Mapping

from .bayes_mastery import weakest_axes
from .core import ErrorRecord, MasteryAxis, axis_label, clamp01


@dataclass(frozen=True)
class ScheduledTask:
    due: str
    priority: float
    task_type: str
    prompt: str
    reason: str
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data


def _due(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def build_review_queue(
    skill: str,
    mastery: Mapping[MasteryAxis, float],
    invariants: Iterable[str],
    errors: Iterable[ErrorRecord],
    days: int = 7,
    tags: Iterable[str] = (),
) -> List[ScheduledTask]:
    """Build a prioritized review queue.

    Priority combines low mastery, M⁻ severity, and near-term OAK leverage.
    """

    base_tags = tuple(tags) + ("omega_learn_t",)
    tasks: List[ScheduledTask] = []
    weak = weakest_axes(mastery, limit=4)
    for idx, axis in enumerate(weak):
        score = mastery.get(axis, 0.5)
        priority = clamp01(1.0 - score + 0.15)
        tasks.append(
            ScheduledTask(
                due=_due(min(days, idx + 1)),
                priority=priority,
                task_type="axis_drill",
                prompt=f"{skill}: pratiquer l'axe {axis_label(axis)} avec un test actif.",
                reason=f"Axe faible détecté par Bayes: {axis.value}={score:.2f}",
                tags=base_tags + (axis.value,),
            )
        )
    for idx, inv in enumerate(list(invariants)[:8]):
        tasks.append(
            ScheduledTask(
                due=_due(1 + (idx % max(1, days))),
                priority=0.55,
                task_type="invariant_recall",
                prompt=f"Rappel actif: définir et appliquer l'invariant '{inv}' dans {skill}.",
                reason="Invariant CVCD à stabiliser.",
                tags=base_tags + ("invariant",),
            )
        )
    for idx, err in enumerate(sorted(errors, key=lambda e: e.severity, reverse=True)):
        tasks.append(
            ScheduledTask(
                due=_due(1 + (idx % max(1, days))),
                priority=clamp01(0.5 + err.severity / 3.0),
                task_type="m_minus_retest",
                prompt=f"Retester M⁻: {err.future_test}",
                reason=f"Erreur ouverte: {err.name}; cause: {err.cause}",
                tags=base_tags + ("m_minus",),
            )
        )
    tasks.append(
        ScheduledTask(
            due=_due(days),
            priority=0.8,
            task_type="oak_gate",
            prompt=f"OAK final pour {skill}: variante nouvelle + explication + capture résidus.",
            reason="Vérifier que la connaissance se décompresse en action/transfert.",
            tags=base_tags + ("oak",),
        )
    )
    return sorted(tasks, key=lambda t: (t.due, -t.priority, t.task_type))
