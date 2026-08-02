from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import write_mesh


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-intercompany-mesh")
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(write_mesh(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
