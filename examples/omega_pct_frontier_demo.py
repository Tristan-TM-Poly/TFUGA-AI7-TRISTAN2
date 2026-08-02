from omega_pct_t.frontier import AdaptiveFrontier, FrontierBudget, synthetic_particle_candidates

budget = FrontierBudget(max_seconds=0.2, initial_batch=128, max_failures=10)
engine = AdaptiveFrontier(budget)
state = engine.run(
    synthetic_particle_candidates(32),
    "generated/omega_pct_t/frontier-demo/candidates.jsonl",
    lambda item: (True, 1.0, "ok"),
    lambda item: item["id"],
)
print(state)
