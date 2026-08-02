"""Deterministic compiler for reviewable Anime Studio R1 bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .frontier import FrontierBudget, compile_frontier_sample
from .matrix import matrix_summary, write_matrix_jsonl
from .models import AnimeProjectR1, json_ready


def canonical_json(payload: Any) -> str:
    return json.dumps(json_ready(payload), ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def write_json(path: Path, payload: Any) -> None:
    path.write_text(canonical_json(payload), encoding='utf-8')


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
            count += 1
    return count


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_project_bundle(
    project: AnimeProjectR1,
    output_dir: str | Path,
    *,
    frontier_work_items: int = 2048,
) -> dict[str, Any]:
    project.require_valid()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    write_json(output / 'anime-ir.json', project.to_dict())
    write_jsonl(output / 'characters.jsonl', (item.__dict__ for item in project.characters))
    write_jsonl(output / 'scenes.jsonl', (json_ready(item.__dict__) for item in project.scenes))
    write_jsonl(output / 'shots.jsonl', (json_ready(item.__dict__) for item in project.shots))
    write_jsonl(output / 'causal-debts.jsonl', (item.__dict__ for item in project.causal_debts))
    write_jsonl(output / 'assets.jsonl', (json_ready(item.__dict__) for item in project.assets))
    write_jsonl(output / 'nodes.jsonl', (json_ready(item.__dict__) for item in project.nodes))
    write_jsonl(output / 'edges.jsonl', (json_ready(item.__dict__) for item in project.edges))

    matrix_report = write_matrix_jsonl(output / 'matrix-8192.jsonl')
    write_json(output / 'matrix-summary.json', matrix_report)

    frontier_report = compile_frontier_sample(
        output / 'shot-frontier.jsonl',
        tuple(scene.scene_id for scene in project.scenes),
        frontier_work_items,
        FrontierBudget(
            memory_bytes=32 * 1024 * 1024,
            wall_time_s=60.0,
            output_bytes=64 * 1024 * 1024,
            quality_floor=0.70,
        ),
    )
    write_json(output / 'frontier-report.json', frontier_report)

    files = {}
    for path in sorted(output.iterdir()):
        if path.name in {'manifest.json', 'report.md'}:
            continue
        files[path.name] = {
            'sha256': file_hash(path),
            'bytes': path.stat().st_size,
        }

    manifest_base = {
        'schema_version': 'omega-anime-studio/r1',
        'project_id': project.project_id,
        'oak_status': project.oak_status.value,
        'publication_state': project.metadata.get('publication_state'),
        'scene_count': len(project.scenes),
        'shot_count': len(project.shots),
        'matrix_cell_count': matrix_summary()['cell_count'],
        'frontier_work_items': frontier_work_items,
        'files': files,
    }
    manifest_hash = hashlib.sha256(canonical_json(manifest_base).encode('utf-8')).hexdigest()
    manifest = {**manifest_base, 'manifest_sha256': manifest_hash}
    write_json(output / 'manifest.json', manifest)

    report = [
        '# Le Huitième Feu — Ω-ANIME-STUDIO-T∞ R1', '',
        f"- Project: `{project.project_id}`",
        f"- OAK status: `{project.oak_status.value}`",
        f"- Scenes: `{len(project.scenes)}`",
        f"- Shots: `{len(project.shots)}`",
        f"- Matrix cells: `{manifest['matrix_cell_count']}`",
        f"- Frontier sample: `{frontier_work_items}` variants",
        f"- Manifest: `{manifest_hash}`", '',
        '## Boundary', '',
        'The bundle proves deterministic structure and internal validation only.',
        'It does not prove artistic quality, audience demand, legal clearance,',
        'scientific truth, production feasibility or commercial success.', '',
    ]
    (output / 'report.md').write_text('\n'.join(report), encoding='utf-8')
    return manifest
