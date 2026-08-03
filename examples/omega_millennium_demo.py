"""Standalone Ω-MILLENNIUM-T∞ R0.1 demonstration."""
from __future__ import annotations

import json

from omega_millennium_t import compile_campaign, run_benchmark


def main() -> int:
    payload = {
        "benchmark": run_benchmark(),
        "campaign": compile_campaign(total_budget_units=100),
        "boundary": {
            "open_problem_solved": False,
            "software_fixture_validated": True,
            "human_mathematical_review_required": True,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
