"""LOG/CVCD/EXP layer for Ω-GAME-T."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import WorldGraph


@dataclass(slots=True)
class CVCDState:
    """Compressed fertile state extracted from the playable world."""

    danger: float = 0.0
    opportunity: float = 0.0
    imbalance: float = 0.0
    novelty: float = 0.0
    boredom: float = 0.0
    tension: float = 0.0
    coherence: float = 1.0
    invariants: dict[str, Any] = field(default_factory=dict)

    def fertile_tags(self) -> list[str]:
        tags: list[str] = []
        if self.tension >= 0.6:
            tags.append("conflict")
        if self.boredom >= 0.5:
            tags.append("novelty_needed")
        if self.imbalance >= 0.5:
            tags.append("rebalance_needed")
        if self.opportunity >= 0.5:
            tags.append("opportunity")
        if self.coherence < 0.6:
            tags.append("repair_coherence")
        return tags or ["stable_world"]


class WorldCompressor:
    """LOG compressor: world -> compact CVCD state.

    The default heuristic is intentionally transparent. Future versions can plug
    in telemetry, player modeling, Bayesian estimates, or learned embeddings.
    """

    def compress(self, world: WorldGraph) -> CVCDState:
        snapshot = world.snapshot()
        memory_count = snapshot["memory_count"]
        relation_count = snapshot["relation_count"]
        entity_count = max(1, snapshot["entity_count"])

        tension = min(1.0, relation_count / (entity_count * 2))
        novelty = min(1.0, len(snapshot["entity_kinds"]) / 8)
        boredom = max(0.0, 1.0 - novelty - min(0.3, memory_count / 20))
        opportunity = min(1.0, snapshot["hyperedge_count"] / max(1, entity_count))
        imbalance = self._estimate_imbalance(world)
        coherence = 1.0 if snapshot["entity_count"] else 0.0

        return CVCDState(
            danger=min(1.0, tension * 0.7 + imbalance * 0.3),
            opportunity=opportunity,
            imbalance=imbalance,
            novelty=novelty,
            boredom=boredom,
            tension=tension,
            coherence=coherence,
            invariants={
                "snapshot": snapshot,
                "fertile_relations": relation_count,
                "entity_kinds": snapshot["entity_kinds"],
            },
        )

    def _estimate_imbalance(self, world: WorldGraph) -> float:
        powers = [float(entity.attributes.get("power", 0.5)) for entity in world.entities.values()]
        if not powers:
            return 0.0
        return min(1.0, max(powers) - min(powers))


class QuestCVCD:
    """EXP generator: CVCD state -> quest/event blueprint."""

    def generate(self, cvcd: CVCDState) -> dict[str, Any]:
        tags = cvcd.fertile_tags()

        if "repair_coherence" in tags:
            return {
                "quest": "La fissure de cohérence",
                "objective": "Identifier la règle ou le souvenir qui contredit le monde.",
                "constraint": "Aucune nouvelle récompense avant réparation causale.",
                "reward": "Stabilité narrative et nouvelle information fiable.",
                "consequence": "Le monde réduit ses contradictions futures.",
                "cvcd_tags": tags,
            }

        if "rebalance_needed" in tags:
            return {
                "quest": "Le défi du contre-jeu",
                "objective": "Résoudre une situation où la force dominante devient insuffisante.",
                "constraint": "La solution brute est possible mais sous-optimale.",
                "reward": "Nouvelle stratégie, alliance ou outil de contre-jeu.",
                "consequence": "Le joueur découvre un axe de maîtrise non dominant.",
                "cvcd_tags": tags,
            }

        if "novelty_needed" in tags:
            return {
                "quest": "La bibliothèque qui ment",
                "objective": "Découvrir qui falsifie les archives.",
                "constraint": "Aucun combat ne révèle directement la vérité.",
                "reward": "Accès à une carte oubliée.",
                "consequence": "La faction choisie influence la prochaine région.",
                "cvcd_tags": tags,
            }

        if "conflict" in tags:
            return {
                "quest": "Le pacte sous tension",
                "objective": "Transformer un conflit latent en choix lisible.",
                "constraint": "Chaque option conserve un coût réel.",
                "reward": "Réputation, information ou ressource selon la décision.",
                "consequence": "La mémoire du monde enregistre la préférence du joueur.",
                "cvcd_tags": tags,
            }

        return {
            "quest": "Graine mycélienne",
            "objective": "Relier deux éléments du monde encore isolés.",
            "constraint": "La connexion doit créer un choix futur mesurable.",
            "reward": "Nouvelle piste de monde.",
            "consequence": "Le monde augmente sa densité narrative utile.",
            "cvcd_tags": tags,
        }
