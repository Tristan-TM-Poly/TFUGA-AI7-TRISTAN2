"""Canonical original look-development bible for Le Huitième Feu season one."""

from __future__ import annotations

from omega_anime_season_t import build_eighth_fire_season_01_r4

from .models import CharacterDesign, EpisodeLook, LookdevBible


CHARACTERS = (
    CharacterDesign(
        character_id="CHAR-TRISTAN",
        name="Tristan",
        role="protagoniste et opérateur de bifurcations",
        silhouette_signature="verticale étroite, épaules retenues, mains géométriques",
        shape_language="rectangles interrompus par un seul arc lumineux",
        body_ratio="7.5 têtes; centre de gravité haut",
        palette=("#07111F", "#17324A", "#2E6684", "#B8E9F6", "#F4FBFF"),
        accent_color="#60D7FF",
        motion_rules=(
            "immobilité avant décision",
            "regard périphérique avant mouvement du corps",
            "mains visibles seulement lorsqu'une limite est acceptée",
        ),
        expressions=("analyse", "doute", "surcharge", "responsabilité", "refus", "résolution"),
        voice_register="médium clair, peu projeté",
        voice_tempo="phrases courtes; ralentissement sur les distinctions",
        voice_boundary="aucune imitation d'une personne réelle; voix guide synthétique seulement",
    ),
    CharacterDesign(
        character_id="CHAR-OBSERVATRICE",
        name="L'Observatrice",
        role="antagoniste épistémique et gardienne des futurs",
        silhouette_signature="triangle inversé immobile, visage négatif, cape sans vent",
        shape_language="triangles fermés et ellipses absentes",
        body_ratio="8.2 têtes; verticalité irréelle",
        palette=("#08040F", "#24113D", "#5D2D78", "#D8A5FF", "#FFF7FF"),
        accent_color="#D99CFF",
        motion_rules=(
            "entrée depuis le hors-champ plutôt que marche visible",
            "tête parfaitement stable pendant les déplacements",
            "un geste unique par scène, toujours irréversible",
        ),
        expressions=("diagnostic", "calcul", "déception", "curiosité", "peur contenue", "consentement"),
        voice_register="grave douce, sans emphase",
        voice_tempo="constats réguliers séparés par des silences longs",
        voice_boundary="ne pas cloner ou évoquer une interprète réelle",
    ),
    CharacterDesign(
        character_id="CHAR-CREANCIER",
        name="Le Créancier",
        role="incarnation procédurale des dettes déplacées",
        silhouette_signature="masse basse asymétrique, bras multiples suggérés par l'ombre",
        shape_language="hexagones incomplets et courbes de facture",
        body_ratio="6.4 têtes; largeur supérieure à la hauteur apparente",
        palette=("#160B08", "#4A2118", "#8B4B25", "#F0B85B", "#FFF0C7"),
        accent_color="#FFCC66",
        motion_rules=(
            "aucun pas sans contre-mouvement du décor",
            "les extrémités apparaissent après leur ombre",
            "proximité exprimée par compression de perspective",
        ),
        expressions=("réclamation", "patience", "mépris", "faim", "surprise", "solde"),
        voice_register="polyphonie basse non humaine",
        voice_tempo="syllabes longues suivies de chiffres secs",
        voice_boundary="construction originale; aucune banque de voix identifiable",
    ),
    CharacterDesign(
        character_id="CHAR-TEMOIN-ZERO",
        name="Témoin Zéro",
        role="preuve vivante qu'une observation peut survivre sans observateur",
        silhouette_signature="cercle central fragmenté, membres radiaux de longueurs inégales",
        shape_language="cercles ouverts et lignes radiales",
        body_ratio="non anthropométrique; rayon variable",
        palette=("#050A0C", "#12343B", "#247783", "#93F3EF", "#F2FFFF"),
        accent_color="#7FFFD4",
        motion_rules=(
            "rotation sans translation lors de l'écoute",
            "translation par sauts de douze images",
            "silhouette complète uniquement dans les reflets",
        ),
        expressions=("absence", "écho", "reconnaissance", "alarme", "choix", "présence"),
        voice_register="harmoniques claires sans genre assigné",
        voice_tempo="mots isolés répétés avec décalage",
        voice_boundary="timbre synthétique abstrait; aucune imitation humaine",
    ),
)


PALETTES = (
    ("#050912", "#0D2334", "#17506A", "#3BA7C4", "#9BEAFF", "#F5FCFF"),
    ("#070612", "#17143A", "#332A73", "#6C63C8", "#A9B5FF", "#F8F9FF"),
    ("#080B0B", "#15302E", "#25675F", "#4DB9A8", "#A7F2DF", "#F5FFFC"),
    ("#110807", "#3B1714", "#7A3027", "#D0634D", "#FFB096", "#FFF7F2"),
    ("#0D0B08", "#392A16", "#755522", "#C89B3E", "#F3D889", "#FFFBEF"),
    ("#10080A", "#3F1721", "#7D2941", "#CF5476", "#FFACC3", "#FFF5F8"),
    ("#08050F", "#28123F", "#562779", "#A05BC4", "#DDB2F5", "#FFF7FF"),
    ("#08090F", "#202840", "#3C5184", "#718FCE", "#B8C9FF", "#F8FAFF"),
    ("#040C10", "#0E3544", "#16677E", "#2FA9BD", "#8DE7EF", "#F2FEFF"),
    ("#070707", "#242424", "#4D4D4D", "#898989", "#D2D2D2", "#FFFFFF"),
    ("#0B0710", "#321542", "#6B2B79", "#BD5CC5", "#EDA7EC", "#FFF5FF"),
    ("#05040A", "#211337", "#4B286E", "#A358B0", "#F0B76A", "#FFF8E7"),
)

LIGHT_KEYS = (
    "cyan analytique latéral", "violet stationnaire zénithal", "vert absence sous-exposé",
    "rouge mémoire pulsée", "ambre urbain rémanent", "magenta tribunal bifurqué",
    "violet incarné contre-jour", "bleu permission quadrillé", "cyan abyssal volumétrique",
    "gris sans témoin", "pourpre correction terminale", "or-violet du Huitième Feu",
)

COMPOSITIONS = (
    "sujet au tiers gauche, réseau envahissant le vide droit",
    "axe central interdit par une porte décalée",
    "cadre dans le cadre avec nœud aveugle hors foyer",
    "symétrie rompue exactement à douze images",
    "mémoire du plan précédent conservée dans un reflet",
    "champ-contrechamp sans partager la même ligne d'horizon",
    "contre-jour où l'antagoniste possède le fond",
    "quadrillage de permissions qui coupe les visages sans les masquer",
    "profondeur en trois couches, horizon sous-marin oblique",
    "plans fixes dont les objets changent sans témoin",
    "convergence diagonale vers une correction impossible",
    "cercle ouvert autour de Tristan, centre volontairement vide",
)

MOTIFS = (
    "filament cyan interrompu", "siège vide numéroté", "occlusion hexagonale", "horloge sans douze secondes",
    "fenêtres qui se souviennent", "facture en ombre", "visage dans la lumière négative", "sceaux de permission",
    "réseau abyssal", "reflet sans source", "ligne corrigée qui saigne", "flamme à huit branches",
)

CURVES = (
    (0.18, 0.31, 0.47, 0.68, 0.82, 0.72), (0.22, 0.38, 0.51, 0.63, 0.78, 0.88),
    (0.30, 0.42, 0.36, 0.62, 0.81, 0.76), (0.25, 0.55, 0.44, 0.71, 0.91, 0.83),
    (0.20, 0.37, 0.59, 0.73, 0.66, 0.86), (0.34, 0.48, 0.67, 0.72, 0.94, 0.79),
    (0.28, 0.46, 0.64, 0.58, 0.84, 0.92), (0.31, 0.52, 0.75, 0.69, 0.88, 0.95),
    (0.19, 0.35, 0.57, 0.77, 0.90, 0.82), (0.12, 0.29, 0.48, 0.70, 0.87, 0.96),
    (0.39, 0.61, 0.55, 0.78, 0.96, 0.89), (0.26, 0.49, 0.72, 0.91, 1.00, 0.84),
)


def build_eighth_fire_lookdev_r5() -> LookdevBible:
    season = build_eighth_fire_season_01_r4()
    season.require_valid()
    episodes = tuple(
        EpisodeLook(
            episode_number=episode.blueprint.number,
            title=episode.blueprint.title,
            phase=episode.blueprint.phase,
            palette=PALETTES[index],
            light_key=LIGHT_KEYS[index],
            composition_rule=COMPOSITIONS[index],
            forbidden_composition="centrage décoratif sans information causale",
            visual_motif=MOTIFS[index],
            emotional_curve=CURVES[index],
            target_contrast_ratio=7.0,
            camera_entropy_target=round(0.34 + index * 0.035, 3),
        )
        for index, episode in enumerate(season.episodes)
    )
    bible = LookdevBible(
        project_id="omega-anime-lookdev/eighth-fire/season-01-r5",
        style_id="STYLE-NOIR-MYCELIEN-CAUSAL-R5",
        style_name="Noir mycélien causal",
        version="omega-anime-lookdev/r5",
        publication_state="private-draft",
        originality_statement=(
            "Système visuel original construit à partir d'invariants géométriques, lumineux et causaux; "
            "aucune imitation d'un artiste vivant, d'un studio ou d'une œuvre existante."
        ),
        global_invariants=(
            "chaque effet lumineux révèle une relation causale",
            "aucun réseau décoratif sans source et destination lisibles",
            "silhouettes principales reconnaissables en aplat noir",
            "palette sombre avec accent limité à quinze pour cent de l'image",
            "un changement irréversible possède un changement de lumière irréversible",
            "la caméra ne bouge que pour révéler, choisir ou payer une dette",
            "les reflets peuvent conserver une information perdue par le monde direct",
            "les interfaces affichent incertitude, provenance et coût de correction",
            "les scènes d'action gardent une géographie compréhensible",
            "les plans contemplatifs doivent produire une information nouvelle",
        ),
        forbidden_defaults=(
            "imitation d'un style d'artiste ou de studio nommé",
            "génération de visage photoréaliste d'une personne réelle",
            "lumière néon gratuite sans fonction narrative",
            "caméra tremblée pour masquer une géographie incohérente",
            "personnage générique interchangeable entre épisodes",
            "musique ou voix non licenciée",
            "publication automatique des feuilles de développement",
            "confusion entre style frame et animation finale",
        ),
        characters=CHARACTERS,
        episodes=episodes,
    )
    bible.require_valid()
    return bible
