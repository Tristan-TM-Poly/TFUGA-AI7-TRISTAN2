import hashlib
import json
from pathlib import Path

from omega_anime_lookdev_t import LOOKDEV_ARTIFACT_COUNT, build_eighth_fire_lookdev_r5, compile_lookdev_bundle
from omega_anime_lookdev_t.compiler import CHARACTER_NAMES, EPISODE_NAMES, ROOT_NAMES, contrast_ratio


def bible():
    return build_eighth_fire_lookdev_r5()


def compiled(tmp_path: Path) -> Path:
    root = tmp_path / "lookdev"
    compile_lookdev_bundle(bible(), root)
    return root


def test_bible_is_valid():
    assert bible().validate() == []


def test_style_is_original_and_private():
    item = bible()
    assert item.publication_state == "private-draft"
    assert "aucune imitation" in item.originality_statement.lower()


def test_four_design_anchors_exist():
    assert len(bible().characters) == 4


def test_canonical_characters_are_present():
    ids = {item.character_id for item in bible().characters}
    assert {"CHAR-TRISTAN", "CHAR-OBSERVATRICE", "CHAR-CREANCIER", "CHAR-TEMOIN-ZERO"} == ids


def test_silhouettes_are_unique():
    values = [item.silhouette_signature for item in bible().characters]
    assert len(values) == len(set(values))


def test_character_palettes_have_five_colors():
    assert all(len(item.palette) == 5 for item in bible().characters)


def test_every_character_has_six_expressions():
    assert all(len(item.expressions) == 6 for item in bible().characters)


def test_voice_boundaries_are_explicit():
    assert all("imitation" in item.voice_boundary.lower() or "synthétique" in item.voice_boundary.lower() for item in bible().characters)


def test_twelve_episode_looks_exist():
    assert len(bible().episodes) == 12


def test_episode_numbers_are_contiguous():
    assert [item.episode_number for item in bible().episodes] == list(range(1, 13))


def test_episode_titles_are_unique():
    titles = [item.title for item in bible().episodes]
    assert len(titles) == len(set(titles))


def test_episode_palettes_are_unique():
    palettes = [item.palette for item in bible().episodes]
    assert len(palettes) == len(set(palettes))


def test_each_episode_has_six_color_beats():
    assert all(len(item.palette) == 6 and len(item.emotional_curve) == 6 for item in bible().episodes)


def test_composition_rules_are_highly_diverse():
    assert len({item.composition_rule for item in bible().episodes}) == 12


def test_palette_contrast_exceeds_seven():
    assert all(contrast_ratio(item.palette[0], item.palette[-1]) >= 7.0 for item in bible().episodes)


def test_compile_creates_exactly_64_files(tmp_path: Path):
    root = compiled(tmp_path)
    assert len([path for path in root.rglob("*") if path.is_file()]) == LOOKDEV_ARTIFACT_COUNT


def test_root_artifact_set_is_exact(tmp_path: Path):
    root = compiled(tmp_path)
    assert {path.name for path in root.iterdir() if path.is_file()} == ROOT_NAMES


def test_four_character_directories_exist(tmp_path: Path):
    root = compiled(tmp_path)
    assert len([path for path in (root / "characters").iterdir() if path.is_dir()]) == 4


def test_each_character_has_four_sheets(tmp_path: Path):
    root = compiled(tmp_path)
    for directory in (root / "characters").iterdir():
        assert {path.name for path in directory.iterdir()} == CHARACTER_NAMES


def test_twelve_episode_directories_exist(tmp_path: Path):
    root = compiled(tmp_path)
    assert len([path for path in (root / "episodes").iterdir() if path.is_dir()]) == 12


def test_each_episode_has_three_lookdev_files(tmp_path: Path):
    root = compiled(tmp_path)
    for directory in (root / "episodes").iterdir():
        assert {path.name for path in directory.iterdir()} == EPISODE_NAMES


def test_exactly_forty_svg_files_are_generated(tmp_path: Path):
    root = compiled(tmp_path)
    assert len(list(root.rglob("*.svg"))) == 40


def test_all_svg_files_are_self_contained(tmp_path: Path):
    root = compiled(tmp_path)
    for path in root.rglob("*.svg"):
        content = path.read_text(encoding="utf-8")
        assert content.startswith("<svg")
        assert "<image" not in content
        assert "http://" not in content
        assert "https://" not in content


def test_turnarounds_have_four_views(tmp_path: Path):
    root = compiled(tmp_path)
    for path in root.glob("characters/*/turnaround.svg"):
        assert path.read_text(encoding="utf-8").count("data-view=") == 4


def test_expression_sheets_have_six_expressions(tmp_path: Path):
    root = compiled(tmp_path)
    for path in root.glob("characters/*/expressions.svg"):
        assert path.read_text(encoding="utf-8").count("data-expression=") == 6


def test_color_scripts_have_six_beats(tmp_path: Path):
    root = compiled(tmp_path)
    for path in root.glob("episodes/*/color-script.svg"):
        assert path.read_text(encoding="utf-8").count("data-beat=") == 6


def test_keyframe_triptychs_have_three_frames(tmp_path: Path):
    root = compiled(tmp_path)
    for path in root.glob("episodes/*/keyframe-triptych.svg"):
        assert path.read_text(encoding="utf-8").count("data-keyframe=") == 3


def test_dashboard_is_self_contained(tmp_path: Path):
    root = compiled(tmp_path)
    content = (root / "lookdev-dashboard.html").read_text(encoding="utf-8")
    assert "fetch(" not in content
    assert "http://" not in content
    assert "https://" not in content
    assert "Noir mycélien causal" in content


def test_quality_report_passes_machine_gates(tmp_path: Path):
    root = compiled(tmp_path)
    report = json.loads((root / "quality-report.json").read_text())
    assert all(report["gates"].values())
    assert report["human_review_required"] is True
    assert report["named_style_imitation"] is False


def test_manifest_counts_are_exact(tmp_path: Path):
    root = compiled(tmp_path)
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["artifact_count"] == 64
    assert manifest["character_artifact_count"] == 16
    assert manifest["episode_artifact_count"] == 36
    assert manifest["svg_count"] == 40
    assert manifest["html_count"] == 1


def test_manifest_hashes_match_files(tmp_path: Path):
    root = compiled(tmp_path)
    manifest = json.loads((root / "manifest.json").read_text())
    for relative, record in manifest["files"].items():
        path = root / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
        assert path.stat().st_size == record["bytes"]


def test_compilation_is_byte_deterministic(tmp_path: Path):
    first, second = tmp_path / "first", tmp_path / "second"
    compile_lookdev_bundle(bible(), first)
    compile_lookdev_bundle(bible(), second)
    first_paths = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
    second_paths = sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file())
    assert first_paths == second_paths
    for relative in first_paths:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()


def test_music_bible_uses_original_placeholders(tmp_path: Path):
    root = compiled(tmp_path)
    music = json.loads((root / "music-bible.json").read_text())
    assert len(music) == 12
    assert all(item["original_placeholder"] and not item["licensed_recording"] for item in music.values())


def test_provenance_contains_no_external_assets(tmp_path: Path):
    root = compiled(tmp_path)
    provenance = json.loads((root / "asset-provenance.json").read_text())
    assert provenance["external_assets"] == []
    assert provenance["named_style_references"] == []
    assert provenance["public_release_authorized"] is False
