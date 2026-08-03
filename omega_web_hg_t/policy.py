from __future__ import annotations

import ipaddress
import socket
import time
from typing import Callable, Iterable, Mapping
from urllib.parse import urlsplit
from urllib.request import Request, build_opener
from urllib.robotparser import RobotFileParser

from .models import CrawlConfig, FetchResponse, PolicyDecision, SafeRedirectHandler, canonicalize_url, utc_now


class PolicyGate:
    def __init__(
        self,
        config: CrawlConfig,
        *,
        resolver: Callable[[str], Iterable[str]] | None = None,
        robots_loader: Callable[[str], str | None] | None = None,
    ) -> None:
        self.config = config
        self.allowed_domains = config.normalized_domains()
        self._resolver = resolver or self._default_resolver
        self._robots_loader = robots_loader or self._default_robots_loader
        self._robots: dict[str, RobotFileParser | None] = {}

    @staticmethod
    def _default_resolver(hostname: str) -> Iterable[str]:
        return sorted({row[4][0] for row in socket.getaddrinfo(hostname, None)})

    def _default_robots_loader(self, robots_url: str) -> str | None:
        request = Request(robots_url, headers={"User-Agent": self.config.user_agent, "Accept": "text/plain,*/*;q=0.1"})
        try:
            opener = build_opener(SafeRedirectHandler(lambda target: self.decide(target, check_robots=False).allowed))
            with opener.open(request, timeout=self.config.timeout_seconds) as response:
                payload = response.read(1_000_000)
                return payload.decode("utf-8", errors="replace")
        except (OSError, ValueError):
            return None

    def _domain_allowed(self, host: str) -> bool:
        for domain in self.allowed_domains:
            if host == domain:
                return True
            if self.config.include_subdomains and host.endswith("." + domain):
                return True
        return False

    def _public_addresses_only(self, host: str) -> bool:
        try:
            addresses = list(self._resolver(host))
        except OSError:
            return False
        if not addresses:
            return False
        for raw in addresses:
            address = ipaddress.ip_address(raw)
            if not address.is_global:
                return False
        return True

    def _robots_for(self, url: str) -> RobotFileParser | None:
        split = urlsplit(url)
        origin = f"{split.scheme}://{split.netloc}"
        if origin in self._robots:
            return self._robots[origin]
        robots_url = origin + "/robots.txt"
        payload = self._robots_loader(robots_url)
        if payload is None:
            self._robots[origin] = None
            return None
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(payload.splitlines())
        self._robots[origin] = parser
        return parser

    def decide(self, url: str, *, check_robots: bool = True) -> PolicyDecision:
        checked_at = utc_now()
        try:
            normalized = canonicalize_url(url)
        except (ValueError, UnicodeError) as exc:
            return PolicyDecision(url, False, "INVALID_URL", str(exc), checked_at)

        split = urlsplit(normalized)
        host = split.hostname or ""
        if split.scheme not in {"http", "https"}:
            return PolicyDecision(normalized, False, "SCHEME_DENIED", "Seuls HTTP et HTTPS sont autorisés.", checked_at)
        if split.username or split.password:
            return PolicyDecision(normalized, False, "CREDENTIALS_DENIED", "Les identifiants intégrés à l'URL sont interdits.", checked_at)
        if not self._domain_allowed(host):
            return PolicyDecision(normalized, False, "OUT_OF_SCOPE", "Domaine hors de la portée autorisée.", checked_at)
        if self.config.block_private_networks and not self._public_addresses_only(host):
            return PolicyDecision(normalized, False, "NON_PUBLIC_NETWORK", "Adresse privée, locale, réservée ou non résolue.", checked_at)
        if check_robots:
            robots = self._robots_for(normalized)
            if robots is not None and not robots.can_fetch(self.config.user_agent, normalized):
                return PolicyDecision(normalized, False, "ROBOTS_DENIED", "Accès refusé par robots.txt.", checked_at)
        return PolicyDecision(normalized, True, "ALLOW", "Portée, réseau et robots acceptés.", checked_at)


class PoliteHTTPFetcher:
    def __init__(
        self,
        config: CrawlConfig,
        *,
        redirect_validator: Callable[[str], bool] | None = None,
    ) -> None:
        self.config = config
        self._last_request: dict[str, float] = {}
        validator = redirect_validator or (lambda _: True)
        self._opener = build_opener(SafeRedirectHandler(validator))

    def _throttle(self, host: str) -> None:
        previous = self._last_request.get(host)
        if previous is not None:
            remaining = self.config.delay_seconds - (time.monotonic() - previous)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request[host] = time.monotonic()

    def fetch(self, url: str, *, headers: Mapping[str, str] | None = None) -> FetchResponse:
        host = urlsplit(url).hostname or ""
        self._throttle(host)
        request_headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.5,*/*;q=0.1",
        }
        if headers:
            request_headers.update(headers)
        request = Request(url, headers=request_headers)
        with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
            body = response.read(self.config.max_response_bytes + 1)
            if len(body) > self.config.max_response_bytes:
                raise ValueError(f"Réponse supérieure à {self.config.max_response_bytes} octets")
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            return FetchResponse(
                requested_url=url,
                final_url=canonicalize_url(response.geturl()),
                status=int(getattr(response, "status", response.getcode())),
                headers=response_headers,
                body=body,
                fetched_at=utc_now(),
            )
