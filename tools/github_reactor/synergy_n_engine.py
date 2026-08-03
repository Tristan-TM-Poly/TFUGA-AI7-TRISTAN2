#!/usr/bin/env python3
"""Compatibility entry point for Ω-SYNERGY-N-T and Ω-SYNERGY-T∞ Foundry.

The original PR exposed ``discover``, ``search`` and ``write``. These names are
kept while the implementation now lives in the modular ``omega_synergy_t``
package.
"""
from __future__ import annotations

from pathlib import Path

from omega_synergy_t.cli import main
from omega_synergy_t.discovery import discover_n_order
from omega_synergy_t.models import CreationDNA as Node
from omega_synergy_t.models import SynergyCandidate as Candidate
from omega_synergy_t.reporting import write_foundry_bundle
from omega_synergy_t.scanner import ScannerPolicy, scan_repositories


def discover(roots, max_nodes: int = 800):
    result = scan_repositories([Path(root) for root in roots], ScannerPolicy(max_nodes=max_nodes))
    return result.creations, result.file_systems


def search(nodes, file_ids, max_order: int = 4, beam: int = 96, top: int = 25):
    result = discover_n_order(nodes, file_ids, max_order=max_order, beam_width=beam, top_k=top)
    pair_scores = {
        tuple(candidate.systems): candidate.score
        for candidate in result.get(2, [])
    }
    return result, pair_scores


def write(out, roots, nodes, result, _pair_scores, args):
    return write_foundry_bundle(
        Path(out),
        [Path(root) for root in roots],
        list(nodes),
        result,
        {
            "max_order": args.max_order,
            "beam_width": args.beam_width,
            "top_k": args.top_k,
            "max_nodes": args.max_nodes,
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
