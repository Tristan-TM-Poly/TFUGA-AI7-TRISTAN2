import pathlib

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "universal_auto2_engines.yaml"
DOC = ROOT / "docs" / "OMEGA_UNIVERSAL_AUTO2_OS_T.md"


def load_manifest():
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_and_doc_exist():
    assert MANIFEST.exists()
    assert DOC.exists()
    assert "UNIVERSAL-AUTO" in DOC.read_text(encoding="utf-8")


def test_manifest_has_oak_statuses_and_mother_equation():
    data = load_manifest()
    assert data["status"] == "oak_safe_scaffold"
    assert data["mother_equation"][0] == "Univers"
    assert data["mother_equation"][-1] == "New capability"
    assert "AUTO_REPAIR_SAFE" in data["statuses"]["allowed"]
    assert "AUTO_BLOCK_SENSITIVE_SCOPE" in data["statuses"]["allowed"]


def test_every_engine_has_contract_fields():
    data = load_manifest()
    required = set(data["engine_contract"]["required_metadata"])
    for family_name, engines in data["engine_families"].items():
        assert engines, family_name
        for engine in engines:
            missing = required - set(engine)
            assert not missing, f"{engine['name']} missing {missing}"
            assert engine["allowed_artifacts"], engine["name"]
            assert engine["oak_gates"], engine["name"]
            assert engine["rollback"], engine["name"]


def test_m_plus_and_m_minus_are_unique():
    data = load_manifest()
    m_plus_ids = [item["id"] for item in data["seed_m_plus"]]
    m_minus_ids = [item["id"] for item in data["seed_m_minus"]]
    assert len(m_plus_ids) == len(set(m_plus_ids))
    assert len(m_minus_ids) == len(set(m_minus_ids))
    assert "mergeable_false_blocks_merge" in m_minus_ids
    assert "draft_blocks_merge" in m_minus_ids


def test_oak_gate_names_are_non_empty_strings():
    data = load_manifest()
    for engines in data["engine_families"].values():
        for engine in engines:
            for gate in engine["oak_gates"]:
                assert isinstance(gate, str)
                assert gate.strip()
