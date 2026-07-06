"""Demo: build packs and company maps for all canonical seeds.

Run:
    python examples/omega_thesis_pack_company_demo.py
"""

from __future__ import annotations

import json

from omega_thesis_factory_t.company_map import company_map
from omega_thesis_factory_t.pack import make_pack
from omega_thesis_factory_t.seed_registry import canonical_seeds


def main() -> int:
    payload = {}
    for seed_id, seed in canonical_seeds().items():
        payload[seed_id] = {
            "pack_report": make_pack(seed, depth=2)["report"],
            "company_map": company_map(seed),
        }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
