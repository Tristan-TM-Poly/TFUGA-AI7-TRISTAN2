from __future__ import annotations

import argparse
import json
import os

from .plan import build_plan, load_constellation


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ω-REPO-GENESIS-T∞")
    p.add_argument("constellation")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--threshold", type=float, default=0.72)
    args = p.parse_args(argv)

    constellation = load_constellation(args.constellation)
    if not args.execute:
        print(json.dumps(build_plan(constellation, threshold=args.threshold), indent=2, sort_keys=True))
        return 0

    token = os.environ.get("TRISTAN_GITHUB_REPO_FACTORY_TOKEN", "")
    if not token:
        raise SystemExit("HOLD: repository-creation connector/token is not available in this runtime")
    from .github_api import GitHubRepoFactory
    receipt = GitHubRepoFactory(token).materialize(constellation, threshold=args.threshold)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0
