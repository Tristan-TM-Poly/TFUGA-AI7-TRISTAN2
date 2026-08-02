from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


USER_AGENT = (
    "WikiForge-T/0.1 "
    "(https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2; "
    "read-only research client)"
)
LANG_RE = re.compile(r"^[a-z][a-z0-9-]{1,19}$")
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ0-9])|(?<=[。！？])")
NUMBER_TOKEN = re.compile(r"(?<!\w)[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)(?:\s?%|\s?[A-Za-zµμ°Ω]+)?")
DATE_TOKEN = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b")
CITATION_TOKEN = re.compile(r"\[REF:[^\]]+\]")


class MediaWikiError(RuntimeError):
    """Raised when a Wikimedia response cannot be safely interpreted."""


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{sha256(raw).hexdigest()[:20]}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonable(record: object) -> dict[str, Any]:
    return asdict(record)  # type: ignore[arg-type]


def invariant_tokens(text: str) -> set[str]:
    """Return translation invariants that must not silently disappear.

    This deliberately favors false positives over silent loss. The token set is
    an audit aid, not a semantic proof of translation quality.
    """

    tokens: set[str] = set()
    for pattern in (NUMBER_TOKEN, DATE_TOKEN, CITATION_TOKEN):
        tokens.update(match.group(0).strip() for match in pattern.finditer(text))
    return tokens


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    article_id: str
    url: str
    retrieved_at: str
    source_type: str = "external_link_unclassified"
    oak_status: str = "unverified_metadata"


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    article_id: str
    language: str
    section: str
    paragraph_index: int
    sentence_index: int
    original_text: str
    citation_markers: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    status: str = "claim_candidate"
    oak_residues: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArticleRecord:
    article_id: str
    qid: str | None
    project: str
    language: str
    requested_title: str
    canonical_title: str
    canonical_url: str
    revision_id: int | None
    revision_timestamp: str | None
    revision_sha1: str | None
    fetched_at: str
    content_hash: str
    sections: tuple[str, ...]
    paragraphs: tuple[str, ...]
    langlinks: Mapping[str, str]
    source_ids: tuple[str, ...]
    license_note: str = (
        "Imported Wikimedia content retains source-specific attribution and "
        "license obligations; inspect the page footer and manifest before reuse."
    )


@dataclass(frozen=True)
class CompileResult:
    topic: str
    source_language: str
    qid: str | None
    generated_at: str
    articles: tuple[ArticleRecord, ...]
    claims: tuple[ClaimRecord, ...]
    sources: tuple[SourceRecord, ...]
    missing_languages: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass
class _ParsedHTML:
    sections: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    paragraph_markers: list[list[str]] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)


class _WikiHTMLExtractor(HTMLParser):
    """Small, dependency-free extractor for Parsoid/parser HTML.

    It extracts readable paragraphs, section headings, inline reference marker
    anchors, and external links inside citation elements. It intentionally does
    not pretend to fully model every MediaWiki template.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.result = _ParsedHTML()
        self._paragraph: list[str] | None = None
        self._heading: list[str] | None = None
        self._markers: list[str] = []
        self._inside_reference_sup = False
        self._inside_cite = False

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = self._attrs(attrs)
        classes = set(attributes.get("class", "").split())
        if tag == "p":
            self._paragraph = []
            self._markers = []
        elif tag in {"h2", "h3", "h4", "h5", "h6"}:
            self._heading = []
        elif tag == "sup" and "reference" in classes:
            self._inside_reference_sup = True
        elif tag == "cite":
            self._inside_cite = True
        elif tag == "a":
            href = attributes.get("href", "")
            if self._inside_reference_sup and href:
                marker = href.rsplit("#", 1)[-1]
                if marker and marker not in self._markers:
                    self._markers.append(marker)
            if self._inside_cite and href.startswith(("http://", "https://")):
                if href not in self.result.source_urls:
                    self.result.source_urls.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._paragraph is not None:
            text = " ".join("".join(self._paragraph).split())
            if text:
                self.result.paragraphs.append(text)
                self.result.paragraph_markers.append(list(self._markers))
            self._paragraph = None
            self._markers = []
        elif tag in {"h2", "h3", "h4", "h5", "h6"} and self._heading is not None:
            text = " ".join("".join(self._heading).split())
            if text:
                self.result.sections.append(text)
            self._heading = None
        elif tag == "sup":
            self._inside_reference_sup = False
        elif tag == "cite":
            self._inside_cite = False

    def handle_data(self, data: str) -> None:
        if self._paragraph is not None:
            self._paragraph.append(data)
        if self._heading is not None:
            self._heading.append(data)


class MediaWikiClient:
    """Read-only Action API client with identification, retry, and throttling."""

    def __init__(
        self,
        language: str,
        *,
        timeout: float = 25.0,
        min_interval: float = 0.15,
        user_agent: str = USER_AGENT,
        max_retries: int = 3,
    ) -> None:
        if not LANG_RE.fullmatch(language):
            raise ValueError(f"Unsafe or unsupported language code: {language!r}")
        self.language = language
        self.timeout = timeout
        self.min_interval = min_interval
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.endpoint = f"https://{language}.wikipedia.org/w/api.php"
        self._last_request = 0.0

    def _request(self, params: Mapping[str, object]) -> dict[str, Any]:
        query = {"format": "json", "formatversion": 2, **params}
        url = f"{self.endpoint}?{urlencode(query, doseq=True)}"
        delay = max(0.0, self.min_interval - (time.monotonic() - self._last_request))
        if delay:
            time.sleep(delay)

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                request = Request(url, headers={"User-Agent": self.user_agent})
                with urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self._last_request = time.monotonic()
                if "error" in payload:
                    raise MediaWikiError(str(payload["error"]))
                return payload
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt + 1 < self.max_retries:
                    time.sleep(0.5 * (2**attempt))
        raise MediaWikiError(f"MediaWiki request failed: {last_error}")

    def resolve(self, title: str) -> dict[str, Any]:
        payload = self._request(
            {
                "action": "query",
                "redirects": 1,
                "titles": title,
                "prop": "info|pageprops|langlinks|revisions",
                "inprop": "url",
                "lllimit": "max",
                "rvprop": "ids|timestamp|sha1",
                "rvlimit": 1,
            }
        )
        pages = payload.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            raise MediaWikiError(f"Page not found: {title!r} ({self.language})")
        return pages[0]

    def parse(self, title: str) -> dict[str, Any]:
        payload = self._request(
            {
                "action": "parse",
                "page": title,
                "redirects": 1,
                "prop": "text|sections|externallinks|langlinks|revid",
            }
        )
        parsed = payload.get("parse")
        if not isinstance(parsed, dict):
            raise MediaWikiError(f"Unable to parse page: {title!r}")
        return parsed


def _langlink_map(page: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in page.get("langlinks", []) or []:
        lang = item.get("lang")
        title = item.get("title") or item.get("*")
        if isinstance(lang, str) and isinstance(title, str):
            result[lang] = title
    return result


def _split_claims(text: str) -> list[str]:
    return [piece.strip() for piece in SENTENCE_BOUNDARY.split(text) if piece.strip()]


class CitationPreservingTranslator:
    """Backend-neutral translation guard.

    The backend receives text where citation markers remain explicit. Missing
    numerical/date/reference tokens make the translation fail closed.
    """

    def __init__(self, backend: Callable[[str, str, str], str]) -> None:
        self.backend = backend

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        translated = self.backend(text, source_language, target_language)
        missing = invariant_tokens(text) - invariant_tokens(translated)
        if missing:
            raise ValueError(f"Translation lost invariants: {sorted(missing)!r}")
        return translated


class WikiCompiler:
    def __init__(self, client_factory: Callable[[str], MediaWikiClient] = MediaWikiClient) -> None:
        self.client_factory = client_factory

    def _compile_article(self, requested_title: str, language: str) -> tuple[ArticleRecord, list[ClaimRecord], list[SourceRecord]]:
        client = self.client_factory(language)
        page = client.resolve(requested_title)
        canonical_title = str(page["title"])
        parsed = client.parse(canonical_title)

        extractor = _WikiHTMLExtractor()
        extractor.feed(str(parsed.get("text", "")))
        extracted = extractor.result

        external_links: list[str] = []
        for url in [*extracted.source_urls, *(parsed.get("externallinks", []) or [])]:
            if isinstance(url, str) and url.startswith(("http://", "https://")) and url not in external_links:
                external_links.append(url)

        revision = (page.get("revisions") or [{}])[0]
        revision_id = revision.get("revid") or parsed.get("revid")
        fetched_at = _utc_now()
        article_id = f"{language}wiki:{canonical_title.replace(' ', '_')}:{revision_id or 'unknown'}"

        sources = [
            SourceRecord(
                source_id=_stable_id("source", article_id, url),
                article_id=article_id,
                url=url,
                retrieved_at=fetched_at,
            )
            for url in external_links
        ]
        source_ids = tuple(source.source_id for source in sources)

        claims: list[ClaimRecord] = []
        current_section = "lead"
        section_iter = iter(extracted.sections)
        next_section = next(section_iter, None)
        # Paragraph-to-heading boundaries are not perfectly recoverable from the
        # compact parser output, so R0.1 keeps lead/known-section metadata honest.
        for paragraph_index, paragraph in enumerate(extracted.paragraphs):
            if paragraph_index > 0 and next_section is not None and paragraph_index % 8 == 0:
                current_section = next_section
                next_section = next(section_iter, None)
            markers = tuple(extracted.paragraph_markers[paragraph_index])
            residues: tuple[str, ...] = () if markers else ("no_inline_reference_marker_detected",)
            for sentence_index, sentence in enumerate(_split_claims(paragraph)):
                claim_id = _stable_id("claim", article_id, paragraph_index, sentence_index, sentence)
                claims.append(
                    ClaimRecord(
                        claim_id=claim_id,
                        article_id=article_id,
                        language=language,
                        section=current_section,
                        paragraph_index=paragraph_index,
                        sentence_index=sentence_index,
                        original_text=sentence,
                        citation_markers=markers,
                        source_ids=source_ids if markers else (),
                        oak_residues=residues,
                    )
                )

        content_hash = sha256(str(parsed.get("text", "")).encode("utf-8")).hexdigest()
        article = ArticleRecord(
            article_id=article_id,
            qid=(page.get("pageprops") or {}).get("wikibase_item"),
            project="wikipedia",
            language=language,
            requested_title=requested_title,
            canonical_title=canonical_title,
            canonical_url=str(page.get("canonicalurl") or page.get("fullurl") or ""),
            revision_id=int(revision_id) if revision_id is not None else None,
            revision_timestamp=revision.get("timestamp"),
            revision_sha1=revision.get("sha1"),
            fetched_at=fetched_at,
            content_hash=content_hash,
            sections=tuple(extracted.sections),
            paragraphs=tuple(extracted.paragraphs),
            langlinks=_langlink_map(page),
            source_ids=source_ids,
        )
        return article, claims, sources

    def compile(
        self,
        topic: str,
        *,
        source_language: str = "fr",
        target_languages: Sequence[str] | str = (),
        max_languages: int | None = 20,
    ) -> CompileResult:
        primary, primary_claims, primary_sources = self._compile_article(topic, source_language)
        available = dict(primary.langlinks)

        if target_languages == "all":
            languages = sorted(available)
            if max_languages is not None and max_languages > 0:
                languages = languages[:max_languages]
        else:
            languages = []
            for language in target_languages:
                if language != source_language and language not in languages:
                    languages.append(language)

        articles = [primary]
        claims = list(primary_claims)
        sources = list(primary_sources)
        missing: list[str] = []
        warnings: list[str] = [
            "R0.1 extracts claim candidates; citation entailment and source quality are not yet verified.",
            "Cross-language presence is not consensus and translation is not performed automatically.",
        ]

        for language in languages:
            title = available.get(language)
            if not title:
                missing.append(language)
                continue
            try:
                article, article_claims, article_sources = self._compile_article(title, language)
            except (MediaWikiError, ValueError) as exc:
                missing.append(language)
                warnings.append(f"{language}: {exc}")
                continue
            articles.append(article)
            claims.extend(article_claims)
            sources.extend(article_sources)

        return CompileResult(
            topic=topic,
            source_language=source_language,
            qid=primary.qid,
            generated_at=_utc_now(),
            articles=tuple(articles),
            claims=tuple(claims),
            sources=tuple(sources),
            missing_languages=tuple(missing),
            warnings=tuple(warnings),
        )

    @staticmethod
    def write(result: CompileResult, output_dir: str | Path) -> Path:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema": "omega_wiki_t.manifest.v0.1",
            "topic": result.topic,
            "source_language": result.source_language,
            "qid": result.qid,
            "generated_at": result.generated_at,
            "article_count": len(result.articles),
            "claim_candidate_count": len(result.claims),
            "source_link_count": len(result.sources),
            "missing_languages": list(result.missing_languages),
            "warnings": list(result.warnings),
            "oak_status": "R0.1_READ_ONLY_EXTRACTION_SCAFFOLD_NOT_VERIFICATION",
        }
        (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        for filename, records in (
            ("articles.jsonl", result.articles),
            ("claims.jsonl", result.claims),
            ("sources.jsonl", result.sources),
        ):
            with (output / filename).open("w", encoding="utf-8") as stream:
                for record in records:
                    stream.write(json.dumps(_jsonable(record), ensure_ascii=False) + "\n")

        matrix = {
            article.language: {
                "title": article.canonical_title,
                "revision_id": article.revision_id,
                "section_count": len(article.sections),
                "paragraph_count": len(article.paragraphs),
                "source_link_count": len(article.source_ids),
                "content_hash": article.content_hash,
            }
            for article in result.articles
        }
        (output / "language-matrix.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output / "report.md").write_text(_render_report(result), encoding="utf-8")
        return output


def _render_report(result: CompileResult) -> str:
    lines = [
        f"# WikiForge-T report — {result.topic}",
        "",
        f"- QID: `{result.qid or 'unresolved'}`",
        f"- Generated: `{result.generated_at}`",
        f"- Languages compiled: {', '.join(article.language for article in result.articles)}",
        f"- Claim candidates: {len(result.claims)}",
        f"- External source links: {len(result.sources)}",
        "",
        "## OAK boundary",
        "",
        "This report is a read-only extraction scaffold. Wikipedia text is not proof; an external link is not automatically a supporting source; multilingual agreement is not automatically consensus.",
        "",
        "## Language matrix",
        "",
        "| Language | Title | Revision | Sections | Paragraphs | Source links |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for article in result.articles:
        lines.append(
            f"| {article.language} | {article.canonical_title} | {article.revision_id or ''} | "
            f"{len(article.sections)} | {len(article.paragraphs)} | {len(article.source_ids)} |"
        )

    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in result.warnings)
    if result.missing_languages:
        lines.append(f"- Missing or failed languages: {', '.join(result.missing_languages)}")

    lines.extend(["", "## Sample claim candidates", ""])
    for claim in result.claims[:20]:
        marker = ", ".join(claim.citation_markers) or "no inline marker"
        lines.append(f"- **[{claim.language}]** {claim.original_text}  \n  Evidence marker: `{marker}`")
    lines.append("")
    return "\n".join(lines)
