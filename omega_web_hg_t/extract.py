from __future__ import annotations

from html.parser import HTMLParser
import re

from .models import ParsedHTML


class SemanticHTMLParser(HTMLParser):
    _TEXT_TAGS = {"p", "li", "blockquote", "pre", "td", "th", "dt", "dd"}
    _IGNORE_TAGS = {"script", "style", "noscript", "svg", "canvas", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.result = ParsedHTML()
        self._ignored_depth = 0
        self._title_depth = 0
        self._heading_level: int | None = None
        self._heading_chunks: list[str] = []
        self._text_depth = 0
        self._text_chunks: list[str] = []
        self._current_level = 0
        self._current_heading = "Document"
        self._current_chunks: list[str] = []

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {key.lower(): value for key, value in attrs}
        if tag in self._IGNORE_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag == "html":
            self.result.language = attr.get("lang")
        elif tag == "title":
            self._title_depth += 1
        elif tag == "link" and (attr.get("rel") or "").lower() == "canonical" and attr.get("href"):
            self.result.canonical_url = attr["href"]
        elif tag == "a" and attr.get("href"):
            self.result.links.append(attr["href"])
        elif re.fullmatch(r"h[1-6]", tag):
            self._flush_section()
            self._heading_level = int(tag[1])
            self._heading_chunks = []
        elif tag in self._TEXT_TAGS:
            self._text_depth += 1
            if self._text_depth == 1:
                self._text_chunks = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._IGNORE_TAGS:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        elif re.fullmatch(r"h[1-6]", tag) and self._heading_level is not None:
            heading = self._clean(" ".join(self._heading_chunks)) or "Section sans titre"
            self._current_level = self._heading_level
            self._current_heading = heading
            self._heading_level = None
            self._heading_chunks = []
        elif tag in self._TEXT_TAGS and self._text_depth:
            self._text_depth -= 1
            if self._text_depth == 0:
                text = self._clean(" ".join(self._text_chunks))
                if text:
                    self._current_chunks.append(text)
                self._text_chunks = []

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._title_depth:
            self.result.title += data
        if self._heading_level is not None:
            self._heading_chunks.append(data)
        if self._text_depth:
            self._text_chunks.append(data)

    def _flush_section(self) -> None:
        text = self._clean("\n".join(self._current_chunks))
        if text:
            self.result.sections.append((self._current_level, self._current_heading, text))
        self._current_chunks = []

    def finish(self) -> ParsedHTML:
        self._flush_section()
        self.result.title = self._clean(self.result.title)
        return self.result


def parse_html(body: bytes, *, content_type: str = "text/html") -> ParsedHTML:
    charset_match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
    charset = charset_match.group(1) if charset_match else "utf-8"
    try:
        text = body.decode(charset, errors="replace")
    except LookupError:
        text = body.decode("utf-8", errors="replace")
    parser = SemanticHTMLParser()
    parser.feed(text)
    parser.close()
    return parser.finish()
