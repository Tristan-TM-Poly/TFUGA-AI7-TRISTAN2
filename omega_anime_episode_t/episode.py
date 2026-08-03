"""Build the canonical 20-minute first episode of Le Huitième Feu."""

from __future__ import annotations

from dataclasses import dataclass

from omega_anime_animatic_t.models import AnimaticScene, AnimaticShot, AnimaticTimeline
from omega_anime_animatic_t.timeline import build_eighth_fire_animatic_r2


EPISODE_DURATION_S = 1200.0
SHOTS_PER_NEW_SCENE = 12


@dataclass(frozen=True)
class SequenceBlueprint:
    scene_id: str
    title: str
    duration_s: float
    objective: str
    irreversible_change: str
    captions: tuple[str, ...]
    dialogue: dict[int, str]
    audio_cue: str


PURPOSES = (
    "establish",
    "question",
    "reveal",
    "compare",
    "test",
    "resist",
    "decide",
    "execute",
    "observe",
    "pay cost",
    "reframe",
    "hook",
)

FRAMINGS = (
    "extreme wide",
    "wide",
    "medium two-shot",
    "medium",
    "close-up",
    "insert",
    "over shoulder",
    "profile close-up",
    "top shot",
    "tracking wide",
    "reaction close-up",
    "symbolic macro",
)

CAMERA_MOTIONS = (
    "locked",
    "slow push",
    "lateral drift",
    "handheld micro-drift",
    "rack focus",
    "orbital move",
    "slow pullback",
    "tilt down",
    "controlled shake",
    "tracking forward",
    "breathing hold",
    "hard cut",
)

SUBJECTS = (
    ("TRISTAN",),
    ("RESEAU",),
    ("TRISTAN", "RESEAU"),
    ("OBSERVATRICE",),
    ("TRISTAN", "OBSERVATRICE"),
    ("INSTRUMENT",),
    ("TRISTAN", "INSTRUMENT"),
    ("VILLE",),
    ("RESEAU", "VILLE"),
    ("DETTE_CAUSALE",),
    ("TRISTAN", "DETTE_CAUSALE"),
    ("OBSERVATRICE", "RESEAU"),
)


BLUEPRINTS = (
    SequenceBlueprint(
        scene_id="S06-TITLE",
        title="Le titre qui refuse de disparaître",
        duration_s=60.0,
        objective="Transformer le choc de l'ouverture en promesse de série.",
        irreversible_change="Le Huitième Feu devient un phénomène nommé et mémorisable.",
        captions=(
            "Le laboratoire reprend son souffle.",
            "Les écrans affichent la même cicatrice.",
            "Le nom apparaît avant d'être prononcé.",
            "Huit lignes convergent sans se toucher.",
            "La ville devient un circuit silencieux.",
            "Tristan reste seul devant le réseau.",
            "Une ombre observe depuis une couche impossible.",
            "Le motif se replie sur lui-même.",
            "Chaque correction laisse une trace.",
            "Chaque trace réclame un témoin.",
            "Le titre se forme dans le bruit.",
            "LE HUITIÈME FEU.",
        ),
        dialogue={11: "Ce n'est pas une énergie. C'est une permission."},
        audio_cue="title-pulse+guide-motif",
    ),
    SequenceBlueprint(
        scene_id="S07-AFTERMATH",
        title="Après la correction",
        duration_s=180.0,
        objective="Mesurer ce que la correction de trois minutes a déplacé.",
        irreversible_change="Tristan découvre que la dette causale possède une adresse réelle.",
        captions=(
            "Les capteurs reviennent un par un.",
            "La panne locale a disparu.",
            "Une autre anomalie naît six rues plus loin.",
            "Les horloges ne dérivent pas toutes ensemble.",
            "Un hôpital bascule sur ses réserves.",
            "La carte énergétique refuse la coïncidence.",
            "Tristan superpose les deux événements.",
            "Le réseau dessine une trajectoire de transfert.",
            "La correction a déplacé le coût.",
            "Le coût a choisi le maillon le plus fragile.",
            "Tristan ouvre un registre de dette causale.",
            "La première entrée porte son propre identifiant.",
        ),
        dialogue={3: "La panne n'a pas disparu.", 8: "Elle a changé de propriétaire.", 11: "Dette numéro un : moi."},
        audio_cue="aftermath-grid+low-heartbeat",
    ),
    SequenceBlueprint(
        scene_id="S08-TRACE",
        title="La trace de l'Observatrice",
        duration_s=180.0,
        objective="Prouver que l'Observatrice laisse une signature testable.",
        irreversible_change="Tristan obtient une réponse qui dépend de sa question.",
        captions=(
            "Le signal revient à intervalle non périodique.",
            "Tristan élimine les explications instrumentales.",
            "Le motif survit au changement de capteur.",
            "Il survit au changement de fréquence.",
            "Il disparaît lorsque personne ne regarde.",
            "Une caméra aveugle enregistre pourtant une absence.",
            "Tristan construit un test à choix forcé.",
            "Deux chemins identiques reçoivent deux questions différentes.",
            "Un seul chemin se met à vibrer.",
            "La réponse encode le mot témoin.",
            "L'Observatrice n'envoie pas un message.",
            "Elle modifie la possibilité de recevoir.",
        ),
        dialogue={5: "Tu ne te caches pas de la caméra.", 8: "Tu te caches de l'intention.", 11: "Alors réponds à ceci : qui paie ?"},
        audio_cue="observer-trace+phase-whisper",
    ),
    SequenceBlueprint(
        scene_id="S09-COUNTERMOVE",
        title="Le contre-mouvement",
        duration_s=180.0,
        objective="Empêcher une seconde dette sans perdre le réseau.",
        irreversible_change="Tristan accepte une correction plus lente mais réversible.",
        captions=(
            "Trois quartiers entrent dans la zone rouge.",
            "La solution immédiate exige un nouveau transfert.",
            "Tristan refuse la répétition.",
            "Il fragmente l'action en douze micro-corrections.",
            "Chaque micro-correction attend une preuve locale.",
            "Le réseau résiste à la première contrainte.",
            "Une branche tente de contourner le verrou.",
            "Tristan réduit l'ambition au lieu d'augmenter la force.",
            "Le système retrouve une marge de stabilité.",
            "La ville perd de la puissance mais garde ses fonctions vitales.",
            "La correction devient observable et réversible.",
            "Pour la première fois, le réseau cède sans victime cachée.",
        ),
        dialogue={2: "Pas une autre victoire invisible.", 7: "Moins vite. Mais sans voler le coût à quelqu'un d'autre.", 11: "Cette fois, je peux revenir en arrière."},
        audio_cue="countermove-sequence+relay-rhythm",
    ),
    SequenceBlueprint(
        scene_id="S10-DEBT",
        title="La dette prend forme",
        duration_s=180.0,
        objective="Révéler que les dettes causales peuvent se regrouper et apprendre.",
        irreversible_change="La dette devient un agent narratif capable d'anticiper Tristan.",
        captions=(
            "Les anciennes anomalies se synchronisent.",
            "Le registre de dette s'ouvre tout seul.",
            "Des entrées futures apparaissent sans valeur.",
            "Une silhouette se compose de conséquences évitées.",
            "Elle ne possède ni visage ni voix stable.",
            "Elle emprunte les sons des systèmes fragiles.",
            "Tristan tente de fermer le registre.",
            "Chaque fermeture crée deux nouvelles branches.",
            "La dette prédit sa prochaine correction.",
            "Elle place déjà le coût sur son chemin.",
            "L'Observatrice intervient pour la première fois.",
            "Elle appelle la forme : le Créancier.",
        ),
        dialogue={4: "Je suis ce que tu refuses de compter.", 8: "Corrige encore. Je saurai où attendre.", 11: "Tu viens de lui apprendre ton langage."},
        audio_cue="causal-debt+fractured-voices",
    ),
    SequenceBlueprint(
        scene_id="S11-CHOICE",
        title="Choisir une limite",
        duration_s=150.0,
        objective="Forcer Tristan à définir une frontière morale opérationnelle.",
        irreversible_change="Tristan renonce à la correction totale et grave une règle de souveraineté.",
        captions=(
            "Le Créancier offre une solution parfaite.",
            "Toutes les anomalies peuvent être déplacées hors de la ville.",
            "La destination reste inconnue.",
            "Tristan simule dix mille futurs incomplets.",
            "Aucun futur ne prouve l'absence de victime.",
            "L'Observatrice refuse de choisir à sa place.",
            "Le réseau réclame une décision immédiate.",
            "Tristan coupe sa propre autorité d'écriture.",
            "Il inscrit une limite : aucun coût sans témoin.",
            "La solution parfaite s'effondre.",
            "La ville survit avec ses imperfections.",
            "Le Créancier conserve pourtant une copie de la règle.",
        ),
        dialogue={1: "Je peux tout réparer.", 5: "Tu peux surtout tout déplacer.", 8: "Aucun coût sans témoin.", 11: "Alors je trouverai un monde sans témoins."},
        audio_cue="choice-silence+single-pulse",
    ),
    SequenceBlueprint(
        scene_id="S12-END",
        title="Après le feu — La Station des Absents",
        duration_s=90.0,
        objective="Fermer l'arc local et ouvrir une destination précise pour l'épisode suivant.",
        irreversible_change="Le réseau reconnaît Tristan et révèle une seconde installation active.",
        captions=(
            "Le matin atteint enfin le laboratoire.",
            "Les fonctions vitales de la ville restent stables.",
            "Le registre affiche une dette non résolue.",
            "Tristan sauvegarde toutes les preuves.",
            "Il refuse d'effacer ses erreurs.",
            "Un second réseau s'allume au-delà de la carte.",
            "Une station abandonnée apparaît sous la neige.",
            "Des câbles sans alimentation émettent une chaleur régulière.",
            "Le symbole du Huitième Feu couvre les murs.",
            "Une voix appelle Tristan avec huit ans d'avance.",
            "La porte se ferme sur le chiffre huit.",
            "Épisode 2 : La Station des Absents.",
        ),
        dialogue={4: "On garde tout. Même ce qui me condamne.", 9: "Tristan, tu es en retard de huit ans.", 11: "La Station des Absents."},
        audio_cue="end-motif+preview-stinger",
    ),
)


def _build_extension(start_s: float, start_scene_order: int, start_global_index: int) -> tuple[list[AnimaticScene], list[AnimaticShot]]:
    scenes: list[AnimaticScene] = []
    shots: list[AnimaticShot] = []
    cursor = start_s
    global_index = start_global_index

    for offset, blueprint in enumerate(BLUEPRINTS):
        scene_order = start_scene_order + offset
        duration = blueprint.duration_s / SHOTS_PER_NEW_SCENE
        scene_start = cursor
        for order in range(1, SHOTS_PER_NEW_SCENE + 1):
            global_index += 1
            start = round(cursor, 6)
            end = round(start + duration, 6)
            intensity = round(min(1.0, 0.24 + global_index / 145.0), 3)
            shots.append(
                AnimaticShot(
                    shot_id=f"{blueprint.scene_id}-SH{order:02d}",
                    scene_id=blueprint.scene_id,
                    order=order,
                    start_s=start,
                    end_s=end,
                    duration_s=round(duration, 6),
                    purpose=PURPOSES[order - 1],
                    framing=FRAMINGS[order - 1],
                    camera_motion=CAMERA_MOTIONS[order - 1],
                    subjects=SUBJECTS[order - 1],
                    caption=blueprint.captions[order - 1],
                    dialogue=blueprint.dialogue.get(order - 1, ""),
                    audio_cue=blueprint.audio_cue,
                    intensity=intensity,
                )
            )
            cursor = end
        scenes.append(
            AnimaticScene(
                scene_id=blueprint.scene_id,
                title=blueprint.title,
                order=scene_order,
                start_s=scene_start,
                end_s=cursor,
                duration_s=blueprint.duration_s,
                objective=blueprint.objective,
                irreversible_change=blueprint.irreversible_change,
            )
        )
    return scenes, shots


def build_eighth_fire_episode_01_r3() -> AnimaticTimeline:
    """Return episode 1 as exactly 20 minutes, preserving the R2 cold open."""

    cold_open = build_eighth_fire_animatic_r2()
    extension_scenes, extension_shots = _build_extension(
        start_s=cold_open.duration_s,
        start_scene_order=len(cold_open.scenes) + 1,
        start_global_index=len(cold_open.shots),
    )
    timeline = AnimaticTimeline(
        project_id="omega-anime-episode/eighth-fire/episode-01-r3",
        title="Le Huitième Feu — Épisode 1 : La dette du réseau",
        version="omega-anime-episode/r3",
        duration_s=EPISODE_DURATION_S,
        fps_reference=24,
        publication_state="private-draft",
        scenes=tuple((*cold_open.scenes, *extension_scenes)),
        shots=tuple((*cold_open.shots, *extension_shots)),
        disclaimers=(
            "Épisode procédural basse fidélité de 20 minutes; ce n'est pas une animation finale.",
            "Les 180 premières secondes conservent l'animatique R2 comme ouverture froide canonique.",
            "Voix, sons et images sont des guides originaux sans imitation d'artiste, studio ou personne réelle.",
            "La cohérence logicielle ne prouve ni qualité artistique, ni audience, ni faisabilité de production.",
        ),
    )
    timeline.require_valid()
    if timeline.duration_s != EPISODE_DURATION_S:
        raise RuntimeError(f"episode duration mismatch: {timeline.duration_s}")
    if len(timeline.scenes) != 12 or len(timeline.shots) != 114:
        raise RuntimeError("episode structure mismatch")
    return timeline
