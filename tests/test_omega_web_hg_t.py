from __future__ import annotations

from pathlib import Path

from omega_web_hg_t.core import (
    CrawlConfig,
    FetchResponse,
    PolicyGate,
    SafeRedirectHandler,
    WebHypergraphCrawler,
    canonicalize_url,
    parse_html,
)


PUBLIC_IP = ["93.184.216.34"]


class MemoryFetcher:
    def __init__(self, pages: dict[str, bytes]) -> None:
        self.pages = pages

    def fetch(self, url: str, *, headers=None) -> FetchResponse:
        return FetchResponse(
            requested_url=url,
            final_url=url,
            status=200,
            headers={"content-type": "text/html; charset=utf-8", "etag": '"fixture"'},
            body=self.pages[url],
            fetched_at="2026-08-03T16:00:00Z",
        )


def allow_all_robots(_: str) -> str:
    return "User-agent: *\nAllow: /\n"


def test_canonicalize_url_removes_fragment_and_tracking() -> None:
    value = canonicalize_url("HTTPS://Example.org:443//a///b?z=2&utm_source=x&a=1#frag")
    assert value == "https://example.org/a/b?a=1&z=2"


def test_policy_blocks_private_networks() -> None:
    config = CrawlConfig("http://127.0.0.1/")
    gate = PolicyGate(config, resolver=lambda _: ["127.0.0.1"], robots_loader=allow_all_robots)
    decision = gate.decide(config.seed_url)
    assert not decision.allowed
    assert decision.code == "NON_PUBLIC_NETWORK"


def test_policy_respects_robots() -> None:
    config = CrawlConfig("https://example.org/private")
    robots = "User-agent: *\nDisallow: /private\n"
    gate = PolicyGate(config, resolver=lambda _: PUBLIC_IP, robots_loader=lambda _: robots)
    decision = gate.decide(config.seed_url)
    assert not decision.allowed
    assert decision.code == "ROBOTS_DENIED"


def test_html_parser_builds_sections_and_links() -> None:
    parsed = parse_html(
        b"""
        <html lang='fr'><head><title>Essai</title><link rel='canonical' href='/canon'></head>
        <body><h1>Alpha</h1><p>Premier paragraphe.</p><h2>Beta</h2>
        <p>Deuxieme paragraphe.</p><a href='/next'>Suite</a><script>ignore()</script></body></html>
        """
    )
    assert parsed.title == "Essai"
    assert parsed.language == "fr"
    assert parsed.canonical_url == "/canon"
    assert parsed.links == ["/next"]
    assert parsed.sections == [
        (1, "Alpha", "Premier paragraphe."),
        (2, "Beta", "Deuxieme paragraphe."),
    ]


def test_crawler_writes_provenance_bundle(tmp_path: Path) -> None:
    root = "https://example.org/"
    next_url = "https://example.org/next"
    pages = {
        root: b"<html><head><title>Root</title></head><body><h1>A</h1><p>Texte A.</p><a href='/next'>next</a></body></html>",
        next_url: b"<html><head><title>Next</title></head><body><h1>B</h1><p>Texte B.</p></body></html>",
    }
    config = CrawlConfig(root, page_budget=10, delay_seconds=0.0)
    gate = PolicyGate(config, resolver=lambda _: PUBLIC_IP, robots_loader=allow_all_robots)
    result = WebHypergraphCrawler(config, policy=gate, fetcher=MemoryFetcher(pages)).crawl()

    assert len(result.pages) == 2
    assert len(result.sections) == 2
    assert len(result.evidence) == 2
    assert any(edge.relation == "PAGE_LINKS_TO_PAGE" for edge in result.edges)
    output = result.write(tmp_path / "bundle")
    assert (output / "manifest.json").is_file()
    assert (output / "hypergraph.json").is_file()
    assert (output / "hypergraph.graphml").is_file()
    assert (output / "oak-report.json").is_file()
    assert len(list((output / "raw").rglob("*.html"))) == 2
    assert result.oak_report()["status"] == "PASS_R0_1"


def test_canonicalize_url_rejects_embedded_credentials() -> None:
    try:
        canonicalize_url("https://user:secret@example.org/")
    except ValueError as exc:
        assert "identifiants" in str(exc)
    else:
        raise AssertionError("embedded credentials must be rejected")


def test_redirect_handler_blocks_out_of_scope_target() -> None:
    handler = SafeRedirectHandler(lambda url: url == "https://example.org/ok")

    class RequestFixture:
        full_url = "https://example.org/start"

    try:
        handler.redirect_request(RequestFixture(), None, 302, "Found", {}, "https://evil.example/target")
    except ValueError as exc:
        assert "Redirection refusée" in str(exc)
    else:
        raise AssertionError("unsafe redirect must be rejected before follow")
