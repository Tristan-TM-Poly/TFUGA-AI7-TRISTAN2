from __future__ import annotations

from .hashing import stable_id
from .models import ActionKind, LearningAction, LearningReport


class LearningPlanner:
    """Compile a learning report into finite, falsifiable next experiments."""

    def plan(
        self,
        report: LearningReport,
        *,
        limit: int = 12,
    ) -> tuple[LearningAction, ...]:
        actions: list[LearningAction] = []

        for cluster in report.failure_clusters[:5]:
            kind = (
                ActionKind.REPAIR_TEST
                if cluster.mean_mutation_gap > 0.0
                else ActionKind.REPAIR_SKILL
            )
            actions.append(
                self._action(
                    kind=kind,
                    target=cluster.signature,
                    priority=2.0 + cluster.repair_value,
                    rationale=(
                        f"{cluster.occurrences} occurrences; repair value "
                        f"{cluster.repair_value:.4f}."
                    ),
                    experiment_spec={
                        "generator": "inverse_failure",
                        "signature": cluster.signature,
                        "task_sample": list(cluster.tasks[:4]),
                        "minimum_counterexamples": 8,
                        "require_independent_tasks": True,
                    },
                    success_criterion=(
                        "Le motif est reproduit, minimisé, puis rejeté par un test "
                        "de régression sur toutes les tâches ciblées."
                    ),
                    stop_condition=(
                        "Arrêter si le motif ne se reproduit pas sur huit essais "
                        "indépendants ou si IPGate bloque la provenance."
                    ),
                )
            )

        for skill in report.skills[:5]:
            priority = skill.weakness * (1.0 + 5.0 * skill.uncertainty)
            actions.append(
                self._action(
                    kind=ActionKind.REPAIR_SKILL,
                    target=skill.skill_id,
                    priority=priority,
                    rationale=(
                        f"mastery={skill.mastery:.4f}; "
                        f"uncertainty={skill.uncertainty:.4f}."
                    ),
                    experiment_spec={
                        "curriculum": "discriminating",
                        "skill_id": skill.skill_id,
                        "target_success_probability": 0.65,
                        "mutation_score_floor": 0.8,
                        "replications": 6,
                    },
                    success_criterion=(
                        "Le posterior de maîtrise augmente et l'incertitude diminue "
                        "sur une série indépendante."
                    ),
                    stop_condition=(
                        "Arrêter si le coût marginal dépasse le budget ou si trois "
                        "échecs successifs ont la même cause non traitée."
                    ),
                )
            )

        for edge in report.transfer_edges[:4]:
            if edge.confidence < 0.35:
                continue
            actions.append(
                self._action(
                    kind=ActionKind.CONFIRM_TRANSFER,
                    target=f"{edge.source_skill}->{edge.target_skill}",
                    priority=edge.confidence,
                    rationale=(
                        f"confidence={edge.confidence:.4f}, "
                        f"campaigns={edge.distinct_campaigns}."
                    ),
                    experiment_spec={
                        "design": "paired_control",
                        "source_skill": edge.source_skill,
                        "target_skill": edge.target_skill,
                        "replications": 10,
                        "hold_other_axes_constant": True,
                    },
                    success_criterion=(
                        "Le gain sur la compétence cible persiste dans une "
                        "comparaison contrôlée."
                    ),
                    stop_condition=(
                        "Arrêter si les contradictions égalent ou dépassent les "
                        "réussites de soutien."
                    ),
                )
            )

        if report.plateau.detected:
            actions.append(
                self._action(
                    kind=ActionKind.EXPLORE_FRONTIER,
                    target=f"plateau:{report.plateau.kind.value}",
                    priority=3.0,
                    rationale=report.plateau.reason,
                    experiment_spec={
                        "policy": "frontier_shift",
                        "change_axes": ["domain", "archetype", "mutation_family"],
                        "preserve_budget": True,
                        "compare_against_previous_window": True,
                    },
                    success_criterion=(
                        "Le gain d'information ou la nouveauté dépasse la fenêtre "
                        "précédente d'au moins vingt pour cent."
                    ),
                    stop_condition=(
                        "Arrêter après une fenêtre complète sans amélioration."
                    ),
                )
            )

        if report.information_efficiency < 0.05 and report.observation_count:
            actions.append(
                self._action(
                    kind=ActionKind.REDUCE_COST,
                    target="global_information_efficiency",
                    priority=1.5,
                    rationale=(
                        f"information_efficiency={report.information_efficiency:.6f}"
                    ),
                    experiment_spec={
                        "policy": "cost_ablation",
                        "compare": ["baseline", "reduced_input", "cheaper_oracle"],
                    },
                    success_criterion=(
                        "Conserver au moins quatre-vingt-dix pour cent du gain "
                        "d'information avec un coût inférieur."
                    ),
                    stop_condition="Arrêter si la qualité des preuves diminue.",
                )
            )

        deduplicated = {action.action_id: action for action in actions}
        ranked = sorted(
            deduplicated.values(),
            key=lambda item: (-item.priority, item.action_id),
        )
        return tuple(ranked[: max(0, limit)])

    def _action(
        self,
        *,
        kind: ActionKind,
        target: str,
        priority: float,
        rationale: str,
        experiment_spec: dict,
        success_criterion: str,
        stop_condition: str,
    ) -> LearningAction:
        action_id = stable_id(
            "learning-action",
            {
                "kind": kind.value,
                "target": target,
                "experiment_spec": experiment_spec,
            },
            length=20,
        )
        return LearningAction(
            action_id=action_id,
            kind=kind,
            priority=priority,
            target=target,
            rationale=rationale,
            experiment_spec=experiment_spec,
            success_criterion=success_criterion,
            stop_condition=stop_condition,
        )
