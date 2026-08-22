"""Ω-OMNI-INGEST-OAK v0.4 compact integration module.

Status: TESTED_SOFTWARE / NON_CERTIFIED_PHYSICAL.
Core invariant: source capture != software test != simulation != prototype != measurement.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EvidenceStatus(str, Enum):
    IDEA = "IDEA"
    FORMAL = "FORMAL"
    SOURCE_CAPTURED = "SOURCE_CAPTURED"
    TESTED_SOFTWARE = "TESTED_SOFTWARE"
    SIMULATED = "SIMULATED"
    PROTOTYPE = "PROTOTYPE"
    MEASURED = "MEASURED"
    CERTIFIED_EXTERNAL = "CERTIFIED_EXTERNAL"
    QUARANTINE = "QUARANTINE"


@dataclass(frozen=True)
class Receipt:
    artifact_id: str
    source: str
    sha256: str
    byte_count: int
    content_type: str = "application/octet-stream"
    status: EvidenceStatus = EvidenceStatus.SOURCE_CAPTURED
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provenance: dict[str, Any] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass(frozen=True)
class OAKVerdict:
    status: EvidenceStatus
    reason: str
    falsifiers: tuple[str, ...] = ()
    required_next_evidence: tuple[str, ...] = ()
    auto_promotable: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


import ipaddress
import socket
from urllib.parse import urlparse


class PolicyError(ValueError):
    pass


@dataclass(frozen=True)
class NetworkPolicy:
    allow_http: bool = False
    allow_private_networks: bool = False
    allowed_domains: tuple[str, ...] = ()
    denied_domains: tuple[str, ...] = ()
    max_bytes: int = 10_000_000
    user_agent: str = "OMEGA-OMNI-OAK/0.4 (+research; provenance-first)"

    def validate_url(self, url: str, resolve_dns: bool = False) -> str:
        p = urlparse(url)
        if p.scheme not in {"https", "http"}:
            raise PolicyError("Only HTTP(S) URLs are allowed.")
        if p.scheme == "http" and not self.allow_http:
            raise PolicyError("Plain HTTP is disabled by default.")
        if not p.hostname:
            raise PolicyError("URL must contain a hostname.")
        if p.username or p.password:
            raise PolicyError("Embedded credentials are forbidden.")

        host = p.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(".local"):
            raise PolicyError("Local-network targets are forbidden.")

        if self.denied_domains and any(host == d or host.endswith("." + d) for d in self.denied_domains):
            raise PolicyError("Domain is denied by policy.")
        if self.allowed_domains and not any(host == d or host.endswith("." + d) for d in self.allowed_domains):
            raise PolicyError("Domain is outside the allowlist.")

        self._reject_private_literal(host)
        if resolve_dns:
            self._reject_private_resolution(host)
        return url

    def _reject_private_literal(self, host: str) -> None:
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return
        if not self.allow_private_networks and not ip.is_global:
            raise PolicyError("Non-global IP targets are forbidden.")

    def _reject_private_resolution(self, host: str) -> None:
        if self.allow_private_networks:
            return
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_global:
                raise PolicyError(f"Hostname resolves to non-global IP: {ip}")


_FORBIDDEN_AUTO = {EvidenceStatus.MEASURED, EvidenceStatus.CERTIFIED_EXTERNAL}


def verdict_for_capture(*, has_source: bool, has_test: bool = False, external_measurement_receipt: bool = False) -> OAKVerdict:
    if not has_source:
        return OAKVerdict(
            status=EvidenceStatus.QUARANTINE,
            reason="No provenance-bearing source receipt.",
            required_next_evidence=("source receipt",),
        )
    if external_measurement_receipt:
        return OAKVerdict(
            status=EvidenceStatus.MEASURED,
            reason="External measurement receipt supplied; measurement remains subject to calibration/reproducibility review.",
            falsifiers=("calibration failure", "non-reproducibility", "provenance break"),
            auto_promotable=False,
        )
    if has_test:
        return OAKVerdict(
            status=EvidenceStatus.TESTED_SOFTWARE,
            reason="Software behavior has a test receipt; no physical certification implied.",
            falsifiers=("test regression", "environment mismatch"),
        )
    return OAKVerdict(
        status=EvidenceStatus.SOURCE_CAPTURED,
        reason="Source captured with provenance; claim not yet tested.",
        required_next_evidence=("explicit claim", "failure condition", "independent test"),
    )


def assert_no_false_certification(status: EvidenceStatus, *, automation_generated: bool) -> None:
    if automation_generated and status in _FORBIDDEN_AUTO:
        raise AssertionError("Automation may not self-assign MEASURED or CERTIFIED_EXTERNAL.")


import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class ToolProposal:
    proposal_id: str
    sample_name: str
    extension: str
    sample_sha256: str
    status: str
    created_at_utc: str
    required_gates: tuple[str, ...]
    note: str

    def to_dict(self):
        return asdict(self)


def propose_parser(sample: Path, proposal_dir: Path) -> ToolProposal:
    raw = sample.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    ext = sample.suffix.lower() or ".unknown"
    pid = f"parser_{ext.lstrip('.') or 'unknown'}_{sha[:12]}"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal = ToolProposal(
        proposal_id=pid,
        sample_name=sample.name,
        extension=ext,
        sample_sha256=sha,
        status="QUARANTINE",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        required_gates=("fixture tests", "negative tests", "resource limits", "manual/independent approval"),
        note="Generated parser scaffolds are proposals, not trusted tools. Execute untrusted candidates only in a real container/sandbox.",
    )
    (proposal_dir / f"{pid}.json").write_text(json.dumps(proposal.to_dict(), indent=2), encoding="utf-8")
    scaffold = f'''"""Parser proposal for {ext}; QUARANTINE until independently tested."""\n\ndef parse(data: bytes):\n    raise NotImplementedError("Implement parser for {ext} and add positive/negative fixtures before promotion")\n'''
    (proposal_dir / f"{pid}.py").write_text(scaffold, encoding="utf-8")
    return proposal


from urllib.parse import quote_plus


@dataclass(frozen=True)
class SourceRequest:
    name: str
    url: str
    access_basis: str
    obey_robots: bool
    max_requests_per_second: float


def arxiv_query(query: str, max_results: int = 10) -> SourceRequest:
    q = quote_plus(query)
    n = max(1, min(int(max_results), 100))
    return SourceRequest(
        name="arXiv",
        url=f"https://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={n}",
        access_basis="documented_public_api",
        obey_robots=False,
        max_requests_per_second=0.33,
    )


def pubchem_compound_by_name(name: str) -> SourceRequest:
    n = quote_plus(name)
    return SourceRequest(
        name="PubChem PUG REST",
        url=f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{n}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey/JSON",
        access_basis="documented_public_api; client cap <= 5 req/s",
        obey_robots=False,
        max_requests_per_second=4.0,
    )


def crossref_works(query: str, rows: int = 10) -> SourceRequest:
    q = quote_plus(query)
    r = max(1, min(int(rows), 100))
    return SourceRequest(
        name="Crossref REST",
        url=f"https://api.crossref.org/works?query={q}&rows={r}",
        access_basis="documented_public_api",
        obey_robots=False,
        max_requests_per_second=1.0,
    )


def openalex_works(search: str, per_page: int = 10) -> SourceRequest:
    q = quote_plus(search)
    p = max(1, min(int(per_page), 100))
    return SourceRequest(
        name="OpenAlex",
        url=f"https://api.openalex.org/works?search={q}&per-page={p}",
        access_basis="documented_public_api",
        obey_robots=False,
        max_requests_per_second=1.0,
    )


import re
from html.parser import HTMLParser
from typing import Any as _Any


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def extract_text(raw: bytes, content_type: str) -> str:
    ct = content_type.lower()
    if "json" in ct:
        obj: _Any = json.loads(raw.decode("utf-8", errors="replace"))
        return json.dumps(obj, ensure_ascii=False, indent=2)
    text = raw.decode("utf-8", errors="replace")
    if "html" in ct:
        p = _TextHTMLParser()
        p.feed(text)
        return p.text()
    return text


def rough_word_count(text: str) -> int:
    return len(re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'-]+\b", text, flags=re.UNICODE))


def equation_like_line_count(text: str) -> int:
    """Heuristic formalism count; deliberately not labeled 'exact equations'."""
    symbols = re.compile(r"(?:[=≠≤≥→←↔∑∫√λΩΔπσρμ]|\\(?:boxed|sum|int|mathcal|frac|begin\{equation))")
    return sum(1 for line in text.splitlines() if symbols.search(line))


def write_derived_text(raw_path: Path, content_type: str, out_path: Path) -> dict[str, int]:
    text = extract_text(raw_path.read_bytes(), content_type)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return {"words": rough_word_count(text), "equation_like_lines": equation_like_line_count(text)}


@dataclass(frozen=True)
class PDFStats:
    file: str
    pages: int
    words_extracted: int
    equation_like_lines: int
    extraction_warnings: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


def analyze_pdf(path: Path) -> PDFStats:
    warnings: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as e:
        raise RuntimeError("PDF statistics require optional dependency: pip install 'omega-omni-ingest-oak[pdf]'") from e

    reader = PdfReader(str(path))
    texts: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            texts.append(page.extract_text() or "")
        except Exception as exc:
            warnings.append(f"page {i+1}: {type(exc).__name__}")
            texts.append("")
    text = "\n".join(texts)
    return PDFStats(
        file=path.name,
        pages=len(reader.pages),
        words_extracted=rough_word_count(text),
        equation_like_lines=equation_like_line_count(text),
        extraction_warnings=tuple(warnings),
    )


import time
import urllib.error
import urllib.request
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser


@dataclass(frozen=True)
class FetchResult:
    receipt: Receipt
    raw_path: Path
    headers_path: Path


class PoliteFetcher:
    """Bounded public-web fetcher with provenance and SSRF guards.

    Generic HTML fetching checks robots.txt. Documented API endpoints can opt out of
    robots enforcement only when the caller records an explicit access_basis.
    """

    def __init__(self, vault: Path, policy: NetworkPolicy | None = None, min_interval_s: float = 1.0):
        self.vault = Path(vault)
        self.policy = policy or NetworkPolicy()
        self.min_interval_s = max(0.0, min_interval_s)
        self._last_fetch: dict[str, float] = {}
        (self.vault / "raw").mkdir(parents=True, exist_ok=True)
        (self.vault / "receipts").mkdir(parents=True, exist_ok=True)

    def fetch(self, url: str, *, access_basis: str = "public_web", obey_robots: bool = True) -> FetchResult:
        self.policy.validate_url(url, resolve_dns=True)
        host = urlparse(url).hostname or ""
        self._throttle(host)
        if obey_robots and not self._robots_allowed(url):
            raise PolicyError("robots.txt disallows this URL for the configured user agent.")

        req = urllib.request.Request(url, headers={"User-Agent": self.policy.user_agent, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                final_url = resp.geturl()
                self.policy.validate_url(final_url, resolve_dns=True)
                content_type = resp.headers.get_content_type() or "application/octet-stream"
                raw = resp.read(self.policy.max_bytes + 1)
                if len(raw) > self.policy.max_bytes:
                    raise PolicyError(f"Response exceeded max_bytes={self.policy.max_bytes}.")
                headers = {k: v for k, v in resp.headers.items()}
                status_code = getattr(resp, "status", 200)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code} for {url}") from e

        sha = hashlib.sha256(raw).hexdigest()
        raw_path = self.vault / "raw" / f"{sha}.bin"
        raw_path.write_bytes(raw)
        headers_path = self.vault / "receipts" / f"{sha}.headers.json"
        headers_payload = {
            "requested_url": url,
            "final_url": final_url,
            "status_code": status_code,
            "headers": headers,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "access_basis": access_basis,
            "robots_obeyed": obey_robots,
        }
        headers_path.write_text(json.dumps(headers_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        receipt = Receipt(
            artifact_id=sha[:16],
            source=final_url,
            sha256=sha,
            byte_count=len(raw),
            content_type=content_type,
            status=EvidenceStatus.SOURCE_CAPTURED,
            provenance=headers_payload,
            limitations=("Source capture is not scientific validation.",),
        )
        (self.vault / "receipts" / f"{sha}.receipt.json").write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return FetchResult(receipt=receipt, raw_path=raw_path, headers_path=headers_path)

    def _throttle(self, host: str) -> None:
        now = time.monotonic()
        last = self._last_fetch.get(host)
        if last is not None:
            wait = self.min_interval_s - (now - last)
            if wait > 0:
                time.sleep(wait)
        self._last_fetch[host] = time.monotonic()

    def _robots_allowed(self, url: str) -> bool:
        p = urlparse(url)
        robots_url = urljoin(f"{p.scheme}://{p.netloc}", "/robots.txt")
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            req = urllib.request.Request(robots_url, headers={"User-Agent": self.policy.user_agent})
            with urllib.request.urlopen(req, timeout=10) as resp:
                text = resp.read(512_000).decode("utf-8", errors="replace")
            rp.parse(text.splitlines())
        except Exception:
            return False
        return rp.can_fetch(self.policy.user_agent, url)
