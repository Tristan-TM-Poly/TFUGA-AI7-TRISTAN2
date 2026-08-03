from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from statistics import fmean
from typing import Any, Iterable, Mapping

from .hashing import sha256_hex, stable_id
from .ingest import normalize_receipts
from .models import (
    FailureCluster,
    InsightKind,
    LearningInsight,
    LearningReport,
    ObservationView,
    SkillLearning,
)
from .plateau import detect_plateau
from .transfer import infer_transfer_edges


class LearningAnalyzer:
    """Extract falsifiable learning claims from one or more campaign receipts."""

    def analyze(
        self,
        receipts: Iterable[Mapping[str, Any]],
        *,
        plateau_window: int = 8,
        insight_limit: int = 24,
    ) -> LearningReport:
        receipt_tuple = tuple(receipts)
        observations, logical_frontier = normalize_receipts(receipt_tuple)
        skills = self._skills(observations)
        clusters = self._failure_clusters(observations)
        transfers = infer_transfer_edges(observations)
        plateau = detect_plateau(observations, window=plateau_window)
        insights = self._insights(
            observations,
            skills,
            clusters,
            transfers,
            plateau,
            insight_limit,
        )

        successes = sum(1 for item in observations if item.success)
        total_gain = sum(item.information_gain for item in observations)
        total_cost = sum(item.cost_units for item in observations)
        unique_addresses = len({item.address for item in observations})
        mean_mutation = (
            fmean(item.mutation_score for item in observations)
            if observations
            else 0.0
        )
        identity = {
            "receipts": [
                {
                    "campaign_id": str(item.get("campaign_id", "")),
                    "receipt_sha256": str(item.get("receipt_sha256", "")),
                }
                for item in receipt_tuple
            ],
            "observations": [item.to_dict() for item in observations],
        }
        report = LearningReport(
            report_id=stable_id("learning-report", identity, length=24),
            system_version="R0.3",
            receipt_count=len(receipt_tuple),
            observation_count=len(observations),
            unique_addresses=unique_addresses,
            logical_frontier_cells=logical_frontier,
            coverage_ratio=(
                unique_addresses / logical_frontier if logical_frontier else 0.0
            ),
            success_rate=successes / len(observations) if observations else 0.0,
            mean_mutation_score=mean_mutation,
            total_information_gain=total_gain,
            total_cost_units=total_cost,
            information_efficiency=total_gain / max(1, total_cost),
            skills=skills,
            failure_clusters=clusters,
            transfer_edges=transfers,
            insights=insights,
            plateau=plateau,
            claims={
                "neural_training_claimed": False,
                "causal_transfer_claimed": False,
                "pedagogical_optimality_claimed": False,
                "formal_program_correctness_claimed": False,
                "learning_analysis_is_empirical": True,
                "counterexamples_are_prioritized": True,
                "uncertainty_is_explicit": True,
            },
        )
        return replace(
            report,
            report_sha256=sha256_hex(report.to_dict(include_hash=False)),
        )

    def _skills(
        self,
        observations: tuple[ObservationView, ...],
    ) -> tuple[SkillLearning, ...]:
        stats: dict[str, dict[str, float]] = defaultdict(
            lambda: {
                "successes": 0.0,
                "failures": 0.0,
                "observations": 0.0,
                "cost": 0.0,
                "gain": 0.0,
                "test_gap": 0.0,
            }
        )
        for observation in observations:
            reliability = 0.5 + 0.5 * observation.mutation_score
            for skill_id in observation.skills:
                row = stats[skill_id]
                if observation.success:
                    row["successes"] += reliability
                else:
                    row["failures"] += reliability
                row["observations"] += 1
                row["cost"] += observation.cost_units
                row["gain"] += observation.information_gain
                row["test_gap"] += observation.test_gap

        skills = [
            SkillLearning(
                skill_id=skill_id,
                successes=row["successes"],
                failures=row["failures"],
                observations=int(row["observations"]),
                total_cost=int(row["cost"]),
                total_information_gain=row["gain"],
                mutation_gap_sum=row["test_gap"],
            )
            for skill_id, row in stats.items()
        ]
        skills.sort(
            key=lambda item: (
                -(item.weakness * (1.0 + 4.0 * item.uncertainty)),
                -item.observations,
                item.skill_id,
            )
        )
        return tuple(skills)

    def _failure_clusters(
        self,
        observations: tuple[ObservationView, ...],
    ) -> tuple[FailureCluster, ...]:
        rows: dict[str, list[ObservationView]] = defaultdict(list)
        for observation in observations:
            for signature in observation.failure_signatures:
                rows[signature].append(observation)
            if observation.test_gap > 0:
                rows[f"surviving_mutation:{observation.mutation_family}"].append(
                    observation
                )

        clusters = []
        for signature, items in rows.items():
            clusters.append(
                FailureCluster(
                    signature=signature,
                    occurrences=len(items),
                    tasks=tuple(sorted({item.task_id for item in items})),
                    skills=tuple(
                        sorted({skill for item in items for skill in item.skills})
                    ),
                    mean_information_gain=fmean(
                        item.information_gain for item in items
                    ),
                    mean_cost=fmean(item.cost_units for item in items),
                    mean_mutation_gap=fmean(item.test_gap for item in items),
                )
            )
        clusters.sort(
            key=lambda item: (-item.repair_value, -item.occurrences, item.signature)
        )
        return tuple(clusters)

    def _insights(
        self,
        observations: tuple[ObservationView, ...],
        skills: tuple[SkillLearning, ...],
        clusters: tuple[FailureCluster, ...],
        transfers: tuple,
        plateau,
        limit: int,
    ) -> tuple[LearningInsight, ...]:
        insights: list[LearningInsight] = []

        for cluster in clusters[:8]:
            kind = (
                InsightKind.TEST_GAP
                if cluster.signature.startswith("surviving_mutation:")
                else InsightKind.COUNTEREXAMPLE
            )
            insights.append(
                LearningInsight(
                    insight_id=stable_id(
                        "insight",
                        {"kind": kind.value, "signature": cluster.signature},
                        length=20,
                    ),
                    kind=kind,
                    title=f"Réparer {cluster.signature}",
                    claim=(
                        f"Le motif {cluster.signature} concentre "
                        f"{cluster.occurrences} observations informatives."
                    ),
                    evidence=tuple(
                        [
                            f"repair_value={cluster.repair_value:.6f}",
                            f"mean_mutation_gap={cluster.mean_mutation_gap:.6f}",
                        ]
                        + [f"task={task}" for task in cluster.tasks[:4]]
                    ),
                    score=2.0
                    + cluster.repair_value
                    + (0.5 if kind is InsightKind.TEST_GAP else 0.0),
                    uncertainty=1.0 / (2.0 + cluster.occurrences),
                    falsifier=(
                        "Une campagne ciblée ne reproduit pas le motif sur des "
                        "tâches indépendantes."
                    ),
                    next_experiment=(
                        "Générer des contre-exemples minimaux et ajouter un test "
                        "de régression avant toute optimisation."
                    ),
                )
            )

        for skill in skills[:8]:
            score = skill.weakness * (1.0 + 4.0 * skill.uncertainty)
            insights.append(
                LearningInsight(
                    insight_id=stable_id(
                        "insight",
                        {"kind": "calibration", "skill": skill.skill_id},
                        length=20,
                    ),
                    kind=InsightKind.CALIBRATION,
                    title=f"Mesurer {skill.skill_id}",
                    claim=(
                        f"Maîtrise estimée {skill.mastery:.3f} avec incertitude "
                        f"{skill.uncertainty:.3f}."
                    ),
                    evidence=(
                        f"observations={skill.observations}",
                        f"learning_efficiency={skill.learning_efficiency:.6f}",
                        f"mean_test_gap={skill.mean_test_gap:.6f}",
                    ),
                    score=0.5 * score,
                    uncertainty=skill.uncertainty,
                    falsifier=(
                        "Des exercices indépendants montrent une performance "
                        "incompatible avec le posterior."
                    ),
                    next_experiment=(
                        "Choisir un exercice discriminant de difficulté voisine "
                        "avec mutation forte et coût borné."
                    ),
                )
            )

        for edge in transfers[:6]:
            if edge.confidence <= 0:
                continue
            insights.append(
                LearningInsight(
                    insight_id=stable_id(
                        "insight",
                        {
                            "kind": "transfer",
                            "source": edge.source_skill,
                            "target": edge.target_skill,
                        },
                        length=20,
                    ),
                    kind=InsightKind.TRANSFER,
                    title=f"Tester le transfert {edge.source_skill} → {edge.target_skill}",
                    claim=(
                        "Une co-réussite répétée suggère un pont de transfert, "
                        "sans établir une causalité."
                    ),
                    evidence=(
                        f"support={edge.supporting_successes}",
                        f"contradictions={edge.contradicting_failures}",
                        f"campaigns={edge.distinct_campaigns}",
                    ),
                    score=1.0 + edge.confidence,
                    uncertainty=1.0 - edge.confidence,
                    falsifier=(
                        "Le transfert disparaît lorsque la compétence source est "
                        "isolée expérimentalement."
                    ),
                    next_experiment=(
                        "Construire une paire contrôlée où seule la compétence "
                        "source varie."
                    ),
                )
            )

        if plateau.detected:
            insights.append(
                LearningInsight(
                    insight_id=stable_id(
                        "insight",
                        {"kind": "plateau", "plateau": plateau.kind.value},
                        length=20,
                    ),
                    kind=InsightKind.PLATEAU,
                    title=f"Briser le plateau {plateau.kind.value}",
                    claim=plateau.reason,
                    evidence=(
                        f"recent_novelty={plateau.recent_novelty:.6f}",
                        f"recent_information={plateau.recent_information_gain:.6f}",
                        f"recent_efficiency={plateau.recent_efficiency:.6f}",
                    ),
                    score=2.0
                    + max(
                        0.0,
                        plateau.previous_efficiency - plateau.recent_efficiency,
                    ),
                    uncertainty=0.25,
                    falsifier="Une nouvelle fenêtre retrouve une pente d'apprentissage positive.",
                    next_experiment=(
                        "Changer de générateur, renforcer les mutants ou déplacer "
                        "le curriculum vers une faiblesse incertaine."
                    ),
                )
            )

        if observations:
            best = max(
                observations,
                key=lambda item: (
                    item.information_efficiency,
                    item.mutation_score,
                    item.address,
                ),
            )
            insights.append(
                LearningInsight(
                    insight_id=stable_id(
                        "insight",
                        {"kind": "strategy", "task": best.task_id},
                        length=20,
                    ),
                    kind=InsightKind.STRATEGY,
                    title=f"Cristalliser la stratégie de {best.task_id}",
                    claim=(
                        "Cette observation maximise actuellement le gain "
                        "d'information par unité de coût."
                    ),
                    evidence=(
                        f"efficiency={best.information_efficiency:.6f}",
                        f"mutation_score={best.mutation_score:.6f}",
                        f"address={best.address}",
                    ),
                    score=1.0
                    + best.information_efficiency * (1.0 + best.mutation_score),
                    uncertainty=1.0 / 3.0,
                    falsifier=(
                        "La stratégie échoue sur une distribution indépendante ou "
                        "sous une famille de mutants plus forte."
                    ),
                    next_experiment=(
                        "Rejouer sur trois distributions indépendantes avant "
                        "inscription dans M⁺."
                    ),
                )
            )

        insights.sort(
            key=lambda item: (-item.score, item.uncertainty, item.insight_id)
        )
        return tuple(insights[: max(0, limit)])
