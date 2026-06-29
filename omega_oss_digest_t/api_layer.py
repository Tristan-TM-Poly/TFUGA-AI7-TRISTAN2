from __future__ import annotations

import hashlib
import json
import os
import re
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .license_gate import classify_license
from .oak_runner import oak_decision
from .scorer import DigestScore
from .stackoverflow_attribution import build_attribution, stackoverflow_license_for_date

GITHUB_API = "https://api.github.com"
STACK_API = "https://api.stackexchange.com/2.3"
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_.:/@#+\-]+$")


def token_from_env(name: str) -> str | None:
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else None


def quote_if_needed(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    if _SAFE_TOKEN.match(value):
        return value
    return '"' + value.replace('"', '\\"') + '"'


@dataclass(frozen=True)
class GitHubSearchIntent:
    keywords: tuple[str, ...]
    language: str | None = None
    license: str | None = None
    min_stars: int | None = None
    pushed_after: str | None = None
    topic: str | None = None
    user: str | None = None
    org: str | None = None
    filename: str | None = None
    path: str | None = None


def compile_github_repository_query(intent: GitHubSearchIntent) -> str:
    parts = [quote_if_needed(k) for k in intent.keywords if k.strip()]
    if intent.language:
        parts.append(f"language:{quote_if_needed(intent.language)}")
    if intent.license:
        parts.append(f"license:{quote_if_needed(intent.license)}")
    if intent.min_stars is not None:
        parts.append(f"stars:>={int(intent.min_stars)}")
    if intent.pushed_after:
        parts.append(f"pushed:>{intent.pushed_after}")
    if intent.topic:
        parts.append(f"topic:{quote_if_needed(intent.topic)}")
    if intent.user:
        parts.append(f"user:{quote_if_needed(intent.user)}")
    if intent.org:
        parts.append(f"org:{quote_if_needed(intent.org)}")
    return " ".join(parts)


def compile_github_code_query(intent: GitHubSearchIntent) -> str:
    parts = [quote_if_needed(k) for k in intent.keywords if k.strip()]
    if intent.language:
        parts.append(f"language:{quote_if_needed(intent.language)}")
    if intent.filename:
        parts.append(f"filename:{quote_if_needed(intent.filename)}")
    if intent.path:
        parts.append(f"path:{quote_if_needed(intent.path)}")
    if intent.user:
        parts.append(f"user:{quote_if_needed(intent.user)}")
    if intent.org:
        parts.append(f"org:{quote_if_needed(intent.org)}")
    return " ".join(parts)


def compile_stackoverflow_query(keywords: tuple[str, ...], tags: tuple[str, ...] = ()) -> dict[str, str]:
    return {"q": " ".join(k.strip() for k in keywords if k.strip()), "tagged": ";".join(t.strip() for t in tags if t.strip())}


@dataclass(frozen=True)
class ApiResponseMeta:
    provider: str
    url: str
    status_code: int
    cached: bool = False
    etag: str | None = None
    last_modified: str | None = None
    rate_remaining: str | None = None
    rate_reset: str | None = None
    retry_after: int | None = None
    backoff: int | None = None


@dataclass(frozen=True)
class CachedJsonResponse:
    data: dict[str, Any]
    meta: ApiResponseMeta


Transport = Callable[[urllib.request.Request, float], tuple[int, dict[str, str], bytes]]


class RateLimitError(RuntimeError):
    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class CachedHttpClient:
    """Dependency-free JSON client with disk cache, conditional requests and rate-limit metadata."""

    def __init__(self, cache_dir: str | Path = ".oss_digest_cache", user_agent: str = "omega-oss-digest-t/0.2", min_interval_seconds: float = 1.0, transport: Transport | None = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent
        self.min_interval_seconds = min_interval_seconds
        self.transport = transport or self._urllib_transport
        self._last_request_at: dict[str, float] = {}

    def get_json(self, provider: str, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None, token: str | None = None, timeout: float = 30.0, use_cache: bool = True) -> CachedJsonResponse:
        full_url = self._build_url(url, params)
        key = hashlib.sha256(f"{provider}:{full_url}".encode()).hexdigest()
        data_path = self.cache_dir / f"{key}.json"
        meta_path = self.cache_dir / f"{key}.meta.json"
        previous = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        request_headers = {"Accept": "application/json", "User-Agent": self.user_agent, **(headers or {})}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if previous.get("etag"):
            request_headers["If-None-Match"] = previous["etag"]
        if previous.get("last_modified"):
            request_headers["If-Modified-Since"] = previous["last_modified"]
        self._respect_interval(provider, full_url)
        request = urllib.request.Request(full_url, headers=request_headers, method="GET")
        try:
            status, response_headers, body = self.transport(request, timeout)
        except urllib.error.HTTPError as exc:
            h = {k.lower(): v for k, v in exc.headers.items()}
            if exc.code == 304 and data_path.exists():
                return CachedJsonResponse(json.loads(data_path.read_text(encoding="utf-8")), ApiResponseMeta(provider, full_url, 304, cached=True, **self._meta_from_headers(h)))
            retry_after = self._retry_after(h)
            if exc.code in {403, 429}:
                raise RateLimitError(f"{provider} rate-limited request", retry_after)
            raise
        h = {k.lower(): v for k, v in response_headers.items()}
        if status == 304 and data_path.exists():
            return CachedJsonResponse(json.loads(data_path.read_text(encoding="utf-8")), ApiResponseMeta(provider, full_url, status, cached=True, **self._meta_from_headers(h)))
        data = json.loads(body.decode("utf-8"))
        backoff = data.get("backoff") if isinstance(data, dict) else None
        meta = ApiResponseMeta(provider, full_url, status, cached=False, backoff=int(backoff) if backoff is not None else None, **self._meta_from_headers(h))
        if use_cache:
            data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            meta_path.write_text(json.dumps(meta.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
        return CachedJsonResponse(data, meta)

    def _respect_interval(self, provider: str, url: str) -> None:
        key = f"{provider}:{url}"
        previous = self._last_request_at.get(key)
        now = time.monotonic()
        if previous is not None:
            remaining = self.min_interval_seconds - (now - previous)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at[key] = time.monotonic()

    @staticmethod
    def _urllib_transport(request: urllib.request.Request, timeout: float) -> tuple[int, dict[str, str], bytes]:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310: intended API client
            return response.status, dict(response.headers.items()), response.read()

    @staticmethod
    def _build_url(url: str, params: dict[str, Any] | None) -> str:
        if not params:
            return url
        clean = {k: v for k, v in params.items() if v is not None}
        return url + ("&" if "?" in url else "?") + urllib.parse.urlencode(clean, doseq=True)

    @staticmethod
    def _retry_after(headers: dict[str, str]) -> int | None:
        raw = headers.get("retry-after")
        if raw and raw.isdigit():
            return int(raw)
        reset = headers.get("x-ratelimit-reset")
        if reset and reset.isdigit():
            return max(0, int(reset) - int(time.time()))
        return None

    def _meta_from_headers(self, headers: dict[str, str]) -> dict[str, Any]:
        return {"etag": headers.get("etag"), "last_modified": headers.get("last-modified"), "rate_remaining": headers.get("x-ratelimit-remaining"), "rate_reset": headers.get("x-ratelimit-reset"), "retry_after": self._retry_after(headers)}


@dataclass(frozen=True)
class GitHubRepositoryCandidate:
    full_name: str
    html_url: str
    description: str | None
    license_id: str | None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    pushed_at: str | None = None
    updated_at: str | None = None
    default_branch: str | None = None
    topics: tuple[str, ...] = ()
    language: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "GitHubRepositoryCandidate":
        lic = item.get("license") or {}
        return cls(item.get("full_name", ""), item.get("html_url", ""), item.get("description"), lic.get("spdx_id") if isinstance(lic, dict) else None, int(item.get("stargazers_count") or 0), int(item.get("forks_count") or item.get("forks") or 0), int(item.get("open_issues_count") or 0), item.get("pushed_at"), item.get("updated_at"), item.get("default_branch"), tuple(item.get("topics") or ()), item.get("language"), item)

    def provenance_source_id(self) -> str:
        return f"github:{self.full_name}"


class GitHubApiClient:
    def __init__(self, http: CachedHttpClient | None = None, token: str | None = None) -> None:
        self.http = http or CachedHttpClient(cache_dir=".oss_digest_cache/github")
        self.token = token if token is not None else token_from_env("GITHUB_TOKEN")

    def search_repositories(self, intent: GitHubSearchIntent, per_page: int = 10, page: int = 1, sort: str | None = "stars", order: str = "desc") -> list[GitHubRepositoryCandidate]:
        response = self.http.get_json("github", f"{GITHUB_API}/search/repositories", params={"q": compile_github_repository_query(intent), "per_page": per_page, "page": page, "sort": sort, "order": order}, headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}, token=self.token)
        return [GitHubRepositoryCandidate.from_api(item) for item in response.data.get("items", [])]

    def search_code(self, intent: GitHubSearchIntent, per_page: int = 10, page: int = 1) -> CachedJsonResponse:
        return self.http.get_json("github", f"{GITHUB_API}/search/code", params={"q": compile_github_code_query(intent), "per_page": per_page, "page": page}, headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}, token=self.token)


def github_candidate_to_source(candidate: GitHubRepositoryCandidate) -> dict[str, Any]:
    return {"source_id": candidate.provenance_source_id(), "source_type": "github_repository", "name": candidate.full_name, "url": candidate.html_url, "license_id": candidate.license_id, "fit": 0.7, "license_compatibility": 0.8 if candidate.license_id else 0.1, "tests": 0.5, "security": 0.5, "maintainability": min(1.0, 0.4 + candidate.stars / 5000), "cvcd_compressibility": 0.6, "utility": 0.7, "community_activity": min(1.0, 0.3 + candidate.stars / 10000), "risk": 0.4 if not candidate.license_id else 0.25, "metadata": asdict(candidate)}


@dataclass(frozen=True)
class StackOverflowQuestionCandidate:
    question_id: int
    title: str
    link: str
    creation_date: int
    last_activity_date: int | None
    tags: tuple[str, ...]
    score: int
    answer_count: int
    is_answered: bool
    accepted_answer_id: int | None = None
    owner_display_name: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "StackOverflowQuestionCandidate":
        owner = item.get("owner") or {}
        return cls(int(item["question_id"]), item.get("title", ""), item.get("link", ""), int(item.get("creation_date") or 0), item.get("last_activity_date"), tuple(item.get("tags") or ()), int(item.get("score") or 0), int(item.get("answer_count") or 0), bool(item.get("is_answered")), item.get("accepted_answer_id"), owner.get("display_name") if isinstance(owner, dict) else None, item)

    def provenance_source_id(self) -> str:
        return f"stackoverflow:question:{self.question_id}"


class StackExchangeApiClient:
    def __init__(self, http: CachedHttpClient | None = None, key: str | None = None, access_token: str | None = None) -> None:
        self.http = http or CachedHttpClient(cache_dir=".oss_digest_cache/stackexchange", min_interval_seconds=60.0)
        self.key = key if key is not None else token_from_env("STACKEXCHANGE_KEY")
        self.access_token = access_token if access_token is not None else token_from_env("STACKEXCHANGE_ACCESS_TOKEN")

    def search_advanced(self, keywords: tuple[str, ...], tags: tuple[str, ...] = (), site: str = "stackoverflow", pagesize: int = 10, page: int = 1, sort: str = "relevance", accepted: bool | None = None) -> list[StackOverflowQuestionCandidate]:
        params: dict[str, Any] = {"site": site, "pagesize": pagesize, "page": page, "sort": sort, "filter": "default", **compile_stackoverflow_query(keywords, tags)}
        if accepted is not None:
            params["accepted"] = str(bool(accepted)).lower()
        if self.key:
            params["key"] = self.key
        if self.access_token:
            params["access_token"] = self.access_token
        response = self.http.get_json("stackexchange", f"{STACK_API}/search/advanced", params=params)
        return [StackOverflowQuestionCandidate.from_api(item) for item in response.data.get("items", [])]


def stack_question_to_source(question: StackOverflowQuestionCandidate) -> dict[str, Any]:
    created = datetime.fromtimestamp(question.creation_date, tz=timezone.utc).date()
    license_id = stackoverflow_license_for_date(created)
    attribution = build_attribution(question.question_id, question.title, question.link, created, question.owner_display_name, question.accepted_answer_id)
    return {"source_id": question.provenance_source_id(), "source_type": "stackoverflow_question", "name": question.title, "url": question.link, "license_id": license_id, "fit": 0.65, "license_compatibility": 0.4, "tests": 0.2, "security": 0.4, "maintainability": 0.5, "cvcd_compressibility": 0.75, "utility": min(1.0, 0.4 + question.score / 100), "community_activity": min(1.0, 0.3 + question.answer_count / 20), "risk": 0.55, "attribution": attribution.asdict(), "metadata": asdict(question)}


@dataclass(frozen=True)
class SecretFinding:
    kind: str
    line: int
    match_preview: str
    severity: str = "high"


SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")), ("generic_api_key", re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}")), ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")), ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")))


def scan_text_for_secrets(text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(SecretFinding(kind, lineno, match.group(0)[:12] + "…"))
    return findings


def local_dependency_inventory(root: str | Path) -> dict[str, list[str]]:
    root = Path(root)
    inventory: dict[str, list[str]] = {}
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        inventory["pyproject.toml"] = list((data.get("project", {}) or {}).get("dependencies", []) or [])
    package_json = root / "package.json"
    if package_json.exists():
        data = json.loads(package_json.read_text(encoding="utf-8"))
        deps: list[str] = []
        for section in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
            deps.extend(f"{name}@{version}" for name, version in (data.get(section) or {}).items())
        inventory["package.json"] = deps
    return inventory


def digest_github_search(intent: GitHubSearchIntent, limit: int = 10) -> list[dict[str, Any]]:
    results = []
    for candidate in GitHubApiClient().search_repositories(intent, per_page=limit):
        source = github_candidate_to_source(candidate)
        score = DigestScore(fit=source["fit"], license_compatibility=source["license_compatibility"], tests=source["tests"], security=source["security"], maintainability=source["maintainability"], cvcd_compressibility=source["cvcd_compressibility"], utility=source["utility"], community_activity=source["community_activity"], risk=source["risk"])
        source["oak_decision"] = asdict(oak_decision(source.get("license_id"), score))
        source["license_decision"] = asdict(classify_license(source.get("license_id")))
        results.append(source)
    return results
