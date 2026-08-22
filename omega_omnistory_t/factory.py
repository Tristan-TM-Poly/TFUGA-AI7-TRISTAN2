"""Deterministic reference StoryIR used by tests and examples."""
from __future__ import annotations

from .models import CanonFact, CanonStatus, CausalEvent, CharacterGenome, StoryIR


def eighth_fire_story() -> StoryIR:
    return StoryIR(
        story_id="EIGHTH-FIRE-R6",
        title="Le Huitième Feu",
        premise="Une cartographe découvre qu'un réseau de lumières interdites répond aux choix humains et menace l'équilibre de sa cité.",
        theme_question="Que reste-t-il du libre arbitre quand le monde apprend de nos décisions?",
        world_rules=(
            "Toute lumière active laisse une trace mesurable.",
            "Une trace ne peut pas être effacée sans coût énergétique.",
            "Aucun personnage ne peut connaître un événement non observé sans source explicite.",
        ),
        characters=(
            CharacterGenome(
                character_id="CHAR-TRISTAN",
                name="Tristan",
                goals=("Comprendre le huitième feu",),
                fears=("Devenir la cause de la catastrophe",),
                knowledge=("sept réseaux publics",),
                abilities=("cartographie des traces",),
                constraints=("la lecture détruit une partie de la trace",),
                voice_rules=("phrases courtes sous pression",),
            ),
            CharacterGenome(
                character_id="CHAR-OBSERVATRICE",
                name="L'Observatrice",
                goals=("Préserver les traces",),
                fears=("Une vérité irréversible",),
                knowledge=("archives incomplètes",),
                voice_rules=("ne répond jamais avant d'avoir reformulé la question",),
            ),
        ),
        events=(
            CausalEvent(
                event_id="EV-001",
                summary="Tristan détecte une huitième signature lumineuse.",
                actors=("CHAR-TRISTAN",),
                consequences=("Le réseau interdit devient observable.",),
                irreversible=True,
            ),
            CausalEvent(
                event_id="EV-002",
                summary="L'Observatrice confronte Tristan avec une archive contradictoire.",
                causes=("EV-001",),
                actors=("CHAR-TRISTAN", "CHAR-OBSERVATRICE"),
                consequences=("Ils doivent choisir entre mesurer et préserver.",),
            ),
        ),
        canon=(
            CanonFact(
                fact_id="FACT-001",
                statement="Le huitième feu laisse une trace différente des sept réseaux publics.",
                status=CanonStatus.CANON,
                provenance=("EV-001",),
            ),
        ),
        presentation_backends=("manga", "anime", "novel", "game"),
        metadata={"epistemic_status": "FORMALIZED", "publication": "private-draft"},
    )
