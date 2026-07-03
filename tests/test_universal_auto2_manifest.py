import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "universal_auto2_engines.yaml"
DOC = ROOT / "docs" / "OMEGA_UNIVERSAL_AUTO2_OS_T.md"


def text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def count_id(manifest: str, item_id: str) -> int:
    return manifest.count(f"id: {item_id}")


def test_files_exist():
    assert MANIFEST.exists()
    assert DOC.exists()


def test_doc_contains_core_canon_sections():
    doc = text(DOC)
    assert "UNIVERSAL-AUTO" in doc
    assert "Mother equation" in doc
    assert "Universal Knowledge Graph" in doc
    assert "Universal Compiler" in doc
    assert "Universal Repair" in doc


def test_manifest_contains_core_status_and_equation():
    manifest = text(MANIFEST)
    assert "status: oak_safe_scaffold" in manifest
    assert "- Univers" in manifest
    assert "- Observation" in manifest
    assert "- New capability" in manifest
    assert "AUTO_REPAIR_SAFE" in manifest


def test_manifest_declares_contract_terms():
    manifest = text(MANIFEST)
    for key in ["owner", "domain", "allowed_artifacts", "oak_gates", "rollback", "m_plus", "m_minus"]:
        assert key in manifest


def test_manifest_declares_engine_families_and_core_engines():
    manifest = text(MANIFEST)
    for family in ["repository:", "memory:", "knowledge:", "theory:", "build:", "risk:"]:
        assert family in manifest
    for engine in ["AIT-GitHub", "AIT-CI", "AIT-M-Plus", "AIT-M-Minus", "AIT-Theory", "AIT-Green", "AIT-OAK"]:
        assert f"name: {engine}" in manifest


def test_seed_memory_ids_are_unique():
    manifest = text(MANIFEST)
    ids = [
        "green_ci_safe_merge_pattern",
        "declared_projection_validation",
        "mergeable_false_blocks_merge",
        "draft_blocks_merge",
        "duplicate_reports_are_noise",
    ]
    for item_id in ids:
        assert count_id(manifest, item_id) == 1
