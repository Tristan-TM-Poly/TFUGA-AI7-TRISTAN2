import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "OMEGA_GITHUB_BRAIN_T.md"
SCHEMA = ROOT / "data" / "github_brain_schema.json"
SEED = ROOT / "data" / "github_brain_seed.yaml"


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_github_brain_files_exist():
    assert DOC.exists()
    assert SCHEMA.exists()
    assert SEED.exists()


def test_schema_is_valid_json_and_names_required_fields():
    schema = json.loads(read(SCHEMA))
    assert schema["title"] == "Omega GitHub Brain Seed"
    required = set(schema["required"])
    assert "lobes" in required
    assert "green_tensor_axes" in required
    assert "repository_genome_fields" in required
    assert "m_plus" in required
    assert "m_minus" in required


def test_seed_mentions_core_lobes_and_axes():
    seed = read(SEED)
    for lobe in ["Math lobe", "Energy lobe", "Kernel lobe", "Harness lobe"]:
        assert lobe in seed
    for axis in ["documentation", "tests", "ci", "oak", "rollback", "m_plus", "m_minus"]:
        assert f"- {axis}" in seed


def test_doc_preserves_metaphor_boundary_and_living_canon():
    doc = read(DOC)
    assert "architecture metaphor" in doc
    assert "Living Canon" in doc
    assert "Universal Theory Card" in doc
    assert "Repository Genome" in doc
    assert "Self-Repair Atlas" in doc


def test_memory_seed_ids_are_unique_by_count():
    seed = read(SEED)
    ids = [
        "pr_210_cognitive_os_canon",
        "pr_209_oakbench_scoring",
        "pr_25_effective_projection_validation",
        "draft_blocks_merge",
        "mergeable_false_blocks_merge",
        "metaphor_not_proof",
    ]
    for item_id in ids:
        assert seed.count(f"id: {item_id}") == 1
