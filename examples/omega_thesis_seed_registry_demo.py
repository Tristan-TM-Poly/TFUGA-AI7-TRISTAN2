"""Demo: expand all first five canonical ThesisSeeds.

Run:
    python examples/omega_thesis_seed_registry_demo.py
"""

from __future__ import annotations

import json

from omega_thesis_factory_t.core import build_page_tree, oak_report
from omega_thesis_factory_t.seed_registry import canonical_seeds


def main() -> int:
    payload = {}
    for seed_id, seed in canonical_seeds().items():
        nodes = build_page_tree(seed, depth=2)
        payload[seed_id] = oak_report(seed, nodes)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
