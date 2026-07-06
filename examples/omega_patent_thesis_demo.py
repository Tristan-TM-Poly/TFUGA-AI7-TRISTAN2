"""Demo for Omega Patent Thesis T."""

from __future__ import annotations

import json

from omega_patent_thesis_t import claim_tree, example_seed, gitpack_paths, risk_level, value_map


def main() -> int:
    seed = example_seed()
    payload = {
        "seed": seed.to_dict(),
        "claim_tree": claim_tree(seed),
        "risk_level": risk_level(seed),
        "value_map": value_map(seed),
        "gitpack": gitpack_paths(seed),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
