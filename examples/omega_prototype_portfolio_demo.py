from omega_prototype_portfolio_t.core import analyze, plan
from omega_prototype_portfolio_t.seed import seed_snapshot

snapshot = seed_snapshot()
analysis = analyze(snapshot)
portfolio_plan = plan(snapshot)
print(snapshot.snapshot_id, snapshot.sha256)
for item in portfolio_plan["selected"]:
    print(item["prototype_id"], item["priority"], item["action"]["title"])
