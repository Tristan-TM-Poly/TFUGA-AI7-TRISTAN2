import hashlib
import json

from omega_plasma_t.materialize_atlas import materialize


def test_materialized_atlas_is_large_hashed_and_uncertified(tmp_path):
    manifest = materialize(tmp_path, shard_size=500)
    assert manifest["permanent_cap"] is False
    assert manifest["counts"]["regime_cells"] > 10_000
    assert manifest["counts"]["instability_diagnostic_pairs"] == 1_200
    assert manifest["counts"]["benchmark_model_pairs"] == 660
    assert manifest["counts"]["model_transitions"] == 462
    assert manifest["authority"]["hardware_actions"] == 0
    assert manifest["authority"]["automatic_main_merge"] is False

    stored = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert stored["epistemic_status"] == "generated_candidate_objects_not_certified"
    for item in stored["files"]:
        path = tmp_path / item["file"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
