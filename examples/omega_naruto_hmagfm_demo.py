"""Minimal deterministic demo for Ω-NARUTO-HMAGFM-HGFMnD² R1.2."""

from __future__ import annotations

import json

from omega_naruto_hmagfm.cli import build_report


def main() -> None:
    report = build_report()
    summary = {
        "schema": report["schema"],
        "accepted_claim_id": report["accepted"]["claim_id"],
        "publication_decision": report["publication_gate"]["decision"],
        "release_allowed": report["publication_gate"]["release_allowed"],
        "oak_merge_correct_on_fixture": report["benchmark"]["oak_merge_correct"],
        "majority_vote_correct_on_fixture": report["benchmark"]["majority_vote_correct"],
        "robustness_stable_fraction": report["robustness"]["stable_fraction"],
        "graph_nodes": len(report["hgfmn_graph"]["nodes"]),
        "graph_edges": len(report["hgfmn_graph"]["edges"]),
        "non_claim": report["oak_boundary"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
