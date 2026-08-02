from omega_pct_t.frontier import AdaptiveFrontier, FrontierBudget, synthetic_particle_candidates


def test_frontier_has_no_item_ceiling_and_stops_on_byte_budget(tmp_path):
    budget = FrontierBudget(max_bytes=5000, initial_batch=8, max_failures=5)
    engine = AdaptiveFrontier(budget)
    state = engine.run(
        synthetic_particle_candidates(4), tmp_path / "items.jsonl",
        lambda item: (True, 1.0, "ok"), lambda item: item["id"],
    )
    assert state.stop_reason == "byte_budget"
    assert state.accepted > 0
    assert state.processed >= state.accepted
    assert state.frontier_digest


def test_frontier_records_quality_rejections_in_m_minus(tmp_path):
    budget = FrontierBudget(max_seconds=0.02, initial_batch=4, target_quality=0.9)
    engine = AdaptiveFrontier(budget)
    state = engine.run(
        synthetic_particle_candidates(2), tmp_path / "items.jsonl",
        lambda item: (item["ordinal"] % 2 == 0, 1.0 if item["ordinal"] % 2 == 0 else 0.0, "odd rejected"),
        lambda item: item["id"],
    )
    assert state.rejected > 0
    assert state.m_minus
    assert state.batch_size >= 1
