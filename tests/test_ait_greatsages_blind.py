import json

from sage_tristan.greatsages import get_profile
from sage_tristan.greatsages_blind import compile_blind_packs, contestant_payload, evaluator_payload


GAUSS = get_profile("gauss")


def test_contestant_pack_hides_target_identity_content_and_descendants():
    target_id = "gauss_1801_ceres"
    contestant, evaluator = compile_blind_packs(GAUSS, target_id)
    payload = contestant_payload(GAUSS, target_id)
    serialized = json.dumps(payload, sort_keys=True)

    target = next(item for item in GAUSS.discoveries if item.discovery_id == target_id)
    assert target_id not in serialized
    assert target.title not in serialized
    assert target.problem not in serialized
    assert target.compressed_invariant not in serialized
    assert "gauss_1809_theoria_motus" not in contestant.visible_discovery_ids
    assert payload["metadata_leakage_detected"] is False
    assert contestant.target_content_withheld is True
    assert contestant.descendant_content_withheld is True
    assert contestant.tournament_id == evaluator.tournament_id


def test_evaluator_pack_retains_secret_target_for_scoring_only():
    payload = evaluator_payload(GAUSS, "gauss_1801_ceres")
    assert payload["target_discovery_id"] == "gauss_1801_ceres"
    assert "gauss_1809_theoria_motus" in payload["masked_discovery_ids"]
    assert "gauss_1809_theoria_motus" in payload["descendants_masked"]
    assert len(payload["target_digest"]) == 64


def test_opaque_tournament_id_does_not_contain_target_id():
    contestant, _ = compile_blind_packs(GAUSS, "gauss_1796_17gon")
    assert "gauss_1796_17gon" not in contestant.tournament_id
    assert contestant.tournament_id.startswith("blind::gauss::")
