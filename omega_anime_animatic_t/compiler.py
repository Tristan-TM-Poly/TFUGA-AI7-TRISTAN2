"""Deterministic R2 compiler: timeline, player, storyboard, subtitles and receipts."""

from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Any

from .models import AnimaticTimeline


ARTIFACT_NAMES = frozenset(
    {
        "audio-cues.jsonl",
        "edit-decision-list.csv",
        "eighth-fire-animatic.html",
        "manifest.json",
        "report.md",
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


def _subtitle_text(shot: Any) -> str:
    if shot.dialogue:
        return shot.dialogue
    return f"[{shot.caption}]"


def _write_vtt(timeline: AnimaticTimeline, path: Path) -> None:
    lines = ["WEBVTT", "", "NOTE Le Huitième Feu — guide FR privé", ""]
    for index, shot in enumerate(timeline.shots, start=1):
        lines.extend(
            [
                str(index),
                f"{_vtt_time(shot.start_s)} --> {_vtt_time(shot.end_s)}",
                _subtitle_text(shot),
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
                "order",
                "start_s",
                "end_s",
                "duration_s",
                "framing",
                "camera_motion",
                "purpose",
            ]
        )
        for shot in timeline.shots:
            writer.writerow(
                [
                    shot.shot_id,
                    shot.scene_id,
                    shot.order,
                    f"{shot.start_s:.3f}",
                    f"{shot.end_s:.3f}",
                    f"{shot.duration_s:.3f}",
                    shot.framing,
                    shot.camera_motion,
                    shot.purpose,
                ]
            )


def _write_audio_cues(timeline: AnimaticTimeline, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for shot in timeline.shots:
            record = {
                "shot_id": shot.shot_id,
                "start_s": shot.start_s,
                "duration_s": shot.duration_s,
                "cue": shot.audio_cue,
                "intensity": shot.intensity,
                "guide_only": True,
            }
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _scene_palette(scene_id: str) -> tuple[str, str, str]:
    palettes = {
        "S01-NOISE": ("#07111f", "#17324a", "#60d7ff"),
        "S02-NETWORK": ("#090d20", "#26205c", "#7fffd4"),
        "S03-CORRECTION": ("#121321", "#563a26", "#ffcc66"),
        "S04-DISPLACEMENT": ("#170c19", "#56213e", "#ff5c8a"),
        "S05-EIGHTH-FIRE": ("#05040e", "#32185c", "#d99cff"),
    }
    return palettes.get(scene_id, ("#101018", "#303040", "#ffffff"))


def _write_contact_sheet(timeline: AnimaticTimeline, path: Path) -> None:
    width, height = 1600, 1800
    columns, rows = 5, 6
    gap = 18
    card_w = (width - gap * (columns + 1)) / columns
    card_h = (height - 120 - gap * (rows + 1)) / rows
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#080b12"/>',
        '<text x="40" y="55" fill="#ffffff" font-family="sans-serif" font-size="32" font-weight="700">Le Huitième Feu — Storyboard R2</text>',
        '<text x="40" y="88" fill="#9cb0c8" font-family="sans-serif" font-size="18">30 plans · 180 secondes · private-draft</text>',
    ]
    for index, shot in enumerate(timeline.shots):
        row, column = divmod(index, columns)
        x = gap + column * (card_w + gap)
        y = 110 + gap + row * (card_h + gap)
        bg, middle, accent = _scene_palette(shot.scene_id)
        caption = html.escape(shot.caption[:42])
        purpose = html.escape(shot.purpose[:35])
        parts.extend(
            [
                f'<g data-shot="{html.escape(shot.shot_id)}">',
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{card_w:.1f}" height="{card_h:.1f}" rx="12" fill="{bg}" stroke="{accent}" stroke-width="2"/>',
                f'<rect x="{x + 12:.1f}" y="{y + 12:.1f}" width="{card_w - 24:.1f}" height="{card_h * 0.56:.1f}" rx="8" fill="{middle}"/>',
                f'<circle cx="{x + card_w * 0.5:.1f}" cy="{y + card_h * 0.31:.1f}" r="{20 + (index % 4) * 4}" fill="none" stroke="{accent}" stroke-width="3"/>',
                f'<path d="M {x + 28:.1f} {y + card_h * 0.48:.1f} Q {x + card_w * 0.45:.1f} {y + 34:.1f}, {x + card_w - 28:.1f} {y + card_h * 0.46:.1f}" fill="none" stroke="{accent}" stroke-width="2" opacity="0.8"/>',
                f'<text x="{x + 14:.1f}" y="{y + card_h * 0.66:.1f}" fill="#ffffff" font-family="monospace" font-size="15">{html.escape(shot.shot_id)}</text>',
                f'<text x="{x + 14:.1f}" y="{y + card_h * 0.76:.1f}" fill="#b8c8da" font-family="sans-serif" font-size="14">{purpose}</text>',
                f'<text x="{x + 14:.1f}" y="{y + card_h * 0.86:.1f}" fill="{accent}" font-family="sans-serif" font-size="13">{caption}</text>',
                f'<text x="{x + card_w - 14:.1f}" y="{y + card_h - 12:.1f}" text-anchor="end" fill="#8da0b8" font-family="monospace" font-size="13">{shot.start_s:.0f}–{shot.end_s:.0f}s</text>',
                "</g>",
            ]
        )
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def _render_html(timeline: AnimaticTimeline) -> str:
    payload = json.dumps(timeline.to_dict(), ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Le Huitième Feu — Animatique R2</title>
<style>
:root {{ color-scheme: dark; font-family: Inter, system-ui, sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; min-height: 100vh; background: #05070d; color: #eef6ff; display: grid; place-items: center; }}
main {{ width: min(1180px, 100vw); padding: 18px; }}
header {{ display:flex; justify-content:space-between; align-items:end; gap:16px; margin-bottom:12px; }}
h1 {{ margin:0; font-size:clamp(24px,4vw,46px); }}
.badge {{ color:#89e7ff; border:1px solid #2c738c; border-radius:999px; padding:6px 12px; }}
.stage {{ position:relative; aspect-ratio:16/9; border:1px solid #26384e; border-radius:16px; overflow:hidden; background:#02040a; box-shadow:0 20px 80px #000a; }}
canvas {{ width:100%; height:100%; display:block; }}
.subtitle {{ position:absolute; left:8%; right:8%; bottom:6%; text-align:center; font-size:clamp(18px,2.4vw,34px); font-weight:700; text-shadow:0 3px 12px #000; }}
.controls {{ display:grid; grid-template-columns:auto 1fr auto auto; gap:12px; align-items:center; padding-top:14px; }}
button {{ background:#16283b; color:white; border:1px solid #3c688c; border-radius:9px; padding:10px 16px; cursor:pointer; }}
input[type=range] {{ width:100%; }}
.meta {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-top:12px; color:#a9bdd2; font-size:14px; }}
.panel {{ background:#0b111c; border:1px solid #1e3044; border-radius:10px; padding:10px; }}
@media (max-width:700px) {{ .controls {{grid-template-columns:auto 1fr}} .meta {{grid-template-columns:1fr}} }}
</style>
</head>
<body>
<main>
<header><div><h1>Le Huitième Feu</h1><div>Animatique procédurale R2 · 180 secondes</div></div><div class="badge">PRIVATE-DRAFT · OAK</div></header>
<section class="stage"><canvas id="stage" width="1280" height="720"></canvas><div id="subtitle" class="subtitle"></div></section>
<section class="controls"><button id="play">Lecture</button><input id="seek" type="range" min="0" max="180" step="0.01" value="0"><output id="time">00:00.00</output><button id="sound">Son guide</button></section>
<section class="meta"><div id="shot" class="panel"></div><div id="intent" class="panel"></div><div id="status" class="panel"></div></section>
</main>
<script>
const TIMELINE={payload};
const canvas=document.getElementById('stage'),ctx=canvas.getContext('2d');
const seek=document.getElementById('seek'),play=document.getElementById('play'),sound=document.getElementById('sound');
const subtitle=document.getElementById('subtitle'),timeOut=document.getElementById('time');
const shotOut=document.getElementById('shot'),intentOut=document.getElementById('intent'),statusOut=document.getElementById('status');
let playing=false,current=0,last=0,audio=null,lastCue='';
const palettes={{'S01-NOISE':['#07111f','#17324a','#60d7ff'],'S02-NETWORK':['#090d20','#26205c','#7fffd4'],'S03-CORRECTION':['#121321','#563a26','#ffcc66'],'S04-DISPLACEMENT':['#170c19','#56213e','#ff5c8a'],'S05-EIGHTH-FIRE':['#05040e','#32185c','#d99cff']}};
function activeShot(t){{return TIMELINE.shots.find(s=>t>=s.start_s&&t<s.end_s)||TIMELINE.shots.at(-1)}}
function fmt(t){{const m=Math.floor(t/60),s=t-m*60;return String(m).padStart(2,'0')+':'+s.toFixed(2).padStart(5,'0')}}
function tone(shot){{if(!audio)return;const o=audio.createOscillator(),g=audio.createGain();o.type='sine';o.frequency.value=140+shot.intensity*520;g.gain.setValueAtTime(0.0001,audio.currentTime);g.gain.exponentialRampToValueAtTime(0.04,audio.currentTime+0.02);g.gain.exponentialRampToValueAtTime(0.0001,audio.currentTime+0.20);o.connect(g).connect(audio.destination);o.start();o.stop(audio.currentTime+0.22)}}
function draw(t){{const s=activeShot(t),p=palettes[s.scene_id]||['#111','#333','#fff'];const local=(t-s.start_s)/s.duration_s;ctx.fillStyle=p[0];ctx.fillRect(0,0,1280,720);const grad=ctx.createRadialGradient(640,360,20,640,360,620);grad.addColorStop(0,p[1]);grad.addColorStop(1,p[0]);ctx.fillStyle=grad;ctx.fillRect(0,0,1280,720);ctx.globalAlpha=.7;ctx.strokeStyle=p[2];ctx.lineWidth=2;for(let i=0;i<18;i++){{const a=i*2.399+s.order;const x=640+Math.cos(a+local)*((i%6)*72+80);const y=350+Math.sin(a*1.31-local)*((i%5)*46+55);ctx.beginPath();ctx.moveTo(640,350);ctx.lineTo(x,y);ctx.stroke();ctx.beginPath();ctx.arc(x,y,4+(i%4),0,Math.PI*2);ctx.stroke()}}ctx.globalAlpha=1;ctx.fillStyle='#07101a';ctx.beginPath();ctx.arc(640+Math.sin(local*Math.PI)*90,310,54,0,Math.PI*2);ctx.fill();ctx.fillRect(598+Math.sin(local*Math.PI)*90,362,84,180);ctx.strokeStyle=p[2];ctx.lineWidth=4;ctx.strokeRect(598+Math.sin(local*Math.PI)*90,362,84,180);ctx.fillStyle='#eef6ff';ctx.font='700 22px system-ui';ctx.fillText(s.shot_id,34,48);ctx.font='18px system-ui';ctx.fillStyle=p[2];ctx.fillText(s.framing+' · '+s.camera_motion,34,78);ctx.textAlign='right';ctx.fillStyle='#b7c8da';ctx.fillText(fmt(s.start_s)+' → '+fmt(s.end_s),1244,48);ctx.textAlign='left';subtitle.textContent=s.dialogue||'['+s.caption+']';shotOut.textContent=s.shot_id+' · '+s.scene_id;intentOut.textContent=s.purpose+' · '+s.caption;statusOut.textContent=s.audio_cue+' · intensité '+s.intensity.toFixed(2);timeOut.textContent=fmt(t);seek.value=t;if(audio&&lastCue!==s.shot_id){{lastCue=s.shot_id;tone(s)}}}}
function frame(now){{if(playing){{if(!last)last=now;current+=Math.min(.1,(now-last)/1000);last=now;if(current>=TIMELINE.duration_s){{current=TIMELINE.duration_s;playing=false;play.textContent='Rejouer'}}}}draw(current);requestAnimationFrame(frame)}}
play.onclick=()=>{{if(current>=TIMELINE.duration_s)current=0;playing=!playing;last=0;play.textContent=playing?'Pause':'Lecture'}};
seek.oninput=()=>{{current=Number(seek.value);lastCue='';draw(current)}};
sound.onclick=()=>{{audio=audio||new AudioContext();audio.resume();sound.textContent='Son actif';lastCue=''}};
draw(0);requestAnimationFrame(frame);
</script>
</body>
</html>
"""


def _write_report(timeline: AnimaticTimeline, path: Path) -> None:
    lines = [
        "# Le Huitième Feu — Animatique R2",
        "",
        f"- Projet : `{timeline.project_id}`",
        f"- Durée : `{timeline.duration_s:.0f} s`",
        f"- Scènes : `{len(timeline.scenes)}`",
        f"- Plans : `{len(timeline.shots)}`",
        "- Lecteur : `Canvas + WebAudio`, autonome et sans dépendance réseau",
        "- Statut : `private-draft`",
        "",
        "## Frontière OAK",
        "",
        "Cet artefact démontre le montage temporel, les intentions de plans, les sous-titres et un langage visuel procédural.",
        "Il ne constitue ni une animation finale, ni une validation artistique, juridique, scientifique ou commerciale.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def compile_animatic_bundle(timeline: AnimaticTimeline, output_dir: str | Path) -> dict[str, Any]:
    timeline.require_valid()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    (output / "timeline.json").write_text(canonical_json(timeline.to_dict()), encoding="utf-8")
    _write_audio_cues(timeline, output / "audio-cues.jsonl")
    _write_edl(timeline, output / "edit-decision-list.csv")
    _write_vtt(timeline, output / "subtitles.fr.vtt")
    _write_contact_sheet(timeline, output / "storyboard-contact-sheet.svg")
    (output / "eighth-fire-animatic.html").write_text(_render_html(timeline), encoding="utf-8")
    _write_report(timeline, output / "report.md")

    files: dict[str, dict[str, Any]] = {}
    for path in sorted(output.iterdir()):
        if path.name == "manifest.json":
            continue
        files[path.name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}

    manifest_base = {
        "schema_version": "omega-anime-animatic/r2",
        "project_id": timeline.project_id,
        "publication_state": timeline.publication_state,
        "duration_s": timeline.duration_s,
        "scene_count": len(timeline.scenes),
        "shot_count": len(timeline.shots),
        "artifact_count": len(ARTIFACT_NAMES),
        "self_contained_browser_player": True,
        "external_network_dependencies": 0,
        "guide_audio_only": True,
        "files": files,
    }
    digest = hashlib.sha256(canonical_json(manifest_base).encode("utf-8")).hexdigest()
    manifest = {**manifest_base, "manifest_sha256": digest}
    (output / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")

    actual_names = {path.name for path in output.iterdir()}
    if actual_names != ARTIFACT_NAMES:
        raise RuntimeError(f"unexpected artifact set: {sorted(actual_names)}")
    return manifest
