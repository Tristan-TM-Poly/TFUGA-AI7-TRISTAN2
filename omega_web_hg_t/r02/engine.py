from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping, Protocol
from urllib.parse import urlsplit

from omega_web_hg_t.extract import parse_html
from omega_web_hg_t.models import CrawlResult, EdgeRecord, EvidenceRecord, FetchResponse, PageRecord, PolicyDecision, SectionRecord, canonicalize_url, stable_id, utc_now
from omega_web_hg_t.policy import PolicyGate

from .archive import WARCWriter
from .discovery import extract_html_metadata, jsonld_digests, maybe_decompress, parse_feed, parse_json_feed, parse_link_header, parse_robots_sitemaps, parse_sitemap, standard_discovery_urls
from .fetch import R02HTTPFetcher
from .models import R02_EXTRACTOR, ChangeRecord, DiscoveryRecord, DocumentMetadataRecord, R02Config, RunBundle, VersionRecord, config_digest
from .state import StateStore


class Fetcher(Protocol):
    def fetch(self, url: str, *, headers: Mapping[str, str] | None = None) -> FetchResponse:
        ...


class IncrementalWebHypergraphCrawler:
    def __init__(self, config: R02Config, *, policy: PolicyGate | None = None, fetcher: Fetcher | None = None) -> None:
        self.config = config
        self.policy = policy or PolicyGate(config.base())
        self.fetcher = fetcher or R02HTTPFetcher(config, redirect_validator=lambda target: self.policy.decide(target).allowed)

    @staticmethod
    def _run_id(seed_url: str) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        return f"run_{stamp}_{sha256(seed_url.encode('utf-8')).hexdigest()[:10]}"

    def _can_enqueue(self, state: StateStore, depth: int) -> bool:
        if self.config.max_depth is not None and depth > self.config.max_depth:
            return False
        if self.config.max_frontier is not None and state.frontier_count() >= self.config.max_frontier:
            return False
        return True

    @staticmethod
    def _priority(mechanism: str, depth: int) -> float:
        base = {
            "seed": 100.0,
            "html_sitemap": 85.0,
            "standard_sitemap": 80.0,
            "standard_sitemap_index": 80.0,
            "sitemap_index": 78.0,
            "sitemap_url": 70.0,
            "html_feed": 65.0,
            "standard_feed": 60.0,
            "feed_entry": 55.0,
            "html_link": 20.0,
        }.get(mechanism, 10.0)
        return base - min(depth, 100) * 0.1

    def _enqueue(self, state: StateStore, bundle: RunBundle, target: str, *, source: str | None, mechanism: str, depth: int) -> bool:
        try:
            normalized = canonicalize_url(target, base_url=source)
        except (ValueError, UnicodeError) as exc:
            bundle.crawl.errors.append({"url": target, "code": "DISCOVERY_INVALID_URL", "message": str(exc)})
            return False
        queued = False
        note = ""
        if self._can_enqueue(state, depth):
            queued = state.enqueue(normalized, depth=depth, priority=self._priority(mechanism, depth), discovered_from=source, mechanism=mechanism)
            if not queued:
                note = "already-known"
        else:
            note = "frontier-or-depth-budget"
        bundle.discoveries.append(DiscoveryRecord(discovery_id=stable_id("discovery", source or "", normalized, mechanism), source_url=source, target_url=normalized, mechanism=mechanism, depth=depth, discovered_at=utc_now(), queued=queued, note=note))
        bundle.crawl.discovered_urls[stable_id("page", normalized)] = normalized
        return queued

    @staticmethod
    def _directives(headers: Mapping[str, str]) -> set[str]:
        raw = headers.get("x-robots-tag", "")
        return {token.strip().lower() for token in raw.replace(",", " ").split() if token.strip()}

    @staticmethod
    def _section_digest(sections: list[tuple[int, str, str]]) -> str:
        payload = json.dumps(sections, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return sha256(payload).hexdigest()

    @staticmethod
    def _content_extension(content_type: str) -> str:
        lowered = content_type.lower()
        if "html" in lowered:
            return "html"
        if "json" in lowered:
            return "json"
        if "xml" in lowered or "rss" in lowered or "atom" in lowered:
            return "xml"
        if "text" in lowered:
            return "txt"
        return "bin"

    @staticmethod
    def _change(*, run_id: str, url: str, previous: VersionRecord | None, current: VersionRecord | None, change_type: str, details: Mapping[str, object] | None = None) -> ChangeRecord:
        detected = utc_now()
        return ChangeRecord(
            change_id=stable_id("change", run_id, url, change_type, previous.version_id if previous else "", current.version_id if current else ""),
            run_id=run_id,
            url=url,
            change_type=change_type,
            detected_at=detected,
            previous_version_id=previous.version_id if previous else None,
            current_version_id=current.version_id if current else None,
            previous_sha256=previous.content_sha256 if previous else None,
            current_sha256=current.content_sha256 if current else None,
            details=details or {},
        )

    def crawl(self, output_root: str | Path) -> RunBundle:
        root = Path(output_root)
        root.mkdir(parents=True, exist_ok=True)
        seed = canonicalize_url(self.config.seed_url)
        run_id = self._run_id(seed)
        run_dir = root / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        base_result = CrawlResult(config=self.config.base())
        bundle = RunBundle(run_id=run_id, config=self.config, crawl=base_result)
        warc = WARCWriter(run_dir / "archive.warc") if self.config.store_warc else None
        seen_page_ids: set[str] = set()
        seen_section_ids: set[str] = set()
        seen_edge_ids: set[str] = set()
        processed = 0

        with StateStore(root / "state.sqlite3") as state:
            bundle.resumed = state.start_run(run_id, seed_url=seed, config_sha256=config_digest(self.config.as_manifest()))
            self._enqueue(state, bundle, seed, source=None, mechanism="seed", depth=0)
            if bundle.resumed:
                for known_url in state.known_urls():
                    if known_url != seed:
                        self._enqueue(state, bundle, known_url, source=None, mechanism="recrawl", depth=0)
            if self.config.discover_standard_endpoints:
                for target, mechanism in standard_discovery_urls(seed):
                    self._enqueue(state, bundle, target, source=seed, mechanism=mechanism, depth=0)

            while True:
                if self.config.resource_budget is not None and processed >= self.config.resource_budget:
                    break
                lease_until = (datetime.now(timezone.utc) + timedelta(seconds=self.config.lease_seconds)).isoformat().replace("+00:00", "Z")
                item = state.claim_next(lease_until=lease_until)
                if item is None:
                    break
                decision = self.policy.decide(item.url)
                base_result.decisions.append(decision)
                if not decision.allowed:
                    state.complete(item.url)
                    continue
                try:
                    conditional = state.conditional_headers(item.url)
                    response = self.fetcher.fetch(item.url, headers=conditional)
                except (OSError, ValueError, UnicodeError) as exc:
                    state.record_error(item.url)
                    if item.attempts <= self.config.max_retries:
                        state.requeue(item.url)
                    else:
                        state.complete(item.url)
                        base_result.errors.append({"url": item.url, "code": type(exc).__name__, "message": str(exc)})
                    continue

                if response.status in {429, 500, 502, 503, 504}:
                    state.record_error(item.url)
                    if item.attempts <= self.config.max_retries:
                        state.requeue(item.url)
                    else:
                        state.complete(item.url)
                        base_result.errors.append({"url": item.url, "code": f"HTTP_{response.status}", "message": "retry budget exhausted"})
                    continue

                previous = state.latest_version(item.url)
                if response.status == 304:
                    change = self._change(run_id=run_id, url=item.url, previous=previous, current=None, change_type="NOT_MODIFIED", details={"conditional_headers": conditional})
                    bundle.changes.append(change)
                    state.record_change(change)
                    state.record_not_modified(item.url)
                    state.complete(item.url)
                    processed += 1
                    continue

                final_decision = self.policy.decide(response.final_url, check_robots=False)
                if not final_decision.allowed:
                    base_result.decisions.append(final_decision)
                    state.complete(item.url)
                    continue

                content_type = response.headers.get("content-type", "application/octet-stream")
                body_hash = sha256(response.body).hexdigest()
                parse_body = maybe_decompress(response.body, content_encoding=response.headers.get("content-encoding", ""), url=response.final_url)
                parsed = None
                html_metadata = None
                title = response.final_url
                language = None
                canonical = response.final_url
                sections: list[tuple[int, str, str]] = []
                directives = self._directives(response.headers)

                if "html" in content_type.lower() and parse_body:
                    parsed = parse_html(parse_body, content_type=content_type)
                    html_metadata = extract_html_metadata(parse_body, base_url=response.final_url, content_type=content_type)
                    directives |= html_metadata.robots_directives
                    title = parsed.title or response.final_url
                    language = parsed.language
                    sections = list(parsed.sections)
                    if parsed.canonical_url:
                        try:
                            candidate_canonical = canonicalize_url(parsed.canonical_url, base_url=response.final_url)
                            canonical_decision = self.policy.decide(candidate_canonical, check_robots=False)
                            if canonical_decision.allowed:
                                canonical = candidate_canonical
                            else:
                                base_result.decisions.append(canonical_decision)
                        except (ValueError, UnicodeError) as exc:
                            base_result.errors.append({"url": response.final_url, "code": "INVALID_CANONICAL", "message": str(exc)})

                noarchive = self.config.respect_meta_robots and "noarchive" in directives
                nofollow = self.config.respect_meta_robots and "nofollow" in directives
                extension = self._content_extension(content_type)
                raw_blob = None
                if self.config.store_raw and not noarchive and response.body:
                    raw_blob = f"objects/sha256/{body_hash[:2]}/{body_hash}.{extension}"
                    base_result.raw_blobs[raw_blob] = response.body

                warc_record_id = None
                if warc is not None:
                    if noarchive:
                        warc_record_id = warc.write_metadata(response.final_url, {"capture": "suppressed", "reason": "noarchive", "sha256": body_hash, "status": response.status})
                    else:
                        warc_record_id = warc.write_response(response)

                page_id = stable_id("page", canonical)
                evidence_id = stable_id("evidence", response.final_url, body_hash, response.fetched_at)
                if page_id not in seen_page_ids:
                    base_result.pages.append(PageRecord(page_id=page_id, requested_url=response.requested_url, final_url=response.final_url, canonical_url=canonical, title=title, language=language, evidence_id=evidence_id, content_sha256=body_hash, fetched_at=response.fetched_at, status=response.status, content_type=content_type, byte_length=len(response.body)))
                    seen_page_ids.add(page_id)
                base_result.evidence.append(EvidenceRecord(evidence_id=evidence_id, requested_url=response.requested_url, final_url=response.final_url, fetched_at=response.fetched_at, http_status=response.status, content_type=content_type, content_sha256=body_hash, byte_length=len(response.body), headers={key: value for key, value in response.headers.items() if key in {"etag", "last-modified", "content-type", "content-language", "cache-control", "link", "x-robots-tag"}}, extractor=R02_EXTRACTOR, policy_code=decision.code, raw_blob=raw_blob))

                for index, (level, heading, text) in enumerate(sections):
                    section_id = stable_id("section", page_id, str(index), heading, text)
                    if section_id not in seen_section_ids:
                        base_result.sections.append(SectionRecord(section_id, page_id, index, level, heading, text, f"section:{index}"))
                        seen_section_ids.add(section_id)
                    edge_id = stable_id("edge", page_id, section_id, "PAGE_CONTAINS_SECTION")
                    if edge_id not in seen_edge_ids:
                        base_result.edges.append(EdgeRecord(edge_id, "PAGE_CONTAINS_SECTION", page_id, section_id, evidence_id))
                        seen_edge_ids.add(edge_id)

                link_relations = parse_link_header(response.headers.get("link", ""), base_url=response.final_url)
                if self.config.discover_sitemaps:
                    for target in link_relations.get("sitemap", ()):
                        self._enqueue(state, bundle, target, source=response.final_url, mechanism="http_link_sitemap", depth=item.depth + 1)
                if self.config.discover_feeds:
                    for target in link_relations.get("alternate", ()):
                        self._enqueue(state, bundle, target, source=response.final_url, mechanism="http_link_alternate", depth=item.depth + 1)

                if html_metadata is not None:
                    bundle.metadata.append(DocumentMetadataRecord(metadata_id=stable_id("metadata", page_id, evidence_id), page_id=page_id, url=canonical, robots_directives=tuple(sorted(directives)), feed_urls=tuple(sorted(set(html_metadata.feed_urls))), sitemap_urls=tuple(sorted(set(html_metadata.sitemap_urls))), license_urls=tuple(sorted(set(html_metadata.license_urls))), jsonld_sha256=jsonld_digests(html_metadata.jsonld_objects), noarchive=noarchive, nofollow=nofollow))
                    if self.config.discover_feeds:
                        for target in html_metadata.feed_urls:
                            self._enqueue(state, bundle, target, source=response.final_url, mechanism="html_feed", depth=item.depth + 1)
                    if self.config.discover_sitemaps:
                        for target in html_metadata.sitemap_urls:
                            self._enqueue(state, bundle, target, source=response.final_url, mechanism="html_sitemap", depth=item.depth + 1)
                    if parsed is not None and not nofollow:
                        for target in parsed.links:
                            try:
                                link = canonicalize_url(target, base_url=response.final_url)
                            except (ValueError, UnicodeError):
                                continue
                            target_id = stable_id("page", link)
                            base_result.discovered_urls[target_id] = link
                            edge_id = stable_id("edge", page_id, target_id, "PAGE_LINKS_TO_PAGE")
                            if edge_id not in seen_edge_ids:
                                base_result.edges.append(EdgeRecord(edge_id, "PAGE_LINKS_TO_PAGE", page_id, target_id, evidence_id))
                                seen_edge_ids.add(edge_id)
                            self._enqueue(state, bundle, link, source=response.final_url, mechanism="html_link", depth=item.depth + 1)

                if item.mechanism == "standard_robots" and parse_body and self.config.discover_sitemaps:
                    for target in parse_robots_sitemaps(parse_body, base_url=response.final_url):
                        self._enqueue(state, bundle, target, source=response.final_url, mechanism="robots_sitemap", depth=item.depth + 1)

                lowered_type = content_type.lower()
                is_xml = any(token in lowered_type for token in ("xml", "rss", "atom")) or urlsplit(response.final_url).path.lower().endswith(".xml")
                if is_xml and parse_body:
                    consumed = False
                    if self.config.discover_sitemaps:
                        try:
                            sitemap = parse_sitemap(parse_body)
                            entries = sitemap.urls if sitemap.kind == "urlset" else sitemap.nested_sitemaps
                            mechanism = "sitemap_url" if sitemap.kind == "urlset" else "sitemap_index"
                            relation = "SITEMAP_DISCOVERS_PAGE" if sitemap.kind == "urlset" else "SITEMAP_DISCOVERS_SITEMAP"
                            for entry in entries:
                                self._enqueue(state, bundle, entry.location, source=response.final_url, mechanism=mechanism, depth=item.depth + 1)
                                target_id = stable_id("page", canonicalize_url(entry.location, base_url=response.final_url))
                                edge_id = stable_id("edge", page_id, target_id, relation)
                                if edge_id not in seen_edge_ids:
                                    base_result.edges.append(EdgeRecord(edge_id, relation, page_id, target_id, evidence_id))
                                    seen_edge_ids.add(edge_id)
                            consumed = True
                        except (ValueError, UnicodeError):
                            pass
                    if self.config.discover_feeds and not consumed:
                        try:
                            for entry in parse_feed(parse_body):
                                self._enqueue(state, bundle, entry.url, source=response.final_url, mechanism="feed_entry", depth=item.depth + 1)
                                target_id = stable_id("page", canonicalize_url(entry.url, base_url=response.final_url))
                                edge_id = stable_id("edge", page_id, target_id, "FEED_DISCOVERS_PAGE")
                                if edge_id not in seen_edge_ids:
                                    base_result.edges.append(EdgeRecord(edge_id, "FEED_DISCOVERS_PAGE", page_id, target_id, evidence_id))
                                    seen_edge_ids.add(edge_id)
                        except (ValueError, UnicodeError):
                            pass

                if self.config.discover_feeds and "application/feed+json" in lowered_type and parse_body:
                    try:
                        for entry in parse_json_feed(parse_body):
                            self._enqueue(state, bundle, entry.url, source=response.final_url, mechanism="feed_entry", depth=item.depth + 1)
                            target_id = stable_id("page", canonicalize_url(entry.url, base_url=response.final_url))
                            edge_id = stable_id("edge", page_id, target_id, "FEED_DISCOVERS_PAGE")
                            if edge_id not in seen_edge_ids:
                                base_result.edges.append(EdgeRecord(edge_id, "FEED_DISCOVERS_PAGE", page_id, target_id, evidence_id))
                                seen_edge_ids.add(edge_id)
                    except (ValueError, UnicodeError, json.JSONDecodeError):
                        pass

                section_digest = self._section_digest(sections)
                version_id = stable_id("version", item.url, body_hash, response.fetched_at)
                version = VersionRecord(version_id=version_id, run_id=run_id, url=item.url, canonical_url=canonical, fetched_at=response.fetched_at, http_status=response.status, content_type=content_type, content_sha256=body_hash, byte_length=len(response.body), evidence_id=evidence_id, etag=response.headers.get("etag"), last_modified=response.headers.get("last-modified"), title=title, section_digest=section_digest, raw_blob=raw_blob, warc_record_id=warc_record_id)
                if response.status in {404, 410}:
                    change_type = "REMOVED" if previous is not None else "MISSING"
                elif previous is None:
                    change_type = "ADDED"
                elif previous.content_sha256 == version.content_sha256:
                    change_type = "UNCHANGED"
                else:
                    change_type = "MODIFIED"
                change = self._change(run_id=run_id, url=item.url, previous=previous, current=version, change_type=change_type)
                bundle.versions.append(version)
                bundle.changes.append(change)
                state.record_version(version)
                state.record_change(change)
                state.complete(item.url)
                processed += 1

            bundle.frontier_remaining = state.frontier_count()
            bundle.finished_at = utc_now()
            final_status = "complete" if bundle.frontier_remaining == 0 else "budget_exhausted"
            state.finish_run(run_id, final_status)
            snapshot_path = state.snapshot(run_dir / "state.snapshot.sqlite3")
            bundle.state_snapshot = snapshot_path.name
            bundle.warc_file = "archive.warc" if warc is not None else None
            bundle.write(run_dir)
        return bundle
