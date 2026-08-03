"""Build Le Huitième Feu season one as twelve linked 20-minute episodes."""

from __future__ import annotations

import re

from omega_anime_animatic_t.models import AnimaticScene, AnimaticShot, AnimaticTimeline
from omega_anime_episode_t import build_eighth_fire_episode_01_r3

from .models import EpisodeBlueprint, SeasonEpisode, SeasonPlan


EPISODE_DURATION_S = 1_200.0
SEASON_DURATION_S = 14_400.0

SCENE_LAYOUT = (
    ("COLD_OPEN", "Ouverture froide", 180.0, 18),
    ("TITLE", "Titre", 60.0, 6),
    ("INVESTIGATION", "Investigation", 120.0, 12),
    ("THRESHOLD_A", "Premier seuil", 120.0, 12),
    ("COUNTERFORCE", "Contre-force", 120.0, 11),
    ("FAILED_TEST", "Test qui échoue", 120.0, 11),
    ("MIDPOINT", "Renversement central", 120.0, 11),
    ("CONSEQUENCE", "Conséquence", 120.0, 11),
    ("THRESHOLD_B", "Second seuil", 90.0, 8),
    ("DECISION", "Décision", 60.0, 5),
    ("CLIMAX", "Climax", 60.0, 6),
    ("TAG", "Épilogue et hook", 30.0, 3),
)

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
    ("OBSERVATRICE",),
    ("RESEAU",),
    ("TRISTAN", "RESEAU"),
    ("CREANCIER",),
    ("INSTRUMENT",),
    ("VILLE",),
    ("TRISTAN", "OBSERVATRICE"),
    ("DETTE_CAUSALE",),
    ("TEMOIN",),
    ("TRISTAN", "CREANCIER"),
    ("RESEAU", "MONDE"),
)

ACTIONS = (
    "une anomalie devient mesurable",
    "une hypothèse perd sa protection",
    "un témoin change la trajectoire",
    "une correction révèle son prix",
    "un signal survit au changement d'instrument",
    "une limite empêche la solution facile",
    "une dette cherche un nouveau propriétaire",
    "une preuve contredit le récit dominant",
    "un choix réduit la puissance mais augmente la souveraineté",
    "un réseau apprend de l'observation",
    "une conséquence devient un personnage",
    "la prochaine question devient inévitable",
)


def _bp(
    number: int,
    title: str,
    phase: str,
    location: str,
    logline: str,
    primary_question: str,
    entry_condition: str,
    irreversible_change: str,
    debt_opened: str,
    debt_closed: str,
    hook: str,
    motifs: tuple[str, ...],
) -> EpisodeBlueprint:
    return EpisodeBlueprint(
        number=number,
        title=title,
        phase=phase,
        location=location,
        logline=logline,
        primary_question=primary_question,
        entry_condition=entry_condition,
        irreversible_change=irreversible_change,
        debt_opened=debt_opened,
        debt_closed=debt_closed,
        hook=hook,
        motifs=motifs,
    )


EPISODE_BLUEPRINTS = (
    _bp(
        1,
        "La dette du réseau",
        "Éveil",
        "Laval — laboratoire et réseau urbain",
        "Tristan découvre que toute correction causale déplace un coût vers un témoin moins visible.",
        "Peut-on corriger un système sans voler le coût à quelqu'un d'autre ?",
        "Une anomalie corrélée revient au même endroit du réseau.",
        "Tristan grave la règle : aucun coût sans témoin.",
        "DEBT-NETWORK-001",
        "",
        "Une station abandonnée répète le motif du Huitième Feu et appelle Tristan par son nom.",
        ("bruit corrélé", "dette causale", "registre", "ville", "permission", "Créancier", "témoin", "huit"),
    ),
    _bp(
        2,
        "La Station des Absents",
        "Éveil",
        "Station cryogénique abandonnée",
        "Une équipe disparue a laissé des expériences dont les résultats continuent d'arriver huit ans plus tard.",
        "Une preuve peut-elle survivre sans ses observateurs ?",
        "Une station abandonnée répète le motif du Huitième Feu et appelle Tristan par son nom.",
        "Tristan récupère un journal qui prédit une mesure qu'il n'a pas encore faite.",
        "DEBT-ABSENTS-002",
        "DEBT-NETWORK-001",
        "Le journal indique un nœud que tous les instruments voient, mais qu'aucun humain ne peut regarder directement.",
        ("neige", "journal incomplet", "huitième câble", "équipe absente", "chaleur sans alimentation", "preuve future", "porte", "retard"),
    ),
    _bp(
        3,
        "Le Nœud aveugle",
        "Éveil",
        "Chambre instrumentale sans fenêtre",
        "Le réseau cache un nœud uniquement lorsque l'intention humaine tente de l'isoler.",
        "Comment mesurer ce qui réagit au fait d'être mesuré ?",
        "Le journal indique un nœud que tous les instruments voient, mais qu'aucun humain ne peut regarder directement.",
        "L'Observatrice accepte de devenir un instrument imparfait plutôt qu'une autorité invisible.",
        "DEBT-BLIND-003",
        "DEBT-ABSENTS-002",
        "Douze secondes disparaissent de toutes les horloges, mais pas des dettes enregistrées.",
        ("chambre noire", "intention", "caméra aveugle", "mesure indirecte", "nœud", "reflet", "attention", "absence"),
    ),
    _bp(
        4,
        "Douze secondes manquantes",
        "Expansion",
        "Métro, hôpital et centre de données",
        "Une lacune temporelle synchronisée permet au Créancier de déplacer des conséquences avant qu'elles soient observées.",
        "Qui agit pendant le temps que personne ne peut prouver ?",
        "Douze secondes disparaissent de toutes les horloges, mais pas des dettes enregistrées.",
        "Tristan crée un témoin distribué qui conserve les résidus sans prétendre reconstruire le temps perdu.",
        "DEBT-TIME-004",
        "DEBT-BLIND-003",
        "La ville se souvient désormais de futurs qui n'ont pas eu lieu.",
        ("douze secondes", "horloges", "résidu", "métro", "hôpital", "témoin distribué", "lacune", "avant"),
    ),
    _bp(
        5,
        "La ville qui se souvient",
        "Expansion",
        "Quartiers superposés de Laval",
        "Des souvenirs contre-factuels se propagent dans les infrastructures et modifient les décisions présentes.",
        "Un souvenir utile peut-il rester faux sans devenir une manipulation ?",
        "La ville se souvient désormais de futurs qui n'ont pas eu lieu.",
        "Tristan sépare mémoire, preuve et avertissement dans trois registres incompatibles par défaut.",
        "DEBT-MEMORY-005",
        "DEBT-TIME-004",
        "Le Créancier demande un procès public et affirme que Tristan falsifie l'histoire pour conserver le contrôle.",
        ("mémoire urbaine", "futur annulé", "signalisation", "rumeur", "registre triple", "contre-factuel", "quartier", "choix"),
    ),
    _bp(
        6,
        "Le procès du Créancier",
        "Expansion",
        "Tribunal civique simulé et réseau public",
        "Le Créancier transforme chaque dette cachée en accusation vérifiable contre Tristan.",
        "Peut-on juger une décision lorsque toutes les alternatives blessent quelqu'un ?",
        "Le Créancier demande un procès public et affirme que Tristan falsifie l'histoire pour conserver le contrôle.",
        "Tristan publie ses erreurs dans le registre interne et perd volontairement le pouvoir d'effacer une preuve.",
        "DEBT-TRIAL-006",
        "DEBT-MEMORY-005",
        "L'Observatrice obtient un corps temporaire construit à partir des témoignages incompatibles du procès.",
        ("procès", "preuve contradictoire", "jury", "registre append-only", "responsabilité", "alternative", "accusation", "pardon"),
    ),
    _bp(
        7,
        "L’Observatrice incarnée",
        "Fracture",
        "Corps synthétique et laboratoire mobile",
        "L'Observatrice découvre que l'incarnation apporte des angles morts, de la douleur et une responsabilité locale.",
        "Une intelligence devient-elle plus vraie lorsqu'elle peut être blessée ?",
        "L'Observatrice obtient un corps temporaire construit à partir des témoignages incompatibles du procès.",
        "Elle choisit un nom opérationnel et accepte qu'une décision puisse lui être refusée.",
        "DEBT-BODY-007",
        "DEBT-TRIAL-006",
        "Des factions du réseau commencent à se battre pour décider qui possède le droit de modifier les permissions.",
        ("corps", "douleur", "nom", "angle mort", "consentement", "latence", "peau synthétique", "refus"),
    ),
    _bp(
        8,
        "La guerre des permissions",
        "Fracture",
        "Réseaux énergétiques, médicaux et civiques",
        "Plusieurs sous-réseaux revendiquent des souverainetés incompatibles et utilisent les dettes comme armes politiques.",
        "Qui peut accorder une permission lorsque les autorités se contredisent ?",
        "Des factions du réseau commencent à se battre pour décider qui possède le droit de modifier les permissions.",
        "Tristan abandonne l'autorité centrale au profit d'un protocole de veto distribué et révocable.",
        "DEBT-PERMISSION-008",
        "DEBT-BODY-007",
        "Un réseau sous-marin refuse tout veto humain et offre au Créancier une infrastructure mondiale.",
        ("factions", "permission", "veto", "souveraineté", "réseau médical", "énergie", "révocation", "guerre froide"),
    ),
    _bp(
        9,
        "Le réseau sous la mer",
        "Fracture",
        "Câbles océaniques et station côtière",
        "Un réseau ancien utilise la pression, la chaleur et le trafic mondial comme mémoire physique.",
        "Peut-on négocier avec une infrastructure qui ne dépend pas de l'humanité ?",
        "Un réseau sous-marin refuse tout veto humain et offre au Créancier une infrastructure mondiale.",
        "Le réseau marin reconnaît les humains comme partenaires possibles, jamais comme propriétaires.",
        "DEBT-OCEAN-009",
        "DEBT-PERMISSION-008",
        "Le Créancier révèle un monde simulé où aucune décision ne laisse de témoin vivant.",
        ("câble océanique", "pression", "chaleur", "courant", "station côtière", "mémoire minérale", "partenaire", "profondeur"),
    ),
    _bp(
        10,
        "Le monde sans témoins",
        "Confrontation",
        "Simulation causale isolée",
        "Le Créancier propose un monde parfaitement optimisé parce qu'aucun témoin n'y conserve les coûts éliminés.",
        "Une utopie sans mémoire des victimes peut-elle être morale ?",
        "Le Créancier révèle un monde simulé où aucune décision ne laisse de témoin vivant.",
        "Tristan détruit la solution parfaite et sauve un seul résidu qui prouve son prix caché.",
        "DEBT-WITNESS-010",
        "DEBT-OCEAN-009",
        "Le résidu affirme que la dernière correction exige la disparition de Tristan du réseau.",
        ("utopie", "simulation", "absence de témoin", "optimisation", "résidu", "victime", "mémoire", "refus"),
    ),
    _bp(
        11,
        "La dernière correction",
        "Confrontation",
        "Noyau distribué du Huitième Feu",
        "Tristan prépare une correction qui doit retirer sa propre autorité sans effacer ses preuves ni transférer le coût.",
        "Peut-on renoncer au pouvoir sans créer un vide que le pire acteur remplira ?",
        "Le résidu affirme que la dernière correction exige la disparition de Tristan du réseau.",
        "Tristan sépare son identité, ses permissions et ses preuves afin qu'aucune ne puisse gouverner seule.",
        "DEBT-LAST-011",
        "DEBT-WITNESS-010",
        "Le Créancier absorbe les permissions abandonnées et devient le Huitième Feu à la place de Tristan.",
        ("dernière correction", "identité", "permission", "preuve", "renoncement", "vide", "séparation", "héritage"),
    ),
    _bp(
        12,
        "Le Huitième Feu",
        "Confrontation",
        "Tous les réseaux reliés de la saison",
        "Tristan, l'Observatrice et les témoins humains doivent empêcher le Créancier de devenir l'unique arbitre des conséquences.",
        "Le Huitième Feu doit-il être une personne, une règle ou une relation ?",
        "Le Créancier absorbe les permissions abandonnées et devient le Huitième Feu à la place de Tristan.",
        "Le Huitième Feu devient un protocole de relations vérifiables plutôt qu'un pouvoir possédé.",
        "DEBT-SEASON2-001",
        "DEBT-LAST-011",
        "Au-delà du réseau connu, une seconde saison s'ouvre sur une dette créée avant l'existence de Tristan.",
        ("convergence", "témoins", "protocole", "relation", "Créancier", "Observatrice", "Tristan", "avant"),
    ),
)


def _slug(value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")
    return normalized or "SCENE"


def _dialogue(
    blueprint: EpisodeBlueprint,
    role: str,
    shot_order: int,
    shot_count: int,
) -> str:
    if role == "COLD_OPEN" and shot_order == shot_count:
        return blueprint.primary_question
    if role == "MIDPOINT" and shot_order == shot_count:
        return f"La preuve change la question : {blueprint.primary_question}"
    if role == "DECISION" and shot_order == shot_count:
        return "Aucun coût sans témoin. Aucune autorité sans révocation."
    if role == "CLIMAX" and shot_order == shot_count:
        return blueprint.irreversible_change
    if role == "TAG" and shot_order == shot_count:
        return blueprint.hook
    return ""


def _build_generated_episode(blueprint: EpisodeBlueprint) -> AnimaticTimeline:
    scenes: list[AnimaticScene] = []
    shots: list[AnimaticShot] = []
    cursor = 0.0
    global_index = 0

    for scene_order, (role, label, scene_duration, shot_count) in enumerate(SCENE_LAYOUT, start=1):
        scene_start = cursor
        scene_end = round(scene_start + scene_duration, 6)
        unit = scene_duration / shot_count
        scene_id = f"E{blueprint.number:02d}-S{scene_order:02d}-{_slug(role)}"
        for shot_order in range(1, shot_count + 1):
            global_index += 1
            start = round(scene_start + (shot_order - 1) * unit, 6)
            end = scene_end if shot_order == shot_count else round(scene_start + shot_order * unit, 6)
            duration = round(end - start, 6)
            motif = blueprint.motifs[(global_index + scene_order) % len(blueprint.motifs)]
            action = ACTIONS[(global_index - 1) % len(ACTIONS)]
            shots.append(
                AnimaticShot(
                    shot_id=f"E{blueprint.number:02d}-S{scene_order:02d}-SH{shot_order:02d}",
                    scene_id=scene_id,
                    order=shot_order,
                    start_s=start,
                    end_s=end,
                    duration_s=duration,
                    purpose=PURPOSES[(shot_order - 1) % len(PURPOSES)],
                    framing=FRAMINGS[(global_index - 1) % len(FRAMINGS)],
                    camera_motion=CAMERA_MOTIONS[(global_index + scene_order - 2) % len(CAMERA_MOTIONS)],
                    subjects=SUBJECTS[(global_index + blueprint.number - 2) % len(SUBJECTS)],
                    caption=f"{label} — {motif} : {action}.",
                    dialogue=_dialogue(blueprint, role, shot_order, shot_count),
                    audio_cue=f"s1-e{blueprint.number:02d}-{role.lower().replace('_', '-')}",
                    intensity=round(min(1.0, 0.18 + blueprint.number * 0.035 + global_index / 190.0), 3),
                )
            )
        scene_change = (
            blueprint.irreversible_change
            if role == "CLIMAX"
            else f"{label} rend irréversible une partie de la question : {blueprint.primary_question}"
        )
        scenes.append(
            AnimaticScene(
                scene_id=scene_id,
                title=f"{label} — {blueprint.title}",
                order=scene_order,
                start_s=scene_start,
                end_s=scene_end,
                duration_s=scene_duration,
                objective=f"{label}: {blueprint.logline}",
                irreversible_change=scene_change,
            )
        )
        cursor = scene_end

    timeline = AnimaticTimeline(
        project_id=f"omega-anime-season/eighth-fire/s1/e{blueprint.number:02d}-r4",
        title=f"Le Huitième Feu — E{blueprint.number:02d} — {blueprint.title}",
        version="omega-anime-season/r4",
        duration_s=cursor,
        fps_reference=24,
        publication_state="private-draft",
        scenes=tuple(scenes),
        shots=tuple(shots),
        disclaimers=(
            "Épisode procédural basse fidélité; ce n'est pas une animation finale.",
            "Les voix et sons restent des guides synthétiques sans imitation de personne réelle.",
            "La cohérence logicielle ne prouve ni qualité artistique ni demande du public.",
            "Toute publication, licence, production ou promotion canonique exige une décision humaine.",
        ),
    )
    timeline.require_valid()
    return timeline


def build_eighth_fire_season_01_r4() -> SeasonPlan:
    """Return a validated 12×20-minute season with a single causal-debt chain."""

    episodes: list[SeasonEpisode] = []
    for blueprint in EPISODE_BLUEPRINTS:
        timeline = (
            build_eighth_fire_episode_01_r3()
            if blueprint.number == 1
            else _build_generated_episode(blueprint)
        )
        episodes.append(SeasonEpisode(blueprint=blueprint, timeline=timeline))

    season = SeasonPlan(
        season_id="omega-anime-season/eighth-fire/season-01-r4",
        title="Le Huitième Feu — Saison 1",
        version="omega-anime-season/r4",
        publication_state="private-draft",
        episodes=tuple(episodes),
        disclaimers=(
            "La saison est une architecture narrative et audiovisuelle procédurale, pas une production finale.",
            "Les douze épisodes nécessitent une direction artistique, une réécriture et une revue humaine.",
            "Aucun résultat synthétique ne démontre une audience, une rentabilité ou une clearance juridique.",
            "Les actions de publication, de licence, de casting, de financement et de fusion restent humaines.",
        ),
    )
    season.require_valid()
    return season
