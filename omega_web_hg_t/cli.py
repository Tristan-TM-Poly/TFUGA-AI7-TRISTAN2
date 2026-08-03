from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .core import CrawlConfig, PolicyGate, WebHypergraphCrawler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-web-hg",
        description="Ω-WEB-HG-T∞: exploration Web autorisée, hypergraphe et preuves OAK.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = sub.add_parser("inspect", help="Évaluer la portée, le réseau et robots.txt sans crawler la page.")
    inspect_cmd.add_argument("url")
    inspect_cmd.add_argument("--allow-domain", action="append", default=[])
    inspect_cmd.add_argument("--include-subdomains", action="store_true")
    inspect_cmd.add_argument("--user-agent", default="OmegaWebHG/0.1 (+https://github.com/Tristan-TM-Poly)")

    crawl = sub.add_parser("crawl", help="Construire un hypergraphe probatoire d'un site autorisé.")
    crawl.add_argument("url")
    crawl.add_argument("--output-dir", default="generated/omega_web_hg_t")
    crawl.add_argument("--allow-domain", action="append", default=[])
    crawl.add_argument("--include-subdomains", action="store_true")
    crawl.add_argument("--page-budget", type=int, default=100, help="Budget fini du run; 0 retire le plafond de pages.")
    crawl.add_argument("--delay", type=float, default=1.0, help="Délai minimal par domaine en secondes.")
    crawl.add_argument("--max-response-bytes", type=int, default=5_000_000)
    crawl.add_argument("--timeout", type=float, default=20.0)
    crawl.add_argument("--user-agent", default="OmegaWebHG/0.1 (+https://github.com/Tristan-TM-Poly)")
    crawl.add_argument("--no-raw", action="store_true", help="Ne pas conserver les corps HTML bruts.")
    return parser


def config_from_args(args: argparse.Namespace) -> CrawlConfig:
    page_budget = None if getattr(args, "page_budget", 1) == 0 else getattr(args, "page_budget", 100)
    return CrawlConfig(
        seed_url=args.url,
        allowed_domains=tuple(args.allow_domain),
        include_subdomains=args.include_subdomains,
        user_agent=args.user_agent,
        page_budget=page_budget,
        max_response_bytes=getattr(args, "max_response_bytes", 5_000_000),
        delay_seconds=getattr(args, "delay", 1.0),
        timeout_seconds=getattr(args, "timeout", 20.0),
        store_raw=not getattr(args, "no_raw", False),
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = config_from_args(args)
        if args.command == "inspect":
            decision = PolicyGate(config).decide(args.url)
            print(json.dumps(decision.__dict__, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if decision.allowed else 1
        if args.command == "crawl":
            result = WebHypergraphCrawler(config).crawl()
            output = result.write(args.output_dir)
            print(json.dumps({"output_dir": str(output), **result.oak_report()}, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if result.pages else 1
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"omega-web-hg: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Commande non gérée: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
