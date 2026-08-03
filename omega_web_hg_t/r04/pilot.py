from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from urllib.request import Request, urlopen

MAX_BYTES = 1_048_576
USER_AGENT = "Omega-Web-HG-R04/0.4 (+https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2)"


@dataclass(frozen=True)
class PilotTarget:
    source_id: str
    url: str


TARGETS = (
    PilotTarget(
        "wikimedia",
        "https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch=hypergraph&gsrlimit=3&prop=info&format=json&formatversion=2",
    ),
    PilotTarget(
        "crossref",
        "https://api.crossref.org/works?query.title=hypergraph&rows=3&select=DOI,title,published,URL,type",
    ),
    PilotTarget(
        "pubmed",
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=hypergraph&retmax=3&retmode=json&tool=omega_web_hg_r04",
    ),
    PilotTarget(
        "cern_open_data",
        "https://opendata.cern.ch/api/records/?q=physics&size=3",
    ),
    PilotTarget(
        "canada_open_government",
        "https://open.canada.ca/data/api/action/package_search?q=science&rows=3",
    ),
)


def _json_item_count(payload: Any) -> int | None:
    if isinstance(payload, list):
        return len(payload)
    if not isinstance(payload, dict):
        return None
    for path in (
        ("query", "pages"),
        ("message", "items"),
        ("esearchresult", "idlist"),
        ("hits", "hits"),
        ("result", "results"),
    ):
        node: Any = payload
        for key in path:
            if not isinstance(node, dict) or key not in node:
                node = None
                break
            node = node[key]
        if isinstance(node, list):
            return len(node)
    return None


def fetch_target(target: PilotTarget, timeout: float = 20.0) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    request = Request(
        target.url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/xml;q=0.8"},
        method="GET",
    )
    record: dict[str, Any] = {
        "source_id": target.source_id,
        "url": target.url,
        "method": "GET",
        "started_at": started.isoformat(),
        "max_bytes": MAX_BYTES,
        "full_text_collected": False,
        "raw_body_persisted": False,
    }
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
            truncated = len(body) > MAX_BYTES
            body = body[:MAX_BYTES]
            record.update(
                {
                    "status": int(response.status),
                    "content_type": response.headers.get("Content-Type"),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "bytes_received": len(body),
                    "truncated": truncated,
                    "response_sha256": hashlib.sha256(body).hexdigest(),
                }
            )
            try:
                payload = json.loads(body.decode("utf-8"))
                record["metadata_item_count"] = _json_item_count(payload)
                record["parse_status"] = "json_ok"
            except (UnicodeDecodeError, json.JSONDecodeError):
                record["metadata_item_count"] = None
                record["parse_status"] = "non_json_or_invalid_json"
    except Exception as exc:  # Network errors are evidence, not silent drops.
        record.update(
            {
                "status": None,
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
                "parse_status": "fetch_failed",
            }
        )
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    return record


def run_pilot(output_dir: str | Path, *, delay_seconds: float = 1.0) -> Path:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for index, target in enumerate(TARGETS):
        if index:
            time.sleep(max(0.0, delay_seconds))
        records.append(fetch_target(target))
    manifest = {
        "campaign": "omega-web-hg-r04-live-metadata-pilot-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "request_count": len(records),
        "successful_count": sum(1 for item in records if item.get("status") == 200),
        "metadata_only": True,
        "full_text_collected": False,
        "raw_bodies_persisted": False,
        "records": records,
        "oak_boundaries": {
            "response_hash_is_truth": False,
            "metadata_record_is_verified_claim": False,
            "successful_fetch_is_republication_permission": False,
            "pilot_is_complete_internet_absorption": False,
        },
    }
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    (root / "pilot-receipt.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded Ω-WEB-HG R0.4 live metadata pilot")
    parser.add_argument("--output-dir", default="generated/omega_web_hg_r04_live_pilot")
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    args = parser.parse_args(argv)
    output = run_pilot(args.output_dir, delay_seconds=args.delay_seconds)
    print(output / "pilot-receipt.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
