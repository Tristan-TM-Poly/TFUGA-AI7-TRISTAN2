"""Build the R2 animatic timeline from the validated R1 shot graph."""

from __future__ import annotations

from omega_anime_studio_t import build_eighth_fire_r1

from .models import AnimaticScene, AnimaticShot, AnimaticTimeline


DIALOGUE: dict[str, str] = {
    "S01-NOISE-SH06": "Le bruit revient au même endroit.",
    "S02-NETWORK-SH04": "Je ne sais pas si je le vois… ou si je le projette.",
    "S02-NETWORK-SH06": "Un seul nœud. Le minimum.",
    "S03-CORRECTION-SH03": "Maintenant.",
    "S04-DISPLACEMENT-SH04": "Je n’ai rien supprimé. J’ai déplacé la contrainte.",
    "S05-EIGHTH-FIRE-SH03": "Tu n’as pas découvert une nouvelle énergie.",
    "S05-EIGHTH-FIRE-SH04": "Tu as touché la structure qui décide où l’énergie peut aller.",
    "S05-EIGHTH-FIRE-SH06": "Et maintenant, elle te voit.",
}


def _caption(shot: object) -> str:
    revealed = tuple(getattr(shot, "information_revealed"))
    if revealed:
        return str(revealed[0])
    return str(getattr(shot, "purpose")).replace("-", " ")


def _audio_cue(scene_id: str, purpose: str, intensity: float) -> str:
    if scene_id == "S01-NOISE":
        return "lab-hum+correlated-pulse" if intensity > 0.45 else "lab-hum"
    if scene_id == "S02-NETWORK":
        return "causal-filament"
    if scene_id == "S03-CORRECTION":
        return "control-tension+relay-click"
    if scene_id == "S04-DISPLACEMENT":
        return "grid-desync+low-impact"
    if purpose in {"name phenomenon", "define distinction", "end hook"}:
        return "observer-voice+eighth-fire-motif"
    return "eighth-fire-motif"


def build_eighth_fire_animatic_r2() -> AnimaticTimeline:
    """Convert the canonical R1 project to a contiguous 180-second timeline."""

    project = build_eighth_fire_r1()
    project.require_valid()

    shots: list[AnimaticShot] = []
    scenes: list[AnimaticScene] = []
    cursor = 0.0
    global_index = 0

    for scene in sorted(project.scenes, key=lambda item: item.order):
        scene_start = cursor
        scene_shots = sorted(
            (shot for shot in project.shots if shot.scene_id == scene.scene_id),
            key=lambda item: item.order,
        )
        for shot in scene_shots:
            global_index += 1
            start = round(cursor, 6)
            end = round(start + float(shot.duration_s), 6)
            intensity = round(min(1.0, 0.18 + global_index / 38.0), 3)
            shots.append(
                AnimaticShot(
                    shot_id=shot.shot_id,
                    scene_id=shot.scene_id,
                    order=shot.order,
                    start_s=start,
                    end_s=end,
                    duration_s=float(shot.duration_s),
                    purpose=shot.purpose,
                    framing=shot.framing,
                    camera_motion=shot.camera_motion,
                    subjects=tuple(shot.subject_ids),
                    caption=_caption(shot),
                    dialogue=DIALOGUE.get(shot.shot_id, ""),
                    audio_cue=_audio_cue(shot.scene_id, shot.purpose, intensity),
                    intensity=intensity,
                )
            )
            cursor = end
        scenes.append(
            AnimaticScene(
                scene_id=scene.scene_id,
                title=scene.title,
                order=scene.order,
                start_s=scene_start,
                end_s=cursor,
                duration_s=float(scene.duration_target_s),
                objective=scene.objective,
                irreversible_change=scene.irreversible_change,
            )
        )

    timeline = AnimaticTimeline(
        project_id="omega-anime-animatic/eighth-fire/pilot-r2",
        title="Le Huitième Feu — Animatique R2",
        version="omega-anime-animatic/r2",
        duration_s=round(cursor, 6),
        fps_reference=24,
        publication_state="private-draft",
        scenes=tuple(scenes),
        shots=tuple(shots),
        disclaimers=(
            "Animatique procédurale basse fidélité; ce n’est pas une animation finale.",
            "Les voix et sons sont des guides synthétiques sans imitation de personne réelle.",
            "La cohérence logicielle ne prouve ni qualité artistique ni demande du public.",
        ),
    )
    timeline.require_valid()
    return timeline
