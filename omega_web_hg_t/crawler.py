from __future__ import annotations

from collections import deque
from hashlib import sha256

from .extract import parse_html
from .models import (
    EXTRACTOR_VERSION,
    CrawlConfig,
    CrawlResult,
    EdgeRecord,
    EvidenceRecord,
    Fetcher,
    PageRecord,
    SectionRecord,
    canonicalize_url,
    stable_id,
)
from .policy import PolicyGate, PoliteHTTPFetcher


class WebHypergraphCrawler:
    def __init__(
        self,
        config: CrawlConfig,
        *,
        policy: PolicyGate | None = None,
        fetcher: Fetcher | None = None,
    ) -> None:
        self.config = config
        self.policy = policy or PolicyGate(config)
        self.fetcher = fetcher or PoliteHTTPFetcher(
            config,
            redirect_validator=lambda target: self.policy.decide(target).allowed,
        )

    def crawl(self) -> CrawlResult:
        result = CrawlResult(config=self.config)
        seed = canonicalize_url(self.config.seed_url)
        frontier: deque[str] = deque([seed])
        queued = {seed}
        visited: set[str] = set()

        while frontier:
            if self.config.page_budget is not None and len(result.pages) >= self.config.page_budget:
                break
            candidate = frontier.popleft()
            if candidate in visited:
                continue
            visited.add(candidate)

            decision = self.policy.decide(candidate)
            result.decisions.append(decision)
            if not decision.allowed:
                continue

            try:
                response = self.fetcher.fetch(candidate)
                final_decision = self.policy.decide(response.final_url, check_robots=False)
                if not final_decision.allowed:
                    result.decisions.append(final_decision)
                    continue
                content_type = response.headers.get("content-type", "application/octet-stream")
                if "html" not in content_type.lower():
                    result.errors.append({"url": candidate, "code": "UNSUPPORTED_CONTENT", "message": content_type})
                    continue
                parsed = parse_html(response.body, content_type=content_type)
            except (OSError, ValueError, UnicodeError) as exc:
                result.errors.append({"url": candidate, "code": type(exc).__name__, "message": str(exc)})
                continue

            body_hash = sha256(response.body).hexdigest()
            canonical = (
                canonicalize_url(parsed.canonical_url, base_url=response.final_url)
                if parsed.canonical_url
                else response.final_url
            )
            page_id = stable_id("page", canonical)
            evidence_id = stable_id("evidence", response.final_url, body_hash, response.fetched_at)
            raw_blob = f"raw/{body_hash[:2]}/{body_hash}.html" if self.config.store_raw else None
            if raw_blob:
                result.raw_blobs[raw_blob] = response.body

            result.pages.append(
                PageRecord(
                    page_id=page_id,
                    requested_url=response.requested_url,
                    final_url=response.final_url,
                    canonical_url=canonical,
                    title=parsed.title,
                    language=parsed.language,
                    evidence_id=evidence_id,
                    content_sha256=body_hash,
                    fetched_at=response.fetched_at,
                    status=response.status,
                    content_type=content_type,
                    byte_length=len(response.body),
                )
            )
            result.evidence.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    requested_url=response.requested_url,
                    final_url=response.final_url,
                    fetched_at=response.fetched_at,
                    http_status=response.status,
                    content_type=content_type,
                    content_sha256=body_hash,
                    byte_length=len(response.body),
                    headers={
                        key: value
                        for key, value in response.headers.items()
                        if key in {"etag", "last-modified", "content-type", "content-language", "cache-control"}
                    },
                    extractor=EXTRACTOR_VERSION,
                    policy_code=decision.code,
                    raw_blob=raw_blob,
                )
            )

            for index, (level, heading, text) in enumerate(parsed.sections):
                section_id = stable_id("section", page_id, str(index), heading, text)
                result.sections.append(
                    SectionRecord(
                        section_id=section_id,
                        page_id=page_id,
                        index=index,
                        level=level,
                        heading=heading,
                        text=text,
                        locator=f"section:{index}",
                    )
                )
                result.edges.append(
                    EdgeRecord(
                        edge_id=stable_id("edge", page_id, section_id, "PAGE_CONTAINS_SECTION"),
                        relation="PAGE_CONTAINS_SECTION",
                        source_id=page_id,
                        target_id=section_id,
                        evidence_id=evidence_id,
                    )
                )

            for raw_link in parsed.links:
                try:
                    link = canonicalize_url(raw_link, base_url=response.final_url)
                except (ValueError, UnicodeError):
                    continue
                target_id = stable_id("page", link)
                result.discovered_urls[target_id] = link
                result.edges.append(
                    EdgeRecord(
                        edge_id=stable_id("edge", page_id, target_id, "PAGE_LINKS_TO_PAGE"),
                        relation="PAGE_LINKS_TO_PAGE",
                        source_id=page_id,
                        target_id=target_id,
                        evidence_id=evidence_id,
                    )
                )
                if link not in queued:
                    queued.add(link)
                    frontier.append(link)

        return result
