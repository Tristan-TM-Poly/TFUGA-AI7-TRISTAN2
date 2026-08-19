from __future__ import annotations

import json
from dataclasses import asdict

from .evidence import borophene_2026_seed


def main() -> int:
    print(json.dumps([asdict(claim) for claim in borophene_2026_seed()], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
