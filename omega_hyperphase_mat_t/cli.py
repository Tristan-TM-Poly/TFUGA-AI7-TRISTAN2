from __future__ import annotations

import argparse
import json

from .claims import CLAIMS
from .examples import four_site_topology_ensemble
from .model import finite_size_crossover


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω-HYPERPHASE-MAT-T finite hypergraph thermodynamics reference model")
    parser.add_argument("--t-min", type=float, default=0.5)
    parser.add_argument("--t-max", type=float, default=5.0)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--structural-penalty", type=float, default=0.8)
    parser.add_argument("--claims", action="store_true", help="emit the OAK claims registry")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.claims:
        print(json.dumps([claim.__dict__ for claim in CLAIMS], indent=2, sort_keys=True))
        return 0
    if args.steps < 2:
        raise SystemExit("--steps must be >= 2")
    if args.t_min <= 0 or args.t_max <= args.t_min:
        raise SystemExit("require 0 < --t-min < --t-max")
    ensemble = four_site_topology_ensemble(structural_penalty=args.structural_penalty)
    temperatures = [
        args.t_min + i * (args.t_max - args.t_min) / (args.steps - 1)
        for i in range(args.steps)
    ]
    states = ensemble.sweep(temperatures)
    marker = finite_size_crossover(states)
    payload = {
        "model": "OMEGA-HYPERPHASE-MAT-T-R1",
        "oak_status": "FINITE_REFERENCE_MODEL_NOT_BULK_PHASE_PROOF",
        "topology_dynamic": ensemble.topology_is_dynamic,
        "crossover": marker.__dict__,
        "states": [
            {
                "temperature": s.temperature,
                "free_energy": s.free_energy,
                "internal_energy": s.internal_energy,
                "entropy": s.entropy,
                "topology_entropy": s.topology_entropy,
                "conditional_configuration_entropy": s.conditional_configuration_entropy,
                "entropy_chain_residual": s.entropy_chain_residual,
                "heat_capacity": s.heat_capacity,
                "susceptibility": s.susceptibility,
                "mean_abs_magnetization": s.mean_abs_magnetization,
                "mean_active_edge_count": s.mean_active_edge_count,
                "hypergraph_probabilities": s.hypergraph_probabilities,
            }
            for s in states
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
