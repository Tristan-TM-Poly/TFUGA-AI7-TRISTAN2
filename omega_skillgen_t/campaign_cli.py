from __future__ import annotations

import argparse
import json

from .core import load_json
from .campaign import run_static_campaign


def main() -> int:
    parser = argparse.ArgumentParser(prog="omega-skillgen-campaign")
    parser.add_argument("spec")
    parser.add_argument("out")
    args = parser.parse_args()
    report = run_static_campaign(load_json(args.spec), args.out)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
