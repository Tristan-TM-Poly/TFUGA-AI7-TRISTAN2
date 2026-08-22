from sage_tristan.greatsages_polycentric import (
    AccessDecision,
    ActorKind,
    AttributionRole,
    CivilizationZoomTensor,
    TranslationLossTensor,
    software_fixture,
)


def test_world_existence_does_not_imply_access():
    atlas = software_fixture()
    receipt = atlas.access("fixture_school_b", "fixture_atom_1", 150)
    assert receipt.decision is AccessDecision.UNKNOWN_ACCESS
    assert receipt.world_existence_implies_access is False


def test_explicit_access_edge_allows_knowledge_after_date():
    atlas = software_fixture()
    receipt = atlas.access("fixture_person_a", "fixture_atom_1", 120)
    assert receipt.decision is AccessDecision.ALLOWED
    assert receipt.matched_edge_ids == ("access_a_1",)
    assert receipt.evidence_score == 0.81


def test_translation_bridge_is_required_for_language_mismatch():
    atlas = software_fixture()
    before = atlas.access("fixture_school_b", "fixture_atom_1", 155)
    after = atlas.access("fixture_school_b", "fixture_atom_1", 170)
    assert before.decision is AccessDecision.UNKNOWN_ACCESS
    assert after.decision is AccessDecision.ALLOWED
    assert after.translation_loss is not None
    assert after.translation_loss > 0


def test_future_world_atom_is_blocked_even_if_access_edge_exists_later():
    atlas = software_fixture()
    receipt = atlas.access("fixture_network_c", "fixture_atom_2", 140)
    assert receipt.decision is AccessDecision.BLOCKED_FUTURE


def test_attribution_is_parallax_not_single_author_field():
    atlas = software_fixture()
    facets = atlas.attribution_parallax("fixture_atom_1")
    roles = {facet.role for facet in facets}
    actors = {facet.actor_id for facet in facets}
    assert AttributionRole.FIRST_KNOWN_EVIDENCE in roles
    assert AttributionRole.TRANSLATION in roles
    assert len(actors) == 2


def test_translation_loss_tensor_is_bounded_and_deterministic():
    loss = TranslationLossTensor(0.1, 0.2, 0.1, 0.3)
    assert loss.aggregate_loss == 0.185


def test_zoom_tensor_filters_without_ranking():
    atlas = software_fixture()
    sliced = atlas.zoom(CivilizationZoomTensor(time=170, regions=("region_b",)))
    assert "fixture_school_b" in sliced["actor_ids"]
    assert "fixture_network_c" in sliced["actor_ids"]
    assert "fixture_person_a" not in sliced["actor_ids"]


def test_actor_kinds_include_collective_structures():
    kinds = set(ActorKind)
    assert ActorKind.PERSON in kinds
    assert ActorKind.COLLECTIVE in kinds
    assert ActorKind.SCHOOL in kinds
    assert ActorKind.INSTITUTION in kinds
    assert ActorKind.TRADITION in kinds
    assert ActorKind.CIVILIZATION in kinds
    assert ActorKind.NETWORK in kinds
    assert ActorKind.ANONYMOUS_COMMUNITY in kinds
