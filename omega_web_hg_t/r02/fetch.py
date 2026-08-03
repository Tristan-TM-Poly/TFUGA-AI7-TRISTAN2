from __future__ import annotations

import time
from typing import Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from omega_web_hg_t.models import FetchResponse, SafeRedirectHandler, canonicalize_url, utc_now
from .models import R02Config


class R02HTTPFetcher:
    def __init__(self, config: R02Config, *, redirect_validator: Callable[[str], bool]) -> None:
        self.config = config
        self._last_request: dict[str, float] = {}
        self._opener = build_opener(SafeRedirectHandler(redirect_validator))

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
            "Accept": "text/html,application/xhtml+xml,application/xml,application/rss+xml,application/atom+xml,application/json;q=0.9,text/plain;q=0.5,*/*;q=0.1",
            "Accept-Encoding": "identity",
        }
        if headers:
            request_headers.update(headers)
        request = Request(url, headers=request_headers)
        try:
            response = self._opener.open(request, timeout=self.config.timeout_seconds)
        except HTTPError as exc:
            if exc.code not in {304, 404, 410, 429, 500, 502, 503, 504}:
                raise
            response = exc
        with response:
            body = b"" if int(response.code) == 304 else response.read(self.config.max_response_bytes + 1)
            if len(body) > self.config.max_response_bytes:
                raise ValueError(f"Response exceeds {self.config.max_response_bytes} bytes")
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            return FetchResponse(
                requested_url=url,
                final_url=canonicalize_url(response.geturl()),
                status=int(response.code),
                headers=response_headers,
                body=body,
                fetched_at=utc_now(),
            )
