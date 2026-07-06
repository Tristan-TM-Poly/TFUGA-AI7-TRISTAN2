"""Export demo for Omega Patent Thesis T."""

from __future__ import annotations

import json

from omega_patent_thesis_t.export import export_pack
from omega_patent_thesis_t.seed import example_seed


def main() -> int:
    print(json.dumps(export_pack(example_seed()), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
