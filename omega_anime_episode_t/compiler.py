"""Compile a deterministic, self-contained 20-minute episode bundle."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
from pathlib import Path
from typing import Any

from omega_anime_animatic_t.models import AnimaticTimeline


EPISODE_ARTIFACT_NAMES = frozenset(
    {
        "audio-cues.jsonl",
        "edit-decision-list.csv",
        "episode-01.html",
        "episode-outline.md",
        "manifest.json",
        "storyboard-contact-sheet.svg",
        "subtitles.fr.vtt",
        "timeline.json",
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


def _write_vtt(timeline: AnimaticTimeline, path: Path) -> None:
    lines = ["WEBVTT", "", "NOTE Le Huitième Feu — Épisode 1 — guide FR privé", ""]
    for index, shot in enumerate(timeline.shots, start=1):
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


def _write_edl(timeline: AnimaticTimeline, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
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
        scene_orders = {scene.scene_id: scene.order for scene in timeline.scenes}
        for shot in timeline.shots:
            writer.writerow(
                [
                    shot.shot_id,
                    shot.scene_id,
                    scene_orders[shot.scene_id],
                    shot.order,
                    f"{shot.start_s:.3f}",
                    f"{shot.end_s:.3f}",
                    f"{shot.duration_s:.3f}",
                    shot.framing,
                    shot.camera_motion,
                    shot.purpose,
                ]
            )


def _write_audio(timeline: AnimaticTimeline, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for shot in timeline.shots:
            handle.write(
                json.dumps(
                    {
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


def _scene_color(order: int) -> tuple[str, str, str]:
    palettes = (
        ("#07111f", "#17324a", "#60d7ff"),
        ("#090d20", "#26205c", "#7fffd4"),
        ("#121321", "#563a26", "#ffcc66"),
        ("#170c19", "#56213e", "#ff5c8a"),
        ("#05040e", "#32185c", "#d99cff"),
        ("#071611", "#1d4d3b", "#8fffc1"),
        ("#171007", "#5b3a16", "#ffd17a"),
        ("#0b0b18", "#25255a", "#a9b5ff"),
        ("#19090d", "#5c202d", "#ff8fa3"),
        ("#07151a", "#184651", "#7be8ff"),
        ("#120a1a", "#44215a", "#e5a0ff"),
        ("#080808", "#303030", "#ffffff"),
    )
    return palettes[(order - 1) % len(palettes)]


def _write_contact_sheet(timeline: AnimaticTimeline, path: Path) -> None:
    columns = 6
    rows = math.ceil(len(timeline.shots) / columns)
    width = 1800
    gap = 14
    card_h = 190
    height = 120 + rows * (card_h + gap) + gap
    card_w = (width - gap * (columns + 1)) / columns
    scene_orders = {scene.scene_id: scene.order for scene in timeline.scenes}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#070a10"/>',
        '<text x="36" y="48" fill="#ffffff" font-family="sans-serif" font-size="30" font-weight="700">Le Huitième Feu — Épisode 1 — Storyboard R3</text>',
        f'<text x="36" y="82" fill="#9fb2c7" font-family="sans-serif" font-size="17">{len(timeline.shots)} plans · {timeline.duration_s / 60:.0f} minutes · {len(timeline.scenes)} scènes · private-draft</text>',
    ]
    for index, shot in enumerate(timeline.shots):
        row, column = divmod(index, columns)
        x = gap + column * (card_w + gap)
        y = 105 + gap + row * (card_h + gap)
        bg, middle, accent = _scene_color(scene_orders[shot.scene_id])
        caption = html.escape(shot.caption[:48])
        parts.extend(
            [
                f'<g data-shot="{html.escape(shot.shot_id)}">',
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{card_w:.1f}" height="{card_h}" rx="10" fill="{bg}" stroke="{accent}" stroke-width="2"/>',
                f'<rect x="{x + 10:.1f}" y="{y + 10:.1f}" width="{card_w - 20:.1f}" height="92" rx="7" fill="{middle}"/>',
                f'<circle cx="{x + card_w * .5:.1f}" cy="{y + 55:.1f}" r="{16 + index % 5 * 3}" fill="none" stroke="{accent}" stroke-width="3"/>',
                f'<path d="M {x + 22:.1f} {y + 88:.1f} Q {x + card_w * .5:.1f} {y + 18:.1f}, {x + card_w - 22:.1f} {y + 86:.1f}" fill="none" stroke="{accent}" stroke-width="2" opacity=".75"/>',
                f'<text x="{x + 12:.1f}" y="{y + 122:.1f}" fill="#ffffff" font-family="monospace" font-size="13">{html.escape(shot.shot_id)}</text>',
                f'<text x="{x + 12:.1f}" y="{y + 145:.1f}" fill="{accent}" font-family="sans-serif" font-size="12">{caption}</text>',
                f'<text x="{x + 12:.1f}" y="{y + 170:.1f}" fill="#91a4b9" font-family="monospace" font-size="12">{shot.start_s:.1f}s → {shot.end_s:.1f}s</text>',
                "</g>",
            ]
        )
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_outline(timeline: AnimaticTimeline, path: Path) -> None:
    lines = [
        "# Le Huitième Feu — Épisode 1 : La dette du réseau",
        "",
        "- Durée canonique : **20:00**",
        f"- Scènes : **{len(timeline.scenes)}**",
        f"- Plans : **{len(timeline.shots)}**",
        "- Statut : `private-draft`",
        "- Ouverture froide : les 180 secondes de R2 sont préservées.",
        "",
        "## Découpage",
        "",
    ]
    for scene in timeline.scenes:
        lines.extend(
            [
                f"### {scene.order:02d}. {scene.title} — {scene.duration_s:.0f} s",
                "",
                f"**Objectif :** {scene.objective}",
                "",
                f"**Changement irréversible :** {scene.irreversible_change}",
                "",
            ]
        )
    lines.extend(
        [
            "## Frontière OAK",
            "",
            "Ce bundle prouve une structure temporelle reproductible de vingt minutes.",
            "Il ne prouve pas une qualité artistique finale, une audience, un budget, une clearance juridique ou une faisabilité de production professionnelle.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _render_html(timeline: AnimaticTimeline) -> str:
    payload = json.dumps(timeline.to_dict(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    safe_title = html.escape(timeline.title)
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title}</title>
<style>
:root{{color-scheme:dark;font-family:Inter,system-ui,sans-serif}}*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;background:#05070d;color:#eef6ff;display:grid;place-items:center}}main{{width:min(1220px,100vw);padding:18px}}header{{display:flex;justify-content:space-between;align-items:end;gap:16px;margin-bottom:12px}}h1{{margin:0;font-size:clamp(23px,4vw,44px)}}.badge{{color:#89e7ff;border:1px solid #2c738c;border-radius:999px;padding:6px 12px}}.stage{{position:relative;aspect-ratio:16/9;border:1px solid #26384e;border-radius:16px;overflow:hidden;background:#02040a;box-shadow:0 20px 80px #000a}}canvas{{width:100%;height:100%;display:block}}.subtitle{{position:absolute;left:7%;right:7%;bottom:6%;text-align:center;font-size:clamp(17px,2.3vw,32px);font-weight:700;text-shadow:0 3px 12px #000}}.controls{{display:grid;grid-template-columns:auto 1fr auto auto;gap:12px;align-items:center;padding-top:14px}}button{{background:#16283b;color:white;border:1px solid #3c688c;border-radius:9px;padding:10px 16px;cursor:pointer}}input[type=range]{{width:100%}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px;color:#a9bdd2;font-size:14px}}.panel{{background:#0b111c;border:1px solid #1e3044;border-radius:10px;padding:10px}}@media(max-width:700px){{.controls{{grid-template-columns:auto 1fr}}.meta{{grid-template-columns:1fr}}}}
</style>
</head>
<body><main>
<header><div><h1>{safe_title}</h1><div>Épisode canonique · 20:00 · 114 plans</div></div><div class="badge">PRIVATE-DRAFT · OAK</div></header>
<section class="stage"><canvas id="stage" width="1280" height="720"></canvas><div id="subtitle" class="subtitle"></div></section>
<section class="controls"><button id="play">Lecture</button><input id="seek" type="range" min="0" step="0.01" value="0"><output id="time">00:00.00</output><button id="sound">Son guide</button></section>
<section class="meta"><div id="shot" class="panel"></div><div id="intent" class="panel"></div><div id="status" class="panel"></div></section>
</main><script>
const TIMELINE={payload};
const canvas=document.getElementById('stage'),ctx=canvas.getContext('2d'),seek=document.getElementById('seek'),play=document.getElementById('play'),sound=document.getElementById('sound');
const subtitle=document.getElementById('subtitle'),timeOut=document.getElementById('time'),shotOut=document.getElementById('shot'),intentOut=document.getElementById('intent'),statusOut=document.getElementById('status');
seek.max=TIMELINE.duration_s;let playing=false,current=0,last=0,audio=null,lastCue='';
function active(t){{return TIMELINE.shots.find(s=>t>=s.start_s&&t<s.end_s)||TIMELINE.shots.at(-1)}}
function sceneOrder(id){{return TIMELINE.scenes.find(s=>s.scene_id===id).order}}
function fmt(t){{const m=Math.floor(t/60),s=t-m*60;return String(m).padStart(2,'0')+':'+s.toFixed(2).padStart(5,'0')}}
function palette(order){{const hue=(order*47)%360;return [`hsl(${{hue}} 45% 7%)`,`hsl(${{hue}} 55% 20%)`,`hsl(${{(hue+55)%360}} 90% 72%)`]}}
function tone(s){{if(!audio)return;const o=audio.createOscillator(),g=audio.createGain();o.type='sine';o.frequency.value=120+s.intensity*600;g.gain.setValueAtTime(.0001,audio.currentTime);g.gain.exponentialRampToValueAtTime(.035,audio.currentTime+.02);g.gain.exponentialRampToValueAtTime(.0001,audio.currentTime+.19);o.connect(g).connect(audio.destination);o.start();o.stop(audio.currentTime+.2)}}
function draw(t){{const s=active(t),order=sceneOrder(s.scene_id),p=palette(order),local=(t-s.start_s)/s.duration_s;ctx.fillStyle=p[0];ctx.fillRect(0,0,1280,720);const grad=ctx.createRadialGradient(640,350,20,640,350,690);grad.addColorStop(0,p[1]);grad.addColorStop(1,p[0]);ctx.fillStyle=grad;ctx.fillRect(0,0,1280,720);ctx.strokeStyle=p[2];ctx.lineWidth=2;ctx.globalAlpha=.7;for(let i=0;i<22;i++){{const a=i*2.399+order+local;const r=70+(i%7)*68;const x=640+Math.cos(a)*r,y=350+Math.sin(a*1.21)*r*.62;ctx.beginPath();ctx.moveTo(640,350);ctx.lineTo(x,y);ctx.stroke();ctx.beginPath();ctx.arc(x,y,3+(i%5),0,Math.PI*2);ctx.stroke()}}ctx.globalAlpha=1;const px=640+Math.sin(local*Math.PI*2)*80;ctx.fillStyle='#07101a';ctx.beginPath();ctx.arc(px,300,52,0,Math.PI*2);ctx.fill();ctx.fillRect(px-42,350,84,180);ctx.strokeStyle=p[2];ctx.lineWidth=4;ctx.strokeRect(px-42,350,84,180);ctx.fillStyle='#eef6ff';ctx.font='700 22px system-ui';ctx.fillText(s.shot_id,32,46);ctx.font='18px system-ui';ctx.fillStyle=p[2];ctx.fillText(s.framing+' · '+s.camera_motion,32,76);ctx.textAlign='right';ctx.fillStyle='#b7c8da';ctx.fillText(fmt(s.start_s)+' → '+fmt(s.end_s),1248,46);ctx.textAlign='left';subtitle.textContent=s.dialogue||'['+s.caption+']';shotOut.textContent=s.shot_id+' · scène '+order+'/12';intentOut.textContent=s.purpose+' · '+s.caption;statusOut.textContent=s.audio_cue+' · intensité '+s.intensity.toFixed(2);timeOut.textContent=fmt(t);seek.value=t;if(audio&&lastCue!==s.shot_id){{lastCue=s.shot_id;tone(s)}}}}
function frame(now){{if(playing){{if(!last)last=now;current+=Math.min(.1,(now-last)/1000);last=now;if(current>=TIMELINE.duration_s){{current=TIMELINE.duration_s;playing=false;play.textContent='Rejouer'}}}}draw(current);requestAnimationFrame(frame)}}
play.onclick=()=>{{if(current>=TIMELINE.duration_s)current=0;playing=!playing;last=0;play.textContent=playing?'Pause':'Lecture'}};seek.oninput=()=>{{current=Number(seek.value);lastCue='';draw(current)}};sound.onclick=()=>{{audio=audio||new AudioContext();audio.resume();sound.textContent='Son actif';lastCue=''}};draw(0);requestAnimationFrame(frame);
</script></body></html>
"""


def compile_episode_bundle(timeline: AnimaticTimeline, output_dir: str | Path) -> dict[str, Any]:
    timeline.require_valid()
    if timeline.duration_s != 1200.0:
        raise ValueError("episode must be exactly 1200 seconds")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "timeline.json").write_text(canonical_json(timeline.to_dict()), encoding="utf-8")
    _write_audio(timeline, output / "audio-cues.jsonl")
    _write_edl(timeline, output / "edit-decision-list.csv")
    _write_vtt(timeline, output / "subtitles.fr.vtt")
    _write_contact_sheet(timeline, output / "storyboard-contact-sheet.svg")
    _write_outline(timeline, output / "episode-outline.md")
    (output / "episode-01.html").write_text(_render_html(timeline), encoding="utf-8")

    files: dict[str, dict[str, Any]] = {}
    for path in sorted(output.iterdir()):
        if path.name == "manifest.json":
            continue
        files[path.name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    base = {
        "schema_version": "omega-anime-episode/r3",
        "project_id": timeline.project_id,
        "publication_state": timeline.publication_state,
        "duration_s": timeline.duration_s,
        "duration_minutes": timeline.duration_s / 60.0,
        "scene_count": len(timeline.scenes),
        "shot_count": len(timeline.shots),
        "cold_open_duration_s": 180.0,
        "artifact_count": len(EPISODE_ARTIFACT_NAMES),
        "self_contained_browser_player": True,
        "external_network_dependencies": 0,
        "guide_audio_only": True,
        "files": files,
    }
    digest = hashlib.sha256(canonical_json(base).encode("utf-8")).hexdigest()
    manifest = {**base, "manifest_sha256": digest}
    (output / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
    actual = {path.name for path in output.iterdir()}
    if actual != EPISODE_ARTIFACT_NAMES:
        raise RuntimeError(f"unexpected episode artifacts: {sorted(actual)}")
    return manifest
