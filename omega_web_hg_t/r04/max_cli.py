from __future__ import annotations

import argparse
import json
from pathlib import Path

from .max_adapters import MAX_ADAPTERS
from .max_campaign import run_max_campaign


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ω-WEB-HG R0.4 MAX metadata absorption campaign")
    sub = parser.add_subparsers(dest="command", required=True)

    catalog = sub.add_parser("catalog")
    catalog.add_argument("--pretty", action="store_true")

    run = sub.add_parser("run")
    run.add_argument("--output-dir", default="generated/omega_web_hg_r04_max")
    run.add_argument("--query", default="hypergraph")
    run.add_argument("--item-budget", type=int, default=500)
    run.add_argument("--page-size", type=int, default=25)
    run.add_argument("--max-pages-per-source", type=int, default=3)
    run.add_argument("--retries", type=int, default=3)
    run.add_argument("--max-bytes", type=int, default=2_097_152)
    run.add_argument("--resume", action="store_true")

    audit = sub.add_parser("audit")
    audit.add_argument("campaign_dir")

    args = parser.parse_args(argv)
    if args.command == "catalog":
        payload = [{"source_id": item.source_id, "name": item.name, "access_state": item.access_state, "required_env": list(item.required_env), "max_pages": item.max_pages, "requests_per_second": item.requests_per_second, "policy_url": item.policy_url, "metadata_only": item.metadata_only} for item in MAX_ADAPTERS]
        print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0
    if args.command == "run":
        root = run_max_campaign(args.output_dir, query=args.query, item_budget=args.item_budget, page_size=args.page_size, max_pages_per_source=args.max_pages_per_source, retries=args.retries, max_bytes=args.max_bytes, resume=args.resume)
        print(root / "campaign-report.json")
        return 0
    root = Path(args.campaign_dir)
    report = json.loads((root / "campaign-report.json").read_text(encoding="utf-8"))
    required = [root / "records.jsonl", root / "receipts.jsonl", root / "mminus.jsonl", root / "campaign.sqlite3", root / "checkpoint.json"]
    failures = [str(path) for path in required if not path.exists()]
    if report.get("metadata_only") is not True or report.get("raw_bodies_persisted") is not False or report.get("full_text_collected") is not False:
        failures.append("claim_boundary_violation")
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "failures": failures, "record_count": report.get("record_count"), "request_count": report.get("request_count"), "mminus_count": report.get("mminus_count"), "report_sha256": report.get("report_sha256")}, indent=2, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
