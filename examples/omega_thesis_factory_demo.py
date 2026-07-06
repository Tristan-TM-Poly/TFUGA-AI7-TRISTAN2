"""Demo for Ω-THESIS-2N-GIT-T.

Run:
    python examples/omega_thesis_factory_demo.py
"""

from __future__ import annotations

import json

from omega_thesis_factory_t.core import build_page_tree, example_seed, oak_report


def main() -> int:
    seed = example_seed()
    nodes = build_page_tree(seed, depth=3)
    report = oak_report(seed, nodes)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
