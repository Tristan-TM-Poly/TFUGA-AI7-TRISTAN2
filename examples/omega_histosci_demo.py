"""Minimal Ω-HISTOSCI-HG-T∞ R0.1 demonstration."""
from __future__ import annotations

import json

from omega_histosci_hg_t import build_report, build_seed


def main() -> None:
    graph, registry = build_seed()
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print("spectroscopy ancestors:", registry.ancestors_of("physics.optics.spectroscopy"))
    print("prism reachability:", graph.reachable(("instrument::prism",), max_depth=3))


if __name__ == "__main__":
    main()
