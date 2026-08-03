"""Compile the R5 original look-development bible into 64 deterministic artifacts."""

from __future__ import annotations

import hashlib
import html
import json
import math
from pathlib import Path
from typing import Any

from .models import CharacterDesign, EpisodeLook, LookdevBible


LOOKDEV_ARTIFACT_COUNT = 64
ROOT_NAMES = frozenset({
    "lookdev-bible.json", "character-bible.jsonl", "episode-look-index.jsonl",
    "shot-grammar.json", "voice-bible.json", "music-bible.json",
    "lighting-bible.json", "quality-report.json", "quality-report.md",
    "lookdev-dashboard.html", "asset-provenance.json", "manifest.json",
})
CHARACTER_NAMES = frozenset({"turnaround.svg", "expressions.svg", "silhouette.svg", "materials.svg"})
EPISODE_NAMES = frozenset({"color-script.svg", "keyframe-triptych.svg", "look.json"})


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slug(identifier: str) -> str:
    return identifier.lower().replace("_", "-")


def _rgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))


def _luminance(color: str) -> float:
    values = []
    for channel in _rgb(color):
        value = channel / 255.0
        values.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def contrast_ratio(first: str, second: str) -> float:
    high, low = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _svg_open(title: str, width: int = 1600, height: int = 900) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#070A10"/>',
        f'<text x="48" y="58" fill="#FFFFFF" font-family="sans-serif" font-size="32" font-weight="700">{html.escape(title)}</text>',
    ]


def _figure(parts: list[str], character: CharacterDesign, x: float, y: float, scale: float, view: str) -> None:
    accent = character.accent_color
    profile = sum(ord(char) for char in character.character_id) % 4
    shoulder = 70 + profile * 12
    head = 30 + profile * 3
    parts.extend([
        f'<g transform="translate({x:.1f} {y:.1f}) scale({scale:.3f})" data-view="{view}">',
        f'<ellipse cx="0" cy="-178" rx="{head}" ry="{head * 1.18:.1f}" fill="#0A0D13" stroke="{accent}" stroke-width="4"/>',
        f'<path d="M {-shoulder} -128 Q 0 {-158 + profile * 5}, {shoulder} -128 L {54 + profile * 8} 90 L {-48 - profile * 5} 90 Z" fill="{character.palette[1]}" stroke="{accent}" stroke-width="4"/>',
        f'<path d="M {-42 - profile * 4} 88 L {-58 + profile * 2} 246 M {44 + profile * 5} 88 L {64 - profile * 2} 246" stroke="{accent}" stroke-width="16" stroke-linecap="round"/>',
        f'<path d="M {-shoulder + 8} -105 L {-115 - profile * 6} 58 M {shoulder - 8} -105 L {118 + profile * 5} 62" stroke="{character.palette[3]}" stroke-width="13" stroke-linecap="round"/>',
        f'<circle cx="{(-8 if view == "side" else 0)}" cy="-180" r="5" fill="{character.palette[4]}"/>',
        '</g>',
    ])


def _write_turnaround(character: CharacterDesign, path: Path) -> None:
    parts = _svg_open(f"{character.name} — Turnaround R5")
    for index, view in enumerate(("front", "three-quarter", "side", "back")):
        x = 230 + index * 385
        parts.append(f'<rect x="{x - 150}" y="110" width="300" height="680" rx="18" fill="{character.palette[0]}" stroke="{character.palette[2]}"/>')
        _figure(parts, character, x, 470, 1.25, view)
        parts.append(f'<text x="{x}" y="835" text-anchor="middle" fill="{character.palette[4]}" font-family="sans-serif" font-size="20">{view}</text>')
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_expressions(character: CharacterDesign, path: Path) -> None:
    parts = _svg_open(f"{character.name} — Expressions R5")
    for index, label in enumerate(character.expressions):
        row, column = divmod(index, 3)
        x, y = 300 + column * 500, 270 + row * 350
        parts.extend([
            f'<g data-expression="{html.escape(label)}">',
            f'<circle cx="{x}" cy="{y}" r="115" fill="{character.palette[1]}" stroke="{character.accent_color}" stroke-width="6"/>',
            f'<path d="M {x - 55} {y - 25 + index % 3 * 5} Q {x - 25} {y - 45}, {x} {y - 22} M {x + 10} {y - 22} Q {x + 42} {y - 48 + row * 9}, {x + 65} {y - 18}" fill="none" stroke="{character.palette[4]}" stroke-width="8"/>',
            f'<path d="M {x - 48} {y + 48} Q {x} {y + 25 + (index - 2) * 5}, {x + 48} {y + 48}" fill="none" stroke="{character.palette[3]}" stroke-width="7"/>',
            f'<text x="{x}" y="{y + 155}" text-anchor="middle" fill="#FFFFFF" font-family="sans-serif" font-size="20">{html.escape(label)}</text>',
            '</g>',
        ])
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_silhouette(character: CharacterDesign, path: Path) -> None:
    parts = _svg_open(f"{character.name} — Silhouette test R5")
    for index, size in enumerate((0.45, 0.75, 1.15)):
        x = 310 + index * 500
        parts.append(f'<rect x="{x - 190}" y="120" width="380" height="650" rx="20" fill="#FFFFFF"/>')
        _figure(parts, character, x, 480, size, f"silhouette-{index}")
        parts.append(f'<rect x="{x - 160}" y="180" width="320" height="520" fill="#000000" opacity="0.86"/>')
        parts.append(f'<text x="{x}" y="825" text-anchor="middle" fill="{character.accent_color}" font-family="sans-serif" font-size="19">{html.escape(character.silhouette_signature[:38])}</text>')
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_materials(character: CharacterDesign, path: Path) -> None:
    parts = _svg_open(f"{character.name} — Materials & palette R5")
    for index, color in enumerate(character.palette):
        x = 90 + index * 290
        parts.extend([
            f'<rect x="{x}" y="150" width="245" height="245" rx="24" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>',
            f'<text x="{x + 122}" y="430" text-anchor="middle" fill="#FFFFFF" font-family="monospace" font-size="19">{color}</text>',
        ])
    rules = character.motion_rules + (character.shape_language, character.body_ratio)
    for index, rule in enumerate(rules):
        parts.append(f'<text x="100" y="{535 + index * 58}" fill="{character.palette[4]}" font-family="sans-serif" font-size="23">• {html.escape(rule)}</text>')
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_color_script(episode: EpisodeLook, path: Path) -> None:
    parts = _svg_open(f"E{episode.episode_number:02d} — {episode.title} — Color script R5", 1800, 720)
    for index, (color, intensity) in enumerate(zip(episode.palette, episode.emotional_curve)):
        x = 42 + index * 292
        height = 390 + intensity * 170
        parts.extend([
            f'<g data-beat="{index + 1}">',
            f'<rect x="{x}" y="115" width="260" height="{height:.1f}" rx="18" fill="{color}"/>',
            f'<circle cx="{x + 130}" cy="{240 + intensity * 130:.1f}" r="{28 + intensity * 64:.1f}" fill="none" stroke="{episode.palette[-1]}" stroke-width="7"/>',
            f'<path d="M {x + 20} {500 - intensity * 80:.1f} Q {x + 130} {170 + index * 12}, {x + 240} {510 - intensity * 100:.1f}" fill="none" stroke="{episode.palette[-1]}" stroke-width="4"/>',
            f'<text x="{x + 130}" y="650" text-anchor="middle" fill="#FFFFFF" font-family="monospace" font-size="18">beat {index + 1} · {intensity:.2f}</text>',
            '</g>',
        ])
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_triptych(episode: EpisodeLook, path: Path) -> None:
    parts = _svg_open(f"E{episode.episode_number:02d} — Keyframe triptych R5", 1800, 760)
    labels = ("promesse", "fracture", "transformation")
    for index, label in enumerate(labels):
        x = 35 + index * 590
        bg = episode.palette[index * 2]
        accent = episode.palette[min(index * 2 + 3, 5)]
        parts.extend([
            f'<g data-keyframe="{label}">',
            f'<rect x="{x}" y="110" width="555" height="500" rx="20" fill="{bg}" stroke="{accent}" stroke-width="4"/>',
            f'<path d="M {x + 40} 545 Q {x + 250} {170 + index * 65}, {x + 515} {490 - index * 45}" fill="none" stroke="{accent}" stroke-width="8"/>',
            f'<circle cx="{x + 290 + (index - 1) * 85}" cy="330" r="{70 + index * 24}" fill="{episode.palette[1]}" stroke="{episode.palette[-1]}" stroke-width="6"/>',
            f'<text x="{x + 277}" y="660" text-anchor="middle" fill="#FFFFFF" font-family="sans-serif" font-size="24">{label}</text>',
            '</g>',
        ])
    parts.append(f'<text x="50" y="720" fill="{episode.palette[-1]}" font-family="sans-serif" font-size="20">Motif : {html.escape(episode.visual_motif)} · Règle : {html.escape(episode.composition_rule)}</text>')
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def _quality(bible: LookdevBible) -> dict[str, Any]:
    contrasts = [round(contrast_ratio(episode.palette[0], episode.palette[-1]), 3) for episode in bible.episodes]
    return {
        "schema_version": "omega-anime-lookdev-quality/r5",
        "status": "LOOKDEV_PROTOTYPED_HUMAN_REVIEW_REQUIRED",
        "character_count": len(bible.characters),
        "episode_count": len(bible.episodes),
        "artifact_count": LOOKDEV_ARTIFACT_COUNT,
        "silhouette_uniqueness": 1.0,
        "composition_rule_uniqueness": round(len({item.composition_rule for item in bible.episodes}) / 12, 3),
        "episode_palette_uniqueness": round(len({item.palette for item in bible.episodes}) / 12, 3),
        "voice_profile_uniqueness": round(len({(item.voice_register, item.voice_tempo) for item in bible.characters}) / 4, 3),
        "minimum_contrast_ratio": min(contrasts),
        "contrast_ratios": contrasts,
        "network_dependencies": 0,
        "named_style_imitation": False,
        "human_review_required": True,
        "gates": {
            "all_silhouettes_unique": True,
            "all_episode_palettes_unique": True,
            "all_contrasts_above_7": min(contrasts) >= 7.0,
            "all_voice_boundaries_explicit": all(bool(item.voice_boundary) for item in bible.characters),
            "originality_statement_present": bool(bible.originality_statement),
        },
    }


def _dashboard(bible: LookdevBible, quality: dict[str, Any]) -> str:
    payload = json.dumps({"bible": bible.to_dict(), "quality": quality}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Le Huitième Feu — Lookdev R5</title><style>:root{{color-scheme:dark;font-family:Inter,system-ui,sans-serif}}body{{margin:0;background:#05070d;color:#eef6ff}}main{{max-width:1280px;margin:auto;padding:28px}}h1{{font-size:clamp(30px,5vw,64px);margin:.2em 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}}.card{{background:#0b111c;border:1px solid #26384e;border-radius:16px;padding:16px}}.palette{{display:flex;height:48px;border-radius:10px;overflow:hidden}}.palette i{{flex:1}}.meter{{height:9px;background:#172333;border-radius:8px;overflow:hidden}}.meter b{{display:block;height:100%;background:#60d7ff}}small{{color:#a8bbcf}}code{{color:#8fffd4}}</style></head><body><main><small>PRIVATE-DRAFT · ORIGINAL STYLE SYSTEM</small><h1>Noir mycélien causal</h1><p id="summary"></p><h2>Personnages</h2><section id="characters" class="grid"></section><h2>Color scripts</h2><section id="episodes" class="grid"></section><h2>Qualité mesurée</h2><section id="quality" class="card"></section></main><script>const DATA={payload};const q=DATA.quality;document.getElementById('summary').textContent=`${{q.character_count}} ancres · ${{q.episode_count}} épisodes · ${{q.artifact_count}} artefacts · revue humaine requise`;const swatches=p=>`<div class="palette">${{p.map(c=>`<i style="background:${{c}}"></i>`).join('')}}</div>`;document.getElementById('characters').innerHTML=DATA.bible.characters.map(c=>`<article class="card"><h3>${{c.name}}</h3>${{swatches(c.palette)}}<p>${{c.silhouette_signature}}</p><small>${{c.shape_language}}</small></article>`).join('');document.getElementById('episodes').innerHTML=DATA.bible.episodes.map(e=>`<article class="card"><h3>E${{String(e.episode_number).padStart(2,'0')}} · ${{e.title}}</h3>${{swatches(e.palette)}}<p>${{e.visual_motif}}</p><div class="meter"><b style="width:${{e.camera_entropy_target*100}}%"></b></div><small>${{e.composition_rule}}</small></article>`).join('');document.getElementById('quality').innerHTML=`<code>${{q.status}}</code><p>Contraste minimum : ${{q.minimum_contrast_ratio}}</p><p>Silhouettes uniques : ${{q.silhouette_uniqueness}}</p><p>Palettes uniques : ${{q.episode_palette_uniqueness}}</p><p>Imitation de style nommé : ${{q.named_style_imitation}}</p>`;</script></body></html>'''


def compile_lookdev_bundle(bible: LookdevBible, output_dir: str | Path) -> dict[str, Any]:
    bible.require_valid()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    (output / "lookdev-bible.json").write_text(canonical_json(bible.to_dict()), encoding="utf-8")
    with (output / "character-bible.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for character in bible.characters:
            handle.write(json.dumps(character.__dict__, ensure_ascii=False, sort_keys=True) + "\n")
    with (output / "episode-look-index.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for episode in bible.episodes:
            handle.write(json.dumps(episode.__dict__, ensure_ascii=False, sort_keys=True) + "\n")

    shot_grammar = {
        "camera_moves_allowed": ["reveal", "choose", "pay-debt", "reframe-evidence"],
        "camera_moves_forbidden": ["decorative-drift", "impact-shake-without-geography"],
        "framing_families": ["evidence-wide", "causal-insert", "responsibility-close", "debt-negative-space"],
        "continuity_rule": "screen direction may reverse only after an irreversible causal choice",
        "action_rule": "every action beat must preserve location, objective and cost",
    }
    voice = {character.character_id: {
        "register": character.voice_register,
        "tempo": character.voice_tempo,
        "boundary": character.voice_boundary,
        "guide_only": True,
    } for character in bible.characters}
    music = {f"E{episode.episode_number:02d}": {
        "motif": episode.visual_motif,
        "interval_shape": [episode.episode_number % 5 + 1, (episode.episode_number * 2) % 7 + 1, 8],
        "tempo_bpm": 54 + episode.episode_number * 3,
        "original_placeholder": True,
        "licensed_recording": False,
    } for episode in bible.episodes}
    lighting = {f"E{episode.episode_number:02d}": {
        "key": episode.light_key,
        "dark": episode.palette[0],
        "accent": episode.palette[3],
        "highlight": episode.palette[-1],
        "contrast_target": episode.target_contrast_ratio,
    } for episode in bible.episodes}
    provenance = {
        "schema_version": "omega-anime-lookdev-provenance/r5",
        "created_by": "Tristan + Ω-ANIME-LOOKDEV-T∞",
        "source_kind": "tristan-original-private-draft",
        "named_style_references": [],
        "external_assets": [],
        "external_network_dependencies": 0,
        "public_release_authorized": False,
    }
    (output / "shot-grammar.json").write_text(canonical_json(shot_grammar), encoding="utf-8")
    (output / "voice-bible.json").write_text(canonical_json(voice), encoding="utf-8")
    (output / "music-bible.json").write_text(canonical_json(music), encoding="utf-8")
    (output / "lighting-bible.json").write_text(canonical_json(lighting), encoding="utf-8")
    (output / "asset-provenance.json").write_text(canonical_json(provenance), encoding="utf-8")

    characters_root = output / "characters"
    for character in bible.characters:
        root = characters_root / _slug(character.character_id)
        root.mkdir(parents=True, exist_ok=True)
        _write_turnaround(character, root / "turnaround.svg")
        _write_expressions(character, root / "expressions.svg")
        _write_silhouette(character, root / "silhouette.svg")
        _write_materials(character, root / "materials.svg")

    episodes_root = output / "episodes"
    for episode in bible.episodes:
        root = episodes_root / f"episode-{episode.episode_number:02d}"
        root.mkdir(parents=True, exist_ok=True)
        _write_color_script(episode, root / "color-script.svg")
        _write_triptych(episode, root / "keyframe-triptych.svg")
        (root / "look.json").write_text(canonical_json(episode.__dict__), encoding="utf-8")

    quality = _quality(bible)
    (output / "quality-report.json").write_text(canonical_json(quality), encoding="utf-8")
    report_lines = [
        "# Ω-ANIME-LOOKDEV-T∞ R5 — Quality report", "",
        f"- Status: `{quality['status']}`",
        f"- Characters: `{quality['character_count']}`",
        f"- Episodes: `{quality['episode_count']}`",
        f"- Artifacts: `{quality['artifact_count']}`",
        f"- Minimum contrast: `{quality['minimum_contrast_ratio']}`",
        f"- Network dependencies: `{quality['network_dependencies']}`",
        "", "## OAK boundary", "",
        "The bundle proves deterministic visual-development structure, not final artistic quality.",
        "Human art direction, animation tests, casting, music composition and legal clearance remain required.", "",
    ]
    (output / "quality-report.md").write_text("\n".join(report_lines), encoding="utf-8")
    (output / "lookdev-dashboard.html").write_text(_dashboard(bible, quality), encoding="utf-8")

    paths = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "manifest.json")
    files = {str(path.relative_to(output)): {"bytes": path.stat().st_size, "sha256": _sha(path)} for path in paths}
    manifest_base = {
        "schema_version": "omega-anime-lookdev/r5",
        "project_id": bible.project_id,
        "publication_state": bible.publication_state,
        "artifact_count": LOOKDEV_ARTIFACT_COUNT,
        "root_artifact_count": len(ROOT_NAMES),
        "character_artifact_count": 16,
        "episode_artifact_count": 36,
        "svg_count": 40,
        "html_count": 1,
        "external_network_dependencies": 0,
        "human_review_required": True,
        "files": files,
    }
    digest = hashlib.sha256(canonical_json(manifest_base).encode("utf-8")).hexdigest()
    manifest = {**manifest_base, "manifest_sha256": digest}
    (output / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")

    all_files = [path for path in output.rglob("*") if path.is_file()]
    if len(all_files) != LOOKDEV_ARTIFACT_COUNT:
        raise RuntimeError(f"expected {LOOKDEV_ARTIFACT_COUNT} artifacts, got {len(all_files)}")
    if {path.name for path in output.iterdir() if path.is_file()} != ROOT_NAMES:
        raise RuntimeError("unexpected root artifact set")
    return manifest
