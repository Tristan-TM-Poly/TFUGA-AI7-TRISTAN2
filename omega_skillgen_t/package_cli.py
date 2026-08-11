from __future__ import annotations

import argparse
import json

from .package import build_standalone_bundle


def main() -> int:
    parser = argparse.ArgumentParser(prog="omega-skillgen-package")
    parser.add_argument("repo_root")
    parser.add_argument("out_zip")
    args = parser.parse_args()
    result = build_standalone_bundle(args.repo_root, args.out_zip)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
