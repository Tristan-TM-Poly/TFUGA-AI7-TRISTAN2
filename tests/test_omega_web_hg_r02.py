from __future__ import annotations

from pathlib import Path
import json

from omega_web_hg_t.models import FetchResponse, PolicyDecision, utc_now
from omega_web_hg_t.r02.archive import WARCWriter
from omega_web_hg_t.r02.audit import audit_run
from omega_web_hg_t.r02.diffing import compare_run_directories
from omega_web_hg_t.r02.discovery import (
    extract_html_metadata,
    maybe_decompress,
    parse_feed,
    parse_json_feed,
    parse_link_header,
    parse_robots_sitemaps,
    parse_sitemap,
)
from omega_web_hg_t.r02.engine import IncrementalWebHypergraphCrawler
from omega_web_hg_t.r02.models import R02Config, VersionRecord
from omega_web_hg_t.r02.state import StateStore


def test_parse_sitemap_urlset_and_index():
    urlset = b'''<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.org/a</loc><lastmod>2026-08-01</lastmod><priority>0.8</priority></url>
    </urlset>'''
    parsed = parse_sitemap(urlset)
    assert parsed.kind == "urlset"
    assert parsed.urls[0].location == "https://example.org/a"
    assert parsed.urls[0].priority == 0.8

    index = b'''<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example.org/sitemap-1.xml</loc></sitemap>
    </sitemapindex>'''
    parsed_index = parse_sitemap(index)
    assert parsed_index.kind == "sitemapindex"
    assert parsed_index.nested_sitemaps[0].location.endswith("sitemap-1.xml")


def test_parse_rss_and_atom():
    rss = b'''<rss version="2.0"><channel><item><title>A</title><link>https://example.org/a</link><pubDate>x</pubDate></item></channel></rss>'''
    atom = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>B</title><link href="https://example.org/b"/><updated>y</updated></entry></feed>'''
    assert parse_feed(rss)[0].url.endswith("/a")
    assert parse_feed(atom)[0].title == "B"


def test_robots_link_headers_json_feed_and_gzip():
    robots = b"User-agent: *\nSitemap: /sitemap.xml\nSitemap: https://example.org/news.xml\n"
    assert parse_robots_sitemaps(robots, base_url="https://example.org/robots.txt") == (
        "https://example.org/sitemap.xml",
        "https://example.org/news.xml",
    )
    links = parse_link_header(
        '<https://example.org/sitemap.xml>; rel="sitemap", </feed.json>; rel="alternate"',
        base_url="https://example.org/",
    )
    assert links["sitemap"] == ("https://example.org/sitemap.xml",)
    assert links["alternate"] == ("https://example.org/feed.json",)
    feed = parse_json_feed(b'{"version":"https://jsonfeed.org/version/1.1","items":[{"url":"https://example.org/a","title":"A"}]}')
    assert feed[0].title == "A"
    import gzip
    compressed = gzip.compress(b"<urlset/>")
    assert maybe_decompress(compressed, content_encoding="gzip") == b"<urlset/>"


def test_html_metadata_directives_and_jsonld():
    body = b'''<html><head>
      <meta name="robots" content="noarchive, nofollow">
      <link rel="alternate" type="application/rss+xml" href="/feed.xml">
      <link rel="sitemap" href="/sitemap.xml">
      <link rel="license" href="/license">
      <script type="application/ld+json">{"@type":"Article","name":"A"}</script>
    </head></html>'''
    metadata = extract_html_metadata(body, base_url="https://example.org/")
    assert metadata.noarchive and metadata.nofollow
    assert metadata.feed_urls == ["https://example.org/feed.xml"]
    assert metadata.sitemap_urls == ["https://example.org/sitemap.xml"]
    assert metadata.license_urls == ["https://example.org/license"]
    assert metadata.jsonld_objects[0]["@type"] == "Article"


def test_warc_writer_emits_response_and_metadata(tmp_path: Path):
    path = tmp_path / "capture.warc"
    writer = WARCWriter(path)
    response = FetchResponse(
        requested_url="https://example.org/",
        final_url="https://example.org/",
        status=200,
        headers={"content-type": "text/plain"},
        body=b"hello",
        fetched_at="2026-08-03T16:00:00Z",
    )
    response_id = writer.write_response(response)
    metadata_id = writer.write_metadata("https://example.org/", {"policy": "ALLOW"})
    payload = path.read_bytes()
    assert payload.count(b"WARC/1.1") == 2
    assert b"WARC-Type: response" in payload
    assert b"HTTP/1.1 200 OK" in payload
    assert b"WARC-Type: metadata" in payload
    assert response_id.startswith("<urn:uuid:")
    assert metadata_id.startswith("<urn:uuid:")


def _version(run_id: str, url: str, digest: str) -> VersionRecord:
    return VersionRecord(
        version_id=f"version-{run_id}-{digest}",
        run_id=run_id,
        url=url,
        canonical_url=url,
        fetched_at=f"2026-08-03T16:00:0{run_id[-1]}Z",
        http_status=200,
        content_type="text/html",
        content_sha256=digest,
        byte_length=10,
        evidence_id=f"evidence-{digest}",
        etag=f'"{digest}"',
        last_modified="Mon, 03 Aug 2026 16:00:00 GMT",
        title="Page",
        section_digest=digest,
        raw_blob=None,
        warc_record_id=None,
    )


def test_state_resume_leases_and_conditional_headers(tmp_path: Path):
    with StateStore(tmp_path / "state.sqlite3") as store:
        assert store.start_run("run1", seed_url="https://example.org/", config_sha256="a") is False
        assert store.enqueue("https://example.org/", depth=0, mechanism="seed")
        item = store.claim_next(lease_until="2999-01-01T00:00:00Z")
        assert item and item.attempts == 1
        store.requeue(item.url)
        item2 = store.claim_next(lease_until="2999-01-01T00:00:00Z")
        assert item2 and item2.attempts == 2
        version = _version("run1", item2.url, "abc")
        store.record_version(version)
        store.complete(item2.url)
        assert store.conditional_headers(item2.url) == {
            "If-None-Match": '"abc"',
            "If-Modified-Since": "Mon, 03 Aug 2026 16:00:00 GMT",
        }
        assert store.known_urls() == [item2.url]
        assert store.start_run("run2", seed_url=item2.url, config_sha256="b") is True


def _write_page_bundle(root: Path, items: list[dict[str, object]]) -> None:
    root.mkdir(parents=True)
    with (root / "pages.jsonl").open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item) + "\n")


def test_compare_run_directories(tmp_path: Path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    _write_page_bundle(old, [
        {"canonical_url": "https://example.org/a", "content_sha256": "1"},
        {"canonical_url": "https://example.org/b", "content_sha256": "2"},
    ])
    _write_page_bundle(new, [
        {"canonical_url": "https://example.org/a", "content_sha256": "3"},
        {"canonical_url": "https://example.org/c", "content_sha256": "4"},
    ])
    result = compare_run_directories(old, new)
    assert result["counts"] == {"added": 1, "removed": 1, "modified": 1, "unchanged": 0}


class AllowPolicy:
    def decide(self, url: str, *, check_robots: bool = True) -> PolicyDecision:
        return PolicyDecision(url, True, "ALLOW", "fixture", utc_now())


class FixtureFetcher:
    def __init__(self) -> None:
        self.requests: list[tuple[str, dict[str, str]]] = []
        self.bodies = {
            "https://example.org/": (
                "text/html; charset=utf-8",
                b'''<html><head><title>Home</title><link rel="alternate" type="application/rss+xml" href="/feed.xml"></head><body><h1>Home</h1><p>Root</p><a href="/a">A</a></body></html>''',
            ),
            "https://example.org/feed.xml": (
                "application/rss+xml",
                b'''<rss version="2.0"><channel><item><title>B</title><link>https://example.org/b</link></item></channel></rss>''',
            ),
            "https://example.org/a": (
                "text/html",
                b'''<html><head><title>A</title><meta name="robots" content="noarchive"></head><body><h1>A</h1><p>Secret-ish public page</p></body></html>''',
            ),
            "https://example.org/b": (
                "text/html",
                b'''<html><head><title>B</title></head><body><h1>B</h1><p>Body B</p></body></html>''',
            ),
        }

    def fetch(self, url: str, *, headers=None) -> FetchResponse:
        normalized_headers = dict(headers or {})
        self.requests.append((url, normalized_headers))
        content_type, body = self.bodies[url]
        etag = f'"{url.rsplit("/", 1)[-1] or "root"}"'
        if normalized_headers.get("If-None-Match") == etag:
            return FetchResponse(url, url, 304, {"etag": etag, "content-type": content_type}, b"", utc_now())
        return FetchResponse(
            requested_url=url,
            final_url=url,
            status=200,
            headers={"content-type": content_type, "etag": etag, "last-modified": "Mon, 03 Aug 2026 16:00:00 GMT"},
            body=body,
            fetched_at=utc_now(),
        )


def test_incremental_engine_discovers_archives_and_resumes(tmp_path: Path):
    output = tmp_path / "campaign"
    fetcher = FixtureFetcher()
    config = R02Config(
        seed_url="https://example.org/",
        resource_budget=20,
        max_depth=5,
        max_frontier=100,
        delay_seconds=0,
        discover_standard_endpoints=False,
    )
    first = IncrementalWebHypergraphCrawler(config, policy=AllowPolicy(), fetcher=fetcher).crawl(output)
    assert {page.canonical_url for page in first.crawl.pages} == {
        "https://example.org/",
        "https://example.org/a",
        "https://example.org/b",
        "https://example.org/feed.xml",
    }
    assert any(change.change_type == "ADDED" for change in first.changes)
    assert any(item.mechanism == "feed_entry" for item in first.discoveries)
    a_evidence = next(item for item in first.crawl.evidence if item.final_url.endswith("/a"))
    assert a_evidence.raw_blob is None
    run_dir = output / "runs" / first.run_id
    assert (run_dir / "archive.warc").is_file()
    assert (run_dir / "state.snapshot.sqlite3").is_file()
    assert (run_dir / "hypergraph-v2.json").is_file()
    assert (run_dir / "hypergraph-v2.graphml").is_file()
    provenance = json.loads((run_dir / "provenance.jsonld").read_text())
    assert provenance["@context"]["prov"] == "http://www.w3.org/ns/prov#"
    graph_v2 = json.loads((run_dir / "hypergraph-v2.json").read_text())
    node_ids = {item["id"] for item in graph_v2["nodes"]}
    assert all(edge["source_id"] in node_ids and edge["target_id"] in node_ids for edge in graph_v2["hyperedges"])
    assert audit_run(run_dir)["status"] == "PASS_R0_2"

    second_fetcher = FixtureFetcher()
    second = IncrementalWebHypergraphCrawler(config, policy=AllowPolicy(), fetcher=second_fetcher).crawl(output)
    assert second.resumed is True
    assert second.changes
    assert all(change.change_type == "NOT_MODIFIED" for change in second.changes)
    assert any(headers.get("If-None-Match") for _, headers in second_fetcher.requests)
