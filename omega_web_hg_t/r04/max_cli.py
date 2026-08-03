from __future__ import annotations

import argparse
import json
from pathlib import Path

from .max_adapters import MAX_ADAPTERS
from .max_campaign import run_max_campaign
from .max_models import digest_object
from .max_sharding import aggregate_shards, build_shard_matrix, select_adapter_shard


def _write_shard_config(
    root: Path,
    *,
    shard_index: int,
    shard_count: int,
    query: str,
    selected_sources: list[str],
    resume: bool,
) -> dict[str, object]:
    config = {
        "schema": "omega-web-hg-r04-max-shard-config/1.0",
        "shard_index": shard_index,
        "shard_count": shard_count,
        "query": query,
        "selected_sources": selected_sources,
    }
    config["config_sha256"] = digest_object(config)
    path = root / "shard-config.json"
    if resume:
        if not path.exists():
            raise ValueError("resume requested without shard-config.json")
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous.get("config_sha256") != config["config_sha256"]:
            raise ValueError("resume shard configuration mismatch")
    else:
        root.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return config


def _annotate_report(root: Path, config: dict[str, object]) -> None:
    path = root / "campaign-report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    report["campaign_id"] = (
        f"omega-web-hg-r04-max-metadata-s{config['shard_index']}"
        f"-of-{config['shard_count']}"
    )
    report["shard"] = {
        "index": config["shard_index"],
        "count": config["shard_count"],
        "selected_sources": config["selected_sources"],
        "config_sha256": config["config_sha256"],
    }
    report["report_sha256"] = digest_object(
        {key: value for key, value in report.items() if key != "report_sha256"}
    )
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ω-WEB-HG R0.4 MAX metadata absorption campaign"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    catalog = sub.add_parser("catalog")
    catalog.add_argument("--pretty", action="store_true")

    matrix = sub.add_parser("matrix")
    matrix.add_argument("--shard-count", type=int, required=True)

    run = sub.add_parser("run")
    run.add_argument("--output-dir", default="generated/omega_web_hg_r04_max")
    run.add_argument("--query", default="hypergraph")
    run.add_argument("--item-budget", type=int, default=500)
    run.add_argument("--page-size", type=int, default=25)
    run.add_argument("--max-pages-per-source", type=int, default=3)
    run.add_argument("--retries", type=int, default=3)
    run.add_argument("--max-bytes", type=int, default=2_097_152)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--shard-index", type=int, default=0)
    run.add_argument("--shard-count", type=int, default=1)

    audit = sub.add_parser("audit")
    audit.add_argument("campaign_dir")

    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("input_root")
    aggregate.add_argument("--output-dir", required=True)
    aggregate.add_argument("--expected-shards", type=int)

    args = parser.parse_args(argv)

    if args.command == "catalog":
        payload = [
            {
                "source_id": item.source_id,
                "name": item.name,
                "access_state": item.access_state,
                "required_env": list(item.required_env),
                "max_pages": item.max_pages,
                "requests_per_second": item.requests_per_second,
                "policy_url": item.policy_url,
                "metadata_only": item.metadata_only,
            }
            for item in MAX_ADAPTERS
        ]
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2 if args.pretty else None,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "matrix":
        print(json.dumps(build_shard_matrix(args.shard_count), separators=(",", ":")))
        return 0

    if args.command == "run":
        selected = select_adapter_shard(
            MAX_ADAPTERS,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
        )
        root_path = Path(args.output_dir)
        config = _write_shard_config(
            root_path,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
            query=args.query,
            selected_sources=[item.source_id for item in selected],
            resume=args.resume,
        )
        root = run_max_campaign(
            root_path,
            query=args.query,
            item_budget=args.item_budget,
            page_size=args.page_size,
            max_pages_per_source=args.max_pages_per_source,
            retries=args.retries,
            max_bytes=args.max_bytes,
            resume=args.resume,
            adapters=selected,
        )
        _annotate_report(root, config)
        print(root / "campaign-report.json")
        return 0

    if args.command == "aggregate":
        root = aggregate_shards(
            args.input_root,
            args.output_dir,
            expected_shards=args.expected_shards,
        )
        report = json.loads((root / "aggregate-report.json").read_text(encoding="utf-8"))
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["complete"] else 2

    root = Path(args.campaign_dir)
    report = json.loads((root / "campaign-report.json").read_text(encoding="utf-8"))
    required = [
        root / "records.jsonl",
        root / "receipts.jsonl",
        root / "mminus.jsonl",
        root / "campaign.sqlite3",
        root / "checkpoint.json",
        root / "shard-config.json",
    ]
    failures = [str(path) for path in required if not path.exists()]
    if (
        report.get("metadata_only") is not True
        or report.get("raw_bodies_persisted") is not False
        or report.get("full_text_collected") is not False
    ):
        failures.append("claim_boundary_violation")
    shard = report.get("shard") or {}
    if not isinstance(shard.get("selected_sources"), list):
        failures.append("missing_shard_provenance")
    print(
        json.dumps(
            {
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
                "record_count": report.get("record_count"),
                "request_count": report.get("request_count"),
                "mminus_count": report.get("mminus_count"),
                "shard": shard,
                "report_sha256": report.get("report_sha256"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
