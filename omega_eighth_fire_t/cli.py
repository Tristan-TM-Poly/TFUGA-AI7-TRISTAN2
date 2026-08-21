from __future__ import annotations

import argparse
import json

from .core import evaluate
from .io import load_proposal


def main() -> int:
    parser = argparse.ArgumentParser(prog="omega-eighth-fire")
    parser.add_argument("proposal", help="Proposal JSON")
    parser.add_argument("--fail-on-hold", action="store_true", help="Return 2 when constitutional gates HOLD")
    args = parser.parse_args()
    receipt = evaluate(load_proposal(args.proposal))
    print(json.dumps(receipt.to_dict(), indent=2, ensure_ascii=False))
    return 2 if args.fail_on_hold and receipt.decision == "HOLD" else 0


if __name__ == "__main__":
    raise SystemExit(main())
