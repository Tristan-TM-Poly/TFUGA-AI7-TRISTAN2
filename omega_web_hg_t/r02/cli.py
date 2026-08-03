from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .audit import audit_run
from .diffing import compare_run_directories
from .engine import IncrementalWebHypergraphCrawler
from .models import R02Config
from .state import StateStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-web-hg-r02", description="Ω-WEB-HG-T∞ R0.2: crawl incrémental, WARC, SQLite, sitemaps, feeds et diff temporel.")
    sub = parser.add_subparsers(dest="command", required=True)
    crawl = sub.add_parser("crawl", help="Exécuter ou reprendre une campagne incrémentale autorisée.")
    crawl.add_argument("url")
    crawl.add_argument("--output-root", default="generated/omega_web_hg_t_r02")
    crawl.add_argument("--allow-domain", action="append", default=[])
    crawl.add_argument("--include-subdomains", action="store_true")
    crawl.add_argument("--resource-budget", type=int, default=1000, help="0 retire le plafond fini du run.")
    crawl.add_argument("--max-depth", type=int, default=12, help="0 retire la limite de profondeur.")
    crawl.add_argument("--max-frontier", type=int, default=100000, help="0 retire le plafond de frontière.")
    crawl.add_argument("--delay", type=float, default=1.0)
    crawl.add_argument("--timeout", type=float, default=20.0)
    crawl.add_argument("--max-response-bytes", type=int, default=10_000_000)
    crawl.add_argument("--no-raw", action="store_true")
    crawl.add_argument("--no-warc", action="store_true")
    crawl.add_argument("--no-standard-discovery", action="store_true")
    crawl.add_argument("--no-sitemaps", action="store_true")
    crawl.add_argument("--no-feeds", action="store_true")
    crawl.add_argument("--ignore-meta-robots", action="store_true")
    crawl.add_argument("--user-agent", default="OmegaWebHG/0.2 (+https://github.com/Tristan-TM-Poly)")

    diff = sub.add_parser("diff", help="Comparer deux bundles de run sans appeler le réseau.")
    diff.add_argument("previous")
    diff.add_argument("current")
    diff.add_argument("--output")

    audit = sub.add_parser("audit", help="Auditer structure, références et hashes d'un bundle.")
    audit.add_argument("run_dir")

    state = sub.add_parser("state", help="Afficher les compteurs de l'état SQLite persistant.")
    state.add_argument("output_root")
    return parser


def _optional_budget(value: int) -> int | None:
    if value < 0:
        raise ValueError("budget values must be >= 0")
    return None if value == 0 else value


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "crawl":
            config = R02Config(seed_url=args.url, allowed_domains=tuple(args.allow_domain), include_subdomains=args.include_subdomains, user_agent=args.user_agent, resource_budget=_optional_budget(args.resource_budget), max_depth=_optional_budget(args.max_depth), max_frontier=_optional_budget(args.max_frontier), max_response_bytes=args.max_response_bytes, delay_seconds=args.delay, timeout_seconds=args.timeout, store_raw=not args.no_raw, store_warc=not args.no_warc, discover_standard_endpoints=not args.no_standard_discovery, discover_sitemaps=not args.no_sitemaps, discover_feeds=not args.no_feeds, respect_meta_robots=not args.ignore_meta_robots)
            bundle = IncrementalWebHypergraphCrawler(config).crawl(args.output_root)
            run_dir = Path(args.output_root) / "runs" / bundle.run_id
            print(json.dumps({"run_dir": str(run_dir), **bundle.oak_report()}, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if bundle.crawl.pages else 1
        if args.command == "diff":
            result = compare_run_directories(args.previous, args.current)
            payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
            if args.output:
                Path(args.output).write_text(payload, encoding="utf-8")
            print(payload)
            return 0
        if args.command == "audit":
            result = audit_run(args.run_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS_R0_2" else 1
        if args.command == "state":
            with StateStore(Path(args.output_root) / "state.sqlite3") as store:
                print(json.dumps(store.stats(), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"omega-web-hg-r02: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
