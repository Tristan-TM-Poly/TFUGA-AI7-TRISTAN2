from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
import gzip
import json
import re
from typing import Any
from urllib.parse import urljoin
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class SitemapEntry:
    location: str
    last_modified: str | None = None
    change_frequency: str | None = None
    priority: float | None = None


@dataclass(frozen=True)
class SitemapDocument:
    kind: str
    urls: tuple[SitemapEntry, ...] = ()
    nested_sitemaps: tuple[SitemapEntry, ...] = ()


@dataclass(frozen=True)
class FeedEntry:
    url: str
    title: str = ""
    published: str | None = None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if _local(child.tag) == name and child.text:
            value = child.text.strip()
            return value or None
    return None


def parse_sitemap(body: bytes) -> SitemapDocument:
    root = ET.fromstring(body)
    root_name = _local(root.tag)
    if root_name not in {"urlset", "sitemapindex"}:
        raise ValueError(f"Unsupported sitemap root: {root_name}")
    entries: list[SitemapEntry] = []
    for child in root:
        expected = "url" if root_name == "urlset" else "sitemap"
        if _local(child.tag) != expected:
            continue
        location = _child_text(child, "loc")
        if not location:
            continue
        priority_raw = _child_text(child, "priority")
        try:
            priority = float(priority_raw) if priority_raw is not None else None
        except ValueError:
            priority = None
        entries.append(SitemapEntry(location=location, last_modified=_child_text(child, "lastmod"), change_frequency=_child_text(child, "changefreq"), priority=priority))
    if root_name == "urlset":
        return SitemapDocument(kind="urlset", urls=tuple(entries))
    return SitemapDocument(kind="sitemapindex", nested_sitemaps=tuple(entries))


def parse_feed(body: bytes) -> tuple[FeedEntry, ...]:
    root = ET.fromstring(body)
    root_name = _local(root.tag)
    entries: list[FeedEntry] = []
    if root_name == "rss":
        for item in root.iter():
            if _local(item.tag) != "item":
                continue
            link = _child_text(item, "link")
            if link:
                entries.append(FeedEntry(link, _child_text(item, "title") or "", _child_text(item, "pubdate")))
    elif root_name == "feed":
        for item in root:
            if _local(item.tag) != "entry":
                continue
            link = None
            for child in item:
                if _local(child.tag) == "link" and child.attrib.get("href"):
                    rel = child.attrib.get("rel", "alternate").lower()
                    if rel in {"alternate", ""}:
                        link = child.attrib["href"]
                        break
            if link:
                entries.append(FeedEntry(link, _child_text(item, "title") or "", _child_text(item, "updated") or _child_text(item, "published")))
    else:
        raise ValueError(f"Unsupported feed root: {root_name}")
    return tuple(entries)


@dataclass
class HTMLMetadata:
    robots_directives: set[str] = field(default_factory=set)
    feed_urls: list[str] = field(default_factory=list)
    sitemap_urls: list[str] = field(default_factory=list)
    license_urls: list[str] = field(default_factory=list)
    jsonld_objects: list[Any] = field(default_factory=list)

    @property
    def noarchive(self) -> bool:
        return "noarchive" in self.robots_directives

    @property
    def nofollow(self) -> bool:
        return "nofollow" in self.robots_directives


class _MetadataParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.metadata = HTMLMetadata()
        self._jsonld_depth = 0
        self._jsonld_chunks: list[str] = []

    @staticmethod
    def _rels(value: str | None) -> set[str]:
        return {part.lower() for part in re.split(r"\s+", value or "") if part}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): value for key, value in attrs}
        tag = tag.lower()
        if tag == "meta" and (attr.get("name") or "").lower() in {"robots", "googlebot", "bingbot"}:
            for token in re.split(r"[,\s]+", attr.get("content") or ""):
                token = token.strip().lower()
                if token:
                    self.metadata.robots_directives.add(token)
        elif tag == "link" and attr.get("href"):
            rels = self._rels(attr.get("rel"))
            target = urljoin(self.base_url, attr["href"])
            media_type = (attr.get("type") or "").lower()
            if "alternate" in rels and media_type in {"application/rss+xml", "application/atom+xml", "application/feed+json"}:
                self.metadata.feed_urls.append(target)
            if "sitemap" in rels:
                self.metadata.sitemap_urls.append(target)
            if "license" in rels:
                self.metadata.license_urls.append(target)
        elif tag == "script" and (attr.get("type") or "").lower() == "application/ld+json":
            self._jsonld_depth = 1
            self._jsonld_chunks = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._jsonld_depth:
            raw = "".join(self._jsonld_chunks).strip()
            if raw:
                try:
                    self.metadata.jsonld_objects.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass
            self._jsonld_depth = 0
            self._jsonld_chunks = []

    def handle_data(self, data: str) -> None:
        if self._jsonld_depth:
            self._jsonld_chunks.append(data)


def extract_html_metadata(body: bytes, *, base_url: str, content_type: str = "text/html") -> HTMLMetadata:
    charset_match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
    charset = charset_match.group(1) if charset_match else "utf-8"
    try:
        text = body.decode(charset, errors="replace")
    except LookupError:
        text = body.decode("utf-8", errors="replace")
    parser = _MetadataParser(base_url)
    parser.feed(text)
    parser.close()
    return parser.metadata


def jsonld_digests(objects: list[Any]) -> tuple[str, ...]:
    digests = []
    for item in objects:
        payload = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digests.append(sha256(payload).hexdigest())
    return tuple(sorted(digests))


def maybe_decompress(body: bytes, *, content_encoding: str = "", url: str = "") -> bytes:
    if "gzip" in content_encoding.lower() or url.lower().endswith(".gz"):
        try:
            return gzip.decompress(body)
        except (OSError, EOFError):
            return body
    return body


def parse_robots_sitemaps(body: bytes, *, base_url: str) -> tuple[str, ...]:
    text = body.decode("utf-8", errors="replace")
    urls = []
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip().lower() == "sitemap" and value.strip():
            urls.append(urljoin(base_url, value.strip()))
    return tuple(dict.fromkeys(urls))


def parse_link_header(value: str, *, base_url: str) -> dict[str, tuple[str, ...]]:
    relations: dict[str, list[str]] = {}
    for part in re.split(r",(?=\s*<)", value or ""):
        match = re.match(r"\s*<([^>]+)>(.*)$", part)
        if not match:
            continue
        target = urljoin(base_url, match.group(1).strip())
        parameters = match.group(2)
        rel_match = re.search(r";\s*rel\s*=\s*(?:\"([^\"]+)\"|([^;\s]+))", parameters, flags=re.I)
        if not rel_match:
            continue
        for relation in (rel_match.group(1) or rel_match.group(2) or "").lower().split():
            relations.setdefault(relation, []).append(target)
    return {key: tuple(dict.fromkeys(values)) for key, values in relations.items()}


def parse_json_feed(body: bytes) -> tuple[FeedEntry, ...]:
    payload = json.loads(body.decode("utf-8", errors="replace"))
    if not isinstance(payload, dict) or "items" not in payload:
        raise ValueError("Not a JSON Feed document")
    entries = []
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            continue
        target = item.get("url") or item.get("external_url")
        if isinstance(target, str) and target:
            entries.append(FeedEntry(url=target, title=str(item.get("title") or ""), published=str(item.get("date_published") or item.get("date_modified") or "") or None))
    return tuple(entries)


def standard_discovery_urls(seed_url: str) -> tuple[tuple[str, str], ...]:
    return (
        (urljoin(seed_url, "/robots.txt"), "standard_robots"),
        (urljoin(seed_url, "/sitemap.xml"), "standard_sitemap"),
        (urljoin(seed_url, "/sitemap_index.xml"), "standard_sitemap_index"),
        (urljoin(seed_url, "/feed"), "standard_feed"),
        (urljoin(seed_url, "/feed.xml"), "standard_feed"),
        (urljoin(seed_url, "/rss.xml"), "standard_feed"),
        (urljoin(seed_url, "/atom.xml"), "standard_feed"),
    )
