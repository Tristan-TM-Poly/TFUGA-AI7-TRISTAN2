from __future__ import annotations

import json
from dataclasses import replace

import pytest

from omega_anime_studio_t import (
    AdaptiveFrontierController, AnimeGraph, FrontierBudget,
    build_eighth_fire_r1, compile_frontier_sample, compile_project_bundle,
    iter_matrix_cells, iter_scene_variants, matrix_summary, validate_matrix,
    write_matrix_jsonl,
)
from omega_anime_studio_t.models import AnimeNode, HyperEdge


def test_matrix_has_16_domains_256_modules_and_8192_cells() -> None:
    summary = matrix_summary()
    assert summary['domain_count'] == 16
    assert summary['module_count'] == 256
    assert summary['artifact_kind_count'] == 32
    assert summary['cell_count'] == 8192
    assert summary['unique_cell_count'] == 8192
    assert validate_matrix() == []


def test_matrix_ids_are_deterministic_and_unique() -> None:
    first = list(iter_matrix_cells())
    second = list(iter_matrix_cells())
    assert first == second
    assert len({cell.cell_id for cell in first}) == len(first)
    assert first[0].cell_id == 'ANIME-R1-D01-M01-A01'
    assert first[-1].cell_id == 'ANIME-R1-D16-M16-A32'


def test_write_matrix_jsonl(tmp_path) -> None:
    report = write_matrix_jsonl(tmp_path / 'matrix.jsonl')
    lines = (tmp_path / 'matrix.jsonl').read_text(encoding='utf-8').splitlines()
    assert len(lines) == 8192
    assert report['written'] == 8192
    assert len(report['file_sha256']) == 64
    assert json.loads(lines[0])['cell_id'] == 'ANIME-R1-D01-M01-A01'


def test_eighth_fire_r1_is_valid() -> None:
    project = build_eighth_fire_r1()
    assert project.validate() == []
    project.require_valid()
    assert len(project.scenes) == 5
    assert len(project.shots) == 30
    assert sum(scene.duration_target_s for scene in project.scenes) == 180


def test_each_scene_has_six_contiguous_shots() -> None:
    project = build_eighth_fire_r1()
    for scene in project.scenes:
        shots = [shot for shot in project.shots if shot.scene_id == scene.scene_id]
        assert len(shots) == 6
        assert [shot.order for shot in shots] == list(range(1, 7))
        assert sum(shot.duration_s for shot in shots) == scene.duration_target_s


def test_every_power_has_a_limit_and_moral_boundary() -> None:
    for character in build_eighth_fire_r1().characters:
        assert character.power
        assert character.limitation
        assert character.moral_boundary
        assert character.power.casefold() != character.limitation.casefold()


def test_every_asset_has_private_provenance() -> None:
    for asset in build_eighth_fire_r1().assets:
        assert asset.provenance.private is True
        assert asset.provenance.license_id == 'PRIVATE-DRAFT-NOT-LICENSED'


def test_causal_debt_is_linked_to_scene() -> None:
    project = build_eighth_fire_r1()
    debt = project.causal_debts[0]
    scene = next(scene for scene in project.scenes if scene.scene_id == debt.origin_scene_id)
    assert debt.debt_id in scene.causal_debt_ids
    assert debt.status == 'OPEN'
    assert 0 <= debt.certainty <= 1


def test_invalid_shot_scene_reference_is_rejected() -> None:
    project = build_eighth_fire_r1()
    shots = list(project.shots)
    shots[0] = replace(shots[0], scene_id='UNKNOWN')
    errors = replace(project, shots=tuple(shots)).validate()
    assert any('unknown scene ids' in error for error in errors)


def test_invalid_character_reference_is_rejected() -> None:
    project = build_eighth_fire_r1()
    scenes = list(project.scenes)
    scenes[0] = replace(scenes[0], characters=('UNKNOWN',))
    errors = replace(project, scenes=tuple(scenes)).validate()
    assert any('unknown characters' in error for error in errors)


def test_invalid_asset_reference_is_rejected() -> None:
    project = build_eighth_fire_r1()
    shots = list(project.shots)
    shots[0] = replace(shots[0], asset_ids=('UNKNOWN',))
    errors = replace(project, shots=tuple(shots)).validate()
    assert any('unknown assets' in error for error in errors)


def test_graph_rejects_unknown_nodes() -> None:
    graph = AnimeGraph()
    graph.add_node(AnimeNode('A','Task','A'))
    with pytest.raises(ValueError):
        graph.add_edge(HyperEdge('E','DEPENDS_ON',('A',),('B',)))


def test_graph_topological_order_and_cycle_detection() -> None:
    graph = AnimeGraph()
    graph.extend_nodes((AnimeNode('A','Task','A'), AnimeNode('B','Task','B')))
    graph.add_edge(HyperEdge('E1','DEPENDS_ON',('A',),('B',)))
    assert graph.topological_order() == ['A','B']
    graph.add_edge(HyperEdge('E2','DEPENDS_ON',('B',),('A',)))
    with pytest.raises(ValueError):
        graph.topological_order()


def test_scene_variant_generator_is_large_and_deterministic() -> None:
    first = list(iter_scene_variants('S01'))
    second = list(iter_scene_variants('S01'))
    assert len(first) == 32768
    assert first[:10] == second[:10]
    assert len({item.signature for item in first}) == 32768


def test_frontier_controller_has_no_total_cap() -> None:
    controller = AdaptiveFrontierController(
        FrontierBudget(memory_bytes=10_000_000, wall_time_s=1, output_bytes=10_000_000)
    )
    assert not hasattr(controller.budget, 'max_total')
    for variant in list(iter_scene_variants('S01'))[:100]:
        controller.observe(variant)
    assert controller.state.generated == 100
    assert controller.decide().value in {'EXPAND','HOLD'}


def test_compile_frontier_sample(tmp_path) -> None:
    report = compile_frontier_sample(
        tmp_path / 'frontier.jsonl', ('S01','S02'), 2048,
        FrontierBudget(memory_bytes=10_000_000, wall_time_s=10, output_bytes=10_000_000),
    )
    assert report['written'] == 2048
    assert report['no_permanent_total_cap'] is True
    assert len(report['sha256']) == 64
    assert len((tmp_path / 'frontier.jsonl').read_text().splitlines()) == 2048


def test_bundle_contains_expected_outputs(tmp_path) -> None:
    manifest = compile_project_bundle(build_eighth_fire_r1(), tmp_path)
    expected = {
        'anime-ir.json','characters.jsonl','scenes.jsonl','shots.jsonl',
        'causal-debts.jsonl','assets.jsonl','nodes.jsonl','edges.jsonl',
        'matrix-8192.jsonl','matrix-summary.json','shot-frontier.jsonl',
        'frontier-report.json','manifest.json','report.md',
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    assert manifest['matrix_cell_count'] == 8192
    assert manifest['shot_count'] == 30
    assert len(manifest['manifest_sha256']) == 64


def test_bundle_is_deterministic(tmp_path) -> None:
    first = compile_project_bundle(build_eighth_fire_r1(), tmp_path / 'first', frontier_work_items=128)
    second = compile_project_bundle(build_eighth_fire_r1(), tmp_path / 'second', frontier_work_items=128)
    assert first == second
    for name in first['files']:
        assert (tmp_path / 'first' / name).read_bytes() == (tmp_path / 'second' / name).read_bytes()


def test_payload_is_json_serializable() -> None:
    encoded = json.dumps(build_eighth_fire_r1().to_dict(), ensure_ascii=False, sort_keys=True)
    assert 'Le Huitième Feu' in encoded
    assert 'FORMALIZED' in encoded


@pytest.mark.parametrize('work_items', [1, 17, 257, 2048])
def test_frontier_respects_finite_experiment_request(tmp_path, work_items: int) -> None:
    report = compile_frontier_sample(
        tmp_path / f'{work_items}.jsonl', ('S01',), work_items,
        FrontierBudget(memory_bytes=50_000_000, wall_time_s=10, output_bytes=50_000_000),
    )
    assert report['written'] == work_items
    assert report['finite_experiment_work_items'] == work_items


def test_project_rejects_duration_drift() -> None:
    project = build_eighth_fire_r1()
    scenes = list(project.scenes)
    scenes[0] = replace(scenes[0], duration_target_s=31)
    errors = replace(project, scenes=tuple(scenes)).validate()
    assert any('project.duration' in error for error in errors)


def test_project_rejects_equal_information_states() -> None:
    project = build_eighth_fire_r1()
    scene = project.scenes[0]
    scenes = (replace(scene, audience_after=scene.audience_before),) + project.scenes[1:]
    errors = replace(project, scenes=scenes).validate()
    assert any('information state must change' in error for error in errors)


def test_no_orphan_graph_nodes_in_canonical_seed() -> None:
    project = build_eighth_fire_r1()
    graph = AnimeGraph()
    graph.extend_nodes(project.nodes)
    graph.extend_edges(project.edges)
    assert graph.validate() == []
    # LOC-LAB is intentionally a world node not yet linked by R1 edges.
    assert set(graph.orphan_nodes()) <= {'LOC-LAB'}
