from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Callable, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .max_adapters import Adapter, MAX_ADAPTERS
from .max_models import NegativeMemoryEntry, NormalizedRecord, RequestReceipt, canonical_json, digest_object

USER_AGENT = "Omega-Web-HG-R04-MAX/0.4 (+https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2)"
DEFAULT_MAX_BYTES = 2_097_152


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes
    final_url: str


Transport = Callable[[str, Mapping[str, str], float, int], HttpResponse]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_transport(url: str, headers: Mapping[str, str], timeout: float, max_bytes: int) -> HttpResponse:
    request = Request(url, headers=dict(headers), method="GET")
    with urlopen(request, timeout=timeout) as response:
        body = response.read(max_bytes + 1)
        return HttpResponse(int(response.status), dict(response.headers.items()), body, response.geturl())


def _merkle_root(digests: Iterable[str]) -> str:
    layer = [bytes.fromhex(item) for item in sorted(digests)]
    if not layer:
        return hashlib.sha256(b"").hexdigest()
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [hashlib.sha256(layer[i] + layer[i + 1]).digest() for i in range(0, len(layer), 2)]
    return layer[0].hex()


def _init_db(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("CREATE TABLE IF NOT EXISTS records (digest TEXT PRIMARY KEY, source_id TEXT NOT NULL, record_id TEXT NOT NULL, payload TEXT NOT NULL)")
    con.execute("CREATE INDEX IF NOT EXISTS records_source_idx ON records(source_id)")
    con.execute("CREATE TABLE IF NOT EXISTS receipts (digest TEXT PRIMARY KEY, source_id TEXT NOT NULL, request_id TEXT NOT NULL, payload TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS mminus (digest TEXT PRIMARY KEY, source_id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL)")
    con.commit()
    return con


def _write_checkpoint(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _retry_delay(headers: Mapping[str, str], attempt: int) -> float:
    value = headers.get("Retry-After") or headers.get("retry-after")
    if value:
        try:
            return max(0.0, min(float(value), 120.0))
        except ValueError:
            pass
    return min(2.0 ** max(0, attempt - 1), 60.0)


def _header(headers: Mapping[str, str], name: str) -> str | None:
    lower = name.lower()
    for key, value in headers.items():
        if key.lower() == lower:
            return str(value)
    return None


def run_max_campaign(
    output_dir: str | Path,
    *,
    query: str = "hypergraph",
    item_budget: int = 500,
    page_size: int = 25,
    max_pages_per_source: int = 3,
    timeout: float = 25.0,
    retries: int = 3,
    max_bytes: int = DEFAULT_MAX_BYTES,
    resume: bool = False,
    adapters: Iterable[Adapter] = MAX_ADAPTERS,
    env: Mapping[str, str] | None = None,
    transport: Transport = default_transport,
    sleep: Callable[[float], None] = time.sleep,
) -> Path:
    if item_budget < 1 or page_size < 1 or max_pages_per_source < 1 or retries < 1 or max_bytes < 1024:
        raise ValueError("invalid finite campaign budget")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    env_map = dict(os.environ if env is None else env)
    checkpoint_path = root / "checkpoint.json"
    db = _init_db(root / "campaign.sqlite3")
    state = {"adapter_index": 0, "page": 1, "records": 0, "requests": 0}
    if resume and checkpoint_path.exists():
        loaded = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        for key in state:
            if key in loaded:
                state[key] = int(loaded[key])
    elif not resume:
        for table in ("records", "receipts", "mminus"):
            db.execute(f"DELETE FROM {table}")
        db.commit()
    adapter_list = tuple(adapters)
    records_written = int(state["records"])
    requests_made = int(state["requests"])
    skipped: list[dict[str, object]] = []
    started_at = utc_now()
    try:
        for adapter_index, adapter in enumerate(adapter_list):
            if adapter_index < int(state["adapter_index"]):
                continue
            missing = adapter.missing_env(env_map)
            if missing:
                skipped.append({"source_id": adapter.source_id, "reason": "missing_required_environment", "required_env": list(missing)})
                state.update({"adapter_index": adapter_index + 1, "page": 1, "records": records_written, "requests": requests_made})
                _write_checkpoint(checkpoint_path, state)
                continue
            source_pages = min(adapter.max_pages, max_pages_per_source)
            first_page = int(state["page"]) if adapter_index == int(state["adapter_index"]) else 1
            for page in range(first_page, source_pages + 1):
                if records_written >= item_budget:
                    break
                url = adapter.url_builder(query, page, min(page_size, item_budget - records_written), env_map)
                request_id = hashlib.sha256(f"{adapter.source_id}\0{url}\0{page}".encode("utf-8")).hexdigest()
                headers = {"User-Agent": USER_AGENT, "Accept": "application/json, application/xml;q=0.9, text/xml;q=0.8", "Accept-Encoding": "identity"}
                receipt: RequestReceipt | None = None
                parsed: list[NormalizedRecord] = []
                for attempt in range(1, retries + 1):
                    began = utc_now()
                    response_headers: Mapping[str, str] = {}
                    try:
                        response = transport(url, headers, timeout, max_bytes)
                        response_headers = response.headers
                        requests_made += 1
                        truncated = len(response.body) > max_bytes
                        body = response.body[:max_bytes]
                        response_sha = hashlib.sha256(body).hexdigest()
                        if response.status in {429, 500, 502, 503, 504} and attempt < retries:
                            sleep(_retry_delay(response.headers, attempt))
                            continue
                        if response.status < 200 or response.status >= 300:
                            raise RuntimeError(f"HTTP {response.status}")
                        if truncated:
                            raise RuntimeError("response_exceeded_max_bytes")
                        parsed = adapter.parser(body, request_id)
                        receipt = RequestReceipt(request_id, adapter.source_id, response.final_url, "GET", attempt, began, utc_now(), response.status, _header(response.headers, "Content-Type"), response_sha, len(body), truncated, len(parsed), rate_limit=_header(response.headers, "X-RateLimit-Limit"), rate_remaining=_header(response.headers, "X-RateLimit-Remaining"), retry_after=_header(response.headers, "Retry-After"))
                        break
                    except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                        requests_made += 1 if not isinstance(exc, RuntimeError) else 0
                        receipt = RequestReceipt(request_id, adapter.source_id, url, "GET", attempt, began, utc_now(), getattr(exc, "code", None), _header(response_headers, "Content-Type"), None, 0, False, 0, error_type=type(exc).__name__, error=str(exc)[:500], rate_limit=_header(response_headers, "X-RateLimit-Limit"), rate_remaining=_header(response_headers, "X-RateLimit-Remaining"), retry_after=_header(response_headers, "Retry-After"))
                        if attempt < retries:
                            sleep(_retry_delay(response_headers, attempt))
                            continue
                assert receipt is not None
                db.execute("INSERT OR REPLACE INTO receipts(digest, source_id, request_id, payload) VALUES (?, ?, ?, ?)", (receipt.digest, receipt.source_id, receipt.request_id, canonical_json(receipt.to_dict())))
                if receipt.error_type:
                    entry = NegativeMemoryEntry(adapter.source_id, "fetch_or_parse_failure", receipt.error or receipt.error_type, request_id)
                    db.execute("INSERT OR REPLACE INTO mminus(digest, source_id, kind, payload) VALUES (?, ?, ?, ?)", (entry.digest, entry.source_id, entry.kind, canonical_json(entry.to_dict())))
                for record in parsed:
                    if records_written >= item_budget:
                        break
                    cursor = db.execute("INSERT OR IGNORE INTO records(digest, source_id, record_id, payload) VALUES (?, ?, ?, ?)", (record.digest, record.source_id, record.record_id, canonical_json(record.to_dict())))
                    if cursor.rowcount:
                        records_written += 1
                db.commit()
                state.update({"adapter_index": adapter_index, "page": page + 1, "records": records_written, "requests": requests_made})
                _write_checkpoint(checkpoint_path, state)
                if receipt.error_type or not parsed or len(parsed) < min(page_size, item_budget - max(0, records_written - len(parsed))):
                    break
                sleep(max(0.0, 1.0 / adapter.requests_per_second))
            state.update({"adapter_index": adapter_index + 1, "page": 1, "records": records_written, "requests": requests_made})
            _write_checkpoint(checkpoint_path, state)
            if records_written >= item_budget:
                break
        record_rows = list(db.execute("SELECT digest, payload FROM records ORDER BY source_id, record_id, digest"))
        receipt_rows = list(db.execute("SELECT digest, payload FROM receipts ORDER BY source_id, request_id, digest"))
        mminus_rows = list(db.execute("SELECT digest, payload FROM mminus ORDER BY source_id, kind, digest"))
        (root / "records.jsonl").write_text("".join(json.dumps(json.loads(payload), ensure_ascii=False, sort_keys=True) + "\n" for _, payload in record_rows), encoding="utf-8")
        (root / "receipts.jsonl").write_text("".join(json.dumps(json.loads(payload), ensure_ascii=False, sort_keys=True) + "\n" for _, payload in receipt_rows), encoding="utf-8")
        (root / "mminus.jsonl").write_text("".join(json.dumps(json.loads(payload), ensure_ascii=False, sort_keys=True) + "\n" for _, payload in mminus_rows), encoding="utf-8")
        source_counts = dict(db.execute("SELECT source_id, COUNT(*) FROM records GROUP BY source_id ORDER BY source_id"))
        report = {
            "schema": "omega-web-hg-r04-max-campaign/1.0",
            "campaign_id": "omega-web-hg-r04-max-metadata",
            "started_at": started_at,
            "finished_at": utc_now(),
            "query": query,
            "finite_runtime_budget": {"item_budget": item_budget, "page_size": page_size, "max_pages_per_source": max_pages_per_source, "retries": retries, "max_bytes_per_response": max_bytes},
            "permanent_total_cap": None,
            "metadata_only": True,
            "raw_bodies_persisted": False,
            "full_text_collected": False,
            "request_count": len(receipt_rows),
            "record_count": len(record_rows),
            "mminus_count": len(mminus_rows),
            "source_counts": source_counts,
            "skipped": skipped,
            "record_merkle_root": _merkle_root(digest for digest, _ in record_rows),
            "receipt_merkle_root": _merkle_root(digest for digest, _ in receipt_rows),
            "mminus_merkle_root": _merkle_root(digest for digest, _ in mminus_rows),
            "oak_boundaries": {
                "metadata_is_truth": False,
                "source_authority_is_infallibility": False,
                "successful_fetch_is_republication_permission": False,
                "record_count_is_knowledge_completeness": False,
                "large_campaign_is_complete_internet_absorption": False,
            },
        }
        report["report_sha256"] = digest_object(report)
        (root / "campaign-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return root
    finally:
        db.close()
