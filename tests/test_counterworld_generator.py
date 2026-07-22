from tools.counterworld_generator import CounterworldKind, generate_counterworlds


def test_counterworld_pack_contains_six_worlds():
    pack = generate_counterworlds("Reality Forge")
    assert len(pack.worlds) == 6
    assert {world.kind for world in pack.worlds} == {
        CounterworldKind.SUCCESS,
        CounterworldKind.FAILURE,
        CounterworldKind.ABUSE,
        CounterworldKind.COST,
        CounterworldKind.LIMIT,
        CounterworldKind.COUNTEREXAMPLE,
    }


def test_elevated_context_requires_review_for_risky_worlds():
    pack = generate_counterworlds("Review-gated automation", high_stakes=True)
    risky_world = next(world for world in pack.worlds if world.kind == CounterworldKind.ABUSE)
    assert "qualified human validation" in risky_world.oak_response
