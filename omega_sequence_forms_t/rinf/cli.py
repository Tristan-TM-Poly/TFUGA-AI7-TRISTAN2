"""Command-line interface for Ω-SUITE-FORM-T∞ R∞."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..exact import normalize_terms
from .address import CellSpace, cell_space_receipt, sample_addresses
from .benchmark import run_benchmark
from .campaign import campaign_summary, run_campaign
from .catalog import catalog_payload, iter_catalog_records
from .hypergeometric import discover_hypergeometric
from .materialize import materialization_receipt, materialize_catalog, materialize_cells
from .models import CampaignBudget
from .orchestrator import DiscoveryLimits, discover_rinf
from .p_recursive import discover_p_recursive
from .quasipolynomial import discover_quasi_polynomials
from .rational_index import discover_rational_indices


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _parse_terms(text: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in text.split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("provide comma-separated terms")
    return values


def _budget_from_args(args: argparse.Namespace) -> CampaignBudget:
    return CampaignBudget(
        wall_time_seconds=args.wall_time,
        storage_megabytes=args.storage_mb,
        compute_units=args.compute_units,
        materialized_cell_cap=args.cells,
        minimum_marginal_value=getattr(args, "minimum_value", 0.0),
        minimum_value_cost_ratio=getattr(args, "minimum_ratio", 0.0),
    )


def discover_payload(args: argparse.Namespace) -> dict[str, object]:
    terms = normalize_terms(args.terms)
    candidates: list[dict[str, object]] = []
    if not args.families or "quasi" in args.families:
        candidates.extend(item.to_dict() for item in discover_quasi_polynomials(
            terms,
            max_period=args.max_period,
            max_degree=args.max_degree,
            holdout=args.holdout,
        ))
    if not args.families or "rational" in args.families:
        candidates.extend(item.to_dict() for item in discover_rational_indices(
            terms,
            max_numerator_degree=args.max_degree,
            max_denominator_degree=args.max_degree,
            holdout=args.holdout,
        ))
    if not args.families or "hyper" in args.families:
        candidates.extend(item.to_dict() for item in discover_hypergeometric(
            terms,
            max_numerator_degree=args.max_degree,
            max_denominator_degree=args.max_degree,
            holdout=args.holdout,
        ))
    if not args.families or "prec" in args.families:
        candidates.extend(item.to_dict() for item in discover_p_recursive(
            terms,
            max_order=args.max_order,
            max_degree=args.max_degree,
            holdout_equations=args.holdout,
        ))
    return {
        "schema": "omega-sequence-forms-rinf-discovery/1",
        "term_count": len(terms),
        "candidates": candidates,
        "candidate_count": len(candidates),
        "global_identity_proved": False,
    }


def orchestrate_payload(args: argparse.Namespace) -> dict[str, object]:
    limits = DiscoveryLimits(
        max_period=args.max_period,
        max_degree=args.max_degree,
        max_order=args.max_order,
        max_candidates_per_family=args.max_candidates_per_family,
        holdout=args.holdout,
    )
    return discover_rinf(args.terms, limits=limits).to_dict()


def _add_discovery_limits(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("terms", type=_parse_terms)
    parser.add_argument("--holdout", type=int)
    parser.add_argument("--max-period", type=int, default=32)
    parser.add_argument("--max-degree", type=int, default=8)
    parser.add_argument("--max-order", type=int, default=8)
    parser.add_argument("--output")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-sequence-forms-rinf")
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog = subparsers.add_parser("catalog")
    catalog.add_argument("--records", action="store_true")
    catalog.add_argument("--output")

    space = subparsers.add_parser("space")
    space.add_argument("--sample", type=int, default=8)
    space.add_argument("--seed", type=int, default=0)
    space.add_argument("--output")

    discover = subparsers.add_parser("discover")
    _add_discovery_limits(discover)
    discover.add_argument("--families", nargs="*", choices=("quasi", "rational", "hyper", "prec"))

    orchestrate = subparsers.add_parser("orchestrate")
    _add_discovery_limits(orchestrate)
    orchestrate.add_argument("--max-candidates-per-family", type=int, default=16)

    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--campaign-cells", type=int, default=512)
    benchmark.add_argument("--seed", type=int, default=314159)
    benchmark.add_argument("--output")

    campaign = subparsers.add_parser("campaign")
    campaign.add_argument("--campaign-id", default="rinf-campaign")
    campaign.add_argument("--seed", type=int, default=0)
    campaign.add_argument("--cells", type=int)
    campaign.add_argument("--compute-units", type=int)
    campaign.add_argument("--wall-time", type=float)
    campaign.add_argument("--storage-mb", type=int)
    campaign.add_argument("--minimum-value", type=float, default=0.0)
    campaign.add_argument("--minimum-ratio", type=float, default=0.0)
    campaign.add_argument("--initial-frontier", type=int, default=4096)
    campaign.add_argument("--output")

    materialize = subparsers.add_parser("materialize")
    materialize.add_argument("directory")
    materialize.add_argument("--seed", type=int, default=0)
    materialize.add_argument("--cells", type=int, default=100_000)
    materialize.add_argument("--compute-units", type=int)
    materialize.add_argument("--wall-time", type=float)
    materialize.add_argument("--storage-mb", type=int, default=512)
    materialize.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "catalog":
        payload = list(iter_catalog_records()) if args.records else catalog_payload()
    elif args.command == "space":
        cell_space = CellSpace()
        payload = cell_space_receipt(cell_space)
        payload["sample"] = [item.render() for item in sample_addresses(args.sample, seed=args.seed, space=cell_space)]
    elif args.command == "discover":
        payload = discover_payload(args)
    elif args.command == "orchestrate":
        payload = orchestrate_payload(args)
    elif args.command == "benchmark":
        payload = run_benchmark(campaign_cells=args.campaign_cells, seed=args.seed)
    elif args.command == "campaign":
        budget = _budget_from_args(args)
        receipt = run_campaign(
            campaign_id=args.campaign_id,
            seed=args.seed,
            budget=budget,
            initial_frontier=args.initial_frontier,
        )
        payload = campaign_summary(receipt)
    elif args.command == "materialize":
        directory = Path(args.directory)
        budget = _budget_from_args(args)
        catalog_stats = materialize_catalog(directory / "catalog.jsonl", budget=CampaignBudget(storage_megabytes=args.storage_mb))
        cell_stats = materialize_cells(directory / "cells.jsonl", seed=args.seed, budget=budget)
        payload = materialization_receipt(
            catalog_stats=catalog_stats,
            cell_stats=cell_stats,
            budget=budget,
            seed=args.seed,
        )
    else:  # pragma: no cover
        parser.error("unknown command")
        return 2

    _write(payload, args.output)
    return 0 if not isinstance(payload, dict) or payload.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
