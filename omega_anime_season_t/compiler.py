"""Compile the twelve-episode season, continuity ledgers and self-contained players."""

from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Any

from .models import SeasonEpisode, SeasonPlan


EPISODE_ARTIFACT_NAMES = frozenset(
    {
        "audio-cues.jsonl",
        "edit-decision-list.csv",
        "episode-outline.md",
        "manifest.json",
        "player.html",
        "subtitles.fr.vtt",
        "timeline.json",
    }
)

SEASON_ROOT_ARTIFACT_NAMES = frozenset(
    {
        "causal-debt-ledger.jsonl",
        "continuity-ledger.jsonl",
        "episode-index.jsonl",
        "manifest.json",
        "season-dashboard.html",
        "season-outline.md",
        "season.json",
    }
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vtt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def _write_vtt(episode: SeasonEpisode, path: Path) -> None:
    number = episode.blueprint.number
    lines = [
        "WEBVTT",
        "",
        f"NOTE Le Huitième Feu — Saison 1 — Épisode {number:02d} — guide FR privé",
        "",
    ]
    for index, shot in enumerate(episode.timeline.shots, start=1):
        text = shot.dialogue or f"[{shot.caption}]"
        lines.extend(
            [
                str(index),
                f"{_vtt_time(shot.start_s)} --> {_vtt_time(shot.end_s)}",
                text,
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_edl(episode: SeasonEpisode, path: Path) -> None:
    scene_orders = {scene.scene_id: scene.order for scene in episode.timeline.scenes}
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "episode",
                "shot_id",
                "scene_id",
                "scene_order",
                "shot_order",
                "start_s",
                "end_s",
                "duration_s",
                "framing",
                "camera_motion",
                "purpose",
            ]
        )
        for shot in episode.timeline.shots:
            writer.writerow(
                [
                    episode.blueprint.number,
                    shot.shot_id,
                    shot.scene_id,
                    scene_orders[shot.scene_id],
                    shot.order,
                    f"{shot.start_s:.6f}",
                    f"{shot.end_s:.6f}",
                    f"{shot.duration_s:.6f}",
                    shot.framing,
                    shot.camera_motion,
                    shot.purpose,
                ]
            )


def _write_audio(episode: SeasonEpisode, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for shot in episode.timeline.shots:
            handle.write(
                json.dumps(
                    {
                        "episode": episode.blueprint.number,
                        "shot_id": shot.shot_id,
                        "start_s": shot.start_s,
                        "duration_s": shot.duration_s,
                        "cue": shot.audio_cue,
                        "intensity": shot.intensity,
                        "guide_only": True,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )


def _write_episode_outline(episode: SeasonEpisode, path: Path) -> None:
    blueprint = episode.blueprint
    lines = [
        f"# Le Huitième Feu — E{blueprint.number:02d} — {blueprint.title}",
        "",
        "- Durée canonique : **20:00**",
        f"- Phase : **{blueprint.phase}**",
        f"- Lieu principal : **{blueprint.location}**",
        f"- Dette ouverte : `{blueprint.debt_opened}`",
        f"- Dette fermée : `{blueprint.debt_closed or 'aucune'}`",
        "- Statut : `private-draft`",
        "",
        "## Logline",
        "",
        blueprint.logline,
        "",
        "## Question",
        "",
        blueprint.primary_question,
        "",
        "## Découpage",
        "",
    ]
    for scene in episode.timeline.scenes:
        lines.extend(
            [
                f"### {scene.order:02d}. {scene.title} — {scene.duration_s:.0f} s",
                "",
                f"**Objectif :** {scene.objective}",
                "",
                f"**Changement :** {scene.irreversible_change}",
                "",
            ]
        )
    lines.extend(
        [
            "## Hook",
            "",
            blueprint.hook,
            "",
            "## Frontière OAK",
            "",
            "Ce fichier décrit un épisode procédural de préproduction, pas une animation finale ni une validation artistique, juridique ou commerciale.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _episode_player(episode: SeasonEpisode) -> str:
    timeline_payload = json.dumps(
        episode.timeline.to_dict(), ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    blueprint_payload = json.dumps(
        episode.blueprint.__dict__, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    safe_title = html.escape(episode.blueprint.title)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Le Huitième Feu — E{episode.blueprint.number:02d} — {safe_title}</title>
<style>
:root{{color-scheme:dark;font-family:Inter,system-ui,sans-serif}}*{{box-sizing:border-box}}body{{margin:0;background:#05070d;color:#eef6ff;min-height:100vh;display:grid;place-items:center}}main{{width:min(1220px,100vw);padding:18px}}header{{display:flex;justify-content:space-between;gap:16px;align-items:end;margin-bottom:12px}}h1{{margin:0;font-size:clamp(24px,4vw,44px)}}.badge{{border:1px solid #37718f;color:#8ee7ff;border-radius:999px;padding:6px 12px}}.stage{{position:relative;aspect-ratio:16/9;border:1px solid #26384e;border-radius:16px;overflow:hidden;background:#02040a}}canvas{{width:100%;height:100%;display:block}}.subtitle{{position:absolute;left:7%;right:7%;bottom:6%;text-align:center;font-size:clamp(17px,2.2vw,31px);font-weight:700;text-shadow:0 3px 12px #000}}.controls{{display:grid;grid-template-columns:auto 1fr auto auto;gap:12px;align-items:center;padding-top:14px}}button{{background:#16283b;color:#fff;border:1px solid #3c688c;border-radius:9px;padding:10px 16px}}input{{width:100%}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}}.panel{{background:#0b111c;border:1px solid #1e3044;border-radius:10px;padding:10px;color:#b8c8da}}@media(max-width:700px){{.meta{{grid-template-columns:1fr}}.controls{{grid-template-columns:auto 1fr}}}}
</style></head><body><main>
<header><div><h1>E{episode.blueprint.number:02d} — {safe_title}</h1><div>20:00 · 12 scènes · 114 plans · {html.escape(episode.blueprint.phase)}</div></div><div class="badge">PRIVATE-DRAFT · OAK</div></header>
<section class="stage"><canvas id="stage" width="1280" height="720"></canvas><div id="subtitle" class="subtitle"></div></section>
<section class="controls"><button id="play">Lecture</button><input id="seek" type="range" min="0" max="1200" step="0.01" value="0"><output id="time">00:00.00</output><button id="sound">Son guide</button></section>
<section class="meta"><div id="shot" class="panel"></div><div id="intent" class="panel"></div><div id="debt" class="panel"></div></section>
</main><script>
const TIMELINE={timeline_payload},BLUEPRINT={blueprint_payload};
const c=document.getElementById('stage'),x=c.getContext('2d'),seek=document.getElementById('seek'),play=document.getElementById('play'),sound=document.getElementById('sound'),subtitle=document.getElementById('subtitle'),time=document.getElementById('time'),shot=document.getElementById('shot'),intent=document.getElementById('intent'),debt=document.getElementById('debt');
let current=0,playing=false,last=0,audio=null,lastCue='';
function active(t){{return TIMELINE.shots.find(s=>t>=s.start_s&&t<s.end_s)||TIMELINE.shots.at(-1)}}
function sceneOrder(id){{return TIMELINE.scenes.find(s=>s.scene_id===id).order}}
function fmt(t){{const m=Math.floor(t/60),s=t-m*60;return String(m).padStart(2,'0')+':'+s.toFixed(2).padStart(5,'0')}}
function tone(s){{if(!audio)return;const o=audio.createOscillator(),g=audio.createGain();o.frequency.value=110+s.intensity*650;g.gain.setValueAtTime(.0001,audio.currentTime);g.gain.exponentialRampToValueAtTime(.03,audio.currentTime+.02);g.gain.exponentialRampToValueAtTime(.0001,audio.currentTime+.18);o.connect(g).connect(audio.destination);o.start();o.stop(audio.currentTime+.2)}}
function draw(t){{const s=active(t),order=sceneOrder(s.scene_id),h=(BLUEPRINT.number*31+order*47)%360,local=(t-s.start_s)/s.duration_s;x.fillStyle=`hsl(${{h}} 45% 7%)`;x.fillRect(0,0,1280,720);const g=x.createRadialGradient(640,350,20,640,350,680);g.addColorStop(0,`hsl(${{h}} 55% 21%)`);g.addColorStop(1,`hsl(${{h}} 45% 7%)`);x.fillStyle=g;x.fillRect(0,0,1280,720);x.strokeStyle=`hsl(${{(h+58)%360}} 90% 72%)`;x.lineWidth=2;x.globalAlpha=.72;for(let i=0;i<24;i++){{const a=i*2.399+order+local,r=75+(i%8)*64,px=640+Math.cos(a)*r,py=350+Math.sin(a*1.19)*r*.62;x.beginPath();x.moveTo(640,350);x.lineTo(px,py);x.stroke();x.beginPath();x.arc(px,py,3+(i%5),0,Math.PI*2);x.stroke()}}x.globalAlpha=1;const px=640+Math.sin(local*Math.PI*2)*85;x.fillStyle='#07101a';x.beginPath();x.arc(px,295,50,0,Math.PI*2);x.fill();x.fillRect(px-40,343,80,178);x.strokeStyle=`hsl(${{(h+58)%360}} 90% 72%)`;x.lineWidth=4;x.strokeRect(px-40,343,80,178);x.fillStyle='#fff';x.font='700 22px system-ui';x.fillText(s.shot_id,32,46);x.fillStyle='#b8c8da';x.font='17px system-ui';x.fillText(s.framing+' · '+s.camera_motion,32,75);subtitle.textContent=s.dialogue||'['+s.caption+']';shot.textContent=s.shot_id+' · scène '+order;intent.textContent=s.purpose+' · '+s.caption;debt.textContent='Dette ouverte: '+BLUEPRINT.debt_opened+' · fermée: '+(BLUEPRINT.debt_closed||'aucune');time.textContent=fmt(t);seek.value=t;if(audio&&lastCue!==s.shot_id){{lastCue=s.shot_id;tone(s)}}}}
function frame(now){{if(playing){{if(!last)last=now;current+=Math.min(.1,(now-last)/1000);last=now;if(current>=1200){{current=1200;playing=false;play.textContent='Rejouer'}}}}draw(current);requestAnimationFrame(frame)}}
play.onclick=()=>{{if(current>=1200)current=0;playing=!playing;last=0;play.textContent=playing?'Pause':'Lecture'}};seek.oninput=()=>{{current=Number(seek.value);lastCue='';draw(current)}};sound.onclick=()=>{{audio=audio||new AudioContext();audio.resume();sound.textContent='Son actif';lastCue=''}};draw(0);requestAnimationFrame(frame);
</script></body></html>\n"""


def _compile_episode(episode: SeasonEpisode, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    (output / "timeline.json").write_text(
        canonical_json(episode.timeline.to_dict()), encoding="utf-8"
    )
    _write_vtt(episode, output / "subtitles.fr.vtt")
    _write_edl(episode, output / "edit-decision-list.csv")
    _write_audio(episode, output / "audio-cues.jsonl")
    _write_episode_outline(episode, output / "episode-outline.md")
    (output / "player.html").write_text(_episode_player(episode), encoding="utf-8")

    files: dict[str, dict[str, Any]] = {}
    for path in sorted(output.iterdir()):
        if path.name == "manifest.json":
            continue
        files[path.name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    manifest_base = {
        "schema_version": "omega-anime-season/episode-r4",
        "episode": episode.blueprint.number,
        "title": episode.blueprint.title,
        "duration_s": episode.timeline.duration_s,
        "scene_count": len(episode.timeline.scenes),
        "shot_count": len(episode.timeline.shots),
        "publication_state": "private-draft",
        "external_network_dependencies": 0,
        "guide_audio_only": True,
        "files": files,
    }
    manifest = {
        **manifest_base,
        "manifest_sha256": hashlib.sha256(
            canonical_json(manifest_base).encode("utf-8")
        ).hexdigest(),
    }
    (output / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
    if {path.name for path in output.iterdir()} != EPISODE_ARTIFACT_NAMES:
        raise RuntimeError(f"unexpected episode artifact set in {output}")
    return manifest


def _write_episode_index(season: SeasonPlan, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for episode in season.episodes:
            handle.write(
                json.dumps(episode.summary(), ensure_ascii=False, sort_keys=True) + "\n"
            )


def _write_continuity(season: SeasonPlan, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for current, following in zip(season.episodes, season.episodes[1:]):
            record = {
                "from_episode": current.blueprint.number,
                "to_episode": following.blueprint.number,
                "hook": current.blueprint.hook,
                "entry_condition": following.blueprint.entry_condition,
                "matched": current.blueprint.hook == following.blueprint.entry_condition,
            }
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _write_debts(season: SeasonPlan, path: Path) -> None:
    active: set[str] = set()
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for episode in season.episodes:
            blueprint = episode.blueprint
            before = sorted(active)
            if blueprint.debt_closed:
                active.remove(blueprint.debt_closed)
            active.add(blueprint.debt_opened)
            record = {
                "episode": blueprint.number,
                "opened": blueprint.debt_opened,
                "closed": blueprint.debt_closed or None,
                "active_before": before,
                "active_after": sorted(active),
            }
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _write_season_outline(season: SeasonPlan, path: Path) -> None:
    lines = [
        "# Le Huitième Feu — Saison 1 — Ω-ANIME-SEASON-T∞ R4",
        "",
        "- **12 épisodes × 20 minutes**",
        "- **240 minutes / 14 400 secondes**",
        "- **144 scènes**",
        "- **1 368 plans**",
        "- Statut : `private-draft`",
        "",
        "## Épisodes",
        "",
    ]
    for episode in season.episodes:
        bp = episode.blueprint
        lines.extend(
            [
                f"### E{bp.number:02d} — {bp.title} — {bp.phase}",
                "",
                bp.logline,
                "",
                f"- **Question :** {bp.primary_question}",
                f"- **Changement irréversible :** {bp.irreversible_change}",
                f"- **Dette ouverte :** `{bp.debt_opened}`",
                f"- **Dette fermée :** `{bp.debt_closed or 'aucune'}`",
                f"- **Hook :** {bp.hook}",
                "",
            ]
        )
    lines.extend(
        [
            "## Frontière OAK",
            "",
            "Cette saison démontre une architecture narrative, temporelle et logicielle reproductible. Elle ne démontre pas une animation finale, une direction artistique validée, une audience, un financement ou une clearance juridique complète.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _season_dashboard(season: SeasonPlan) -> str:
    payload = json.dumps(season.to_dict(), ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Le Huitième Feu — Saison 1</title>
<style>:root{{color-scheme:dark;font-family:Inter,system-ui,sans-serif}}body{{margin:0;background:#060910;color:#edf6ff}}main{{max-width:1200px;margin:auto;padding:28px}}h1{{font-size:clamp(30px,5vw,62px);margin:0}}.summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}.metric,.card{{background:#0d1522;border:1px solid #20344d;border-radius:14px;padding:16px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.phase{{color:#89e7ff}}.debt{{font-family:monospace;color:#ffc477}}.hook{{color:#c8d6e5}}@media(max-width:800px){{.grid,.summary{{grid-template-columns:1fr}}}}</style></head>
<body><main><h1>Le Huitième Feu — Saison 1</h1><p>Ω-ANIME-SEASON-T∞ R4 · private-draft · aucune dépendance réseau</p><section class="summary"><div class="metric"><b>12</b><br>épisodes</div><div class="metric"><b>240</b><br>minutes</div><div class="metric"><b>144</b><br>scènes</div><div class="metric"><b>1 368</b><br>plans</div></section><section id="episodes" class="grid"></section></main>
<script>const SEASON={payload};const root=document.getElementById('episodes');for(const e of SEASON.episodes){{const card=document.createElement('article');card.className='card';card.innerHTML=`<div class="phase">E${{String(e.number).padStart(2,'0')}} · ${{e.phase}}</div><h2>${{e.title}}</h2><p>${{e.logline}}</p><p><b>Question</b><br>${{e.primary_question}}</p><p class="debt">+ ${{e.debt_opened}}<br>− ${{e.debt_closed||'aucune'}}</p><p class="hook"><b>Hook</b><br>${{e.hook}}</p>`;root.appendChild(card)}}</script></body></html>\n"""


def compile_season_bundle(season: SeasonPlan, output_dir: str | Path) -> dict[str, Any]:
    """Compile 12 episode bundles plus season ledgers into exactly 91 files."""

    season.require_valid()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episodes_root = output / "episodes"
    episodes_root.mkdir(parents=True, exist_ok=True)

    episode_manifests: list[dict[str, Any]] = []
    for episode in season.episodes:
        episode_dir = episodes_root / f"episode-{episode.blueprint.number:02d}"
        episode_manifests.append(_compile_episode(episode, episode_dir))

    (output / "season.json").write_text(canonical_json(season.to_dict()), encoding="utf-8")
    _write_episode_index(season, output / "episode-index.jsonl")
    _write_continuity(season, output / "continuity-ledger.jsonl")
    _write_debts(season, output / "causal-debt-ledger.jsonl")
    _write_season_outline(season, output / "season-outline.md")
    (output / "season-dashboard.html").write_text(
        _season_dashboard(season), encoding="utf-8"
    )

    tracked_files: dict[str, dict[str, Any]] = {}
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path == output / "manifest.json":
            continue
        rel = path.relative_to(output).as_posix()
        tracked_files[rel] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}

    manifest_base = {
        "schema_version": "omega-anime-season/r4",
        "season_id": season.season_id,
        "episode_count": len(season.episodes),
        "total_duration_s": season.total_duration_s,
        "total_scenes": season.total_scenes,
        "total_shots": season.total_shots,
        "artifact_count": len(tracked_files) + 1,
        "episode_artifact_count": len(episode_manifests) * len(EPISODE_ARTIFACT_NAMES),
        "publication_state": season.publication_state,
        "external_network_dependencies": 0,
        "guide_audio_only": True,
        "files": tracked_files,
    }
    manifest = {
        **manifest_base,
        "manifest_sha256": hashlib.sha256(
            canonical_json(manifest_base).encode("utf-8")
        ).hexdigest(),
    }
    (output / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")

    root_names = {path.name for path in output.iterdir() if path.is_file()}
    if root_names != SEASON_ROOT_ARTIFACT_NAMES:
        raise RuntimeError(f"unexpected season root artifact set: {sorted(root_names)}")
    if manifest["artifact_count"] != 91:
        raise RuntimeError(f"expected 91 artifacts, got {manifest['artifact_count']}")
    return manifest
