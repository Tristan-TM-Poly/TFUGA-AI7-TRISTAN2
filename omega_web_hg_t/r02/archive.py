from __future__ import annotations

import base64
from hashlib import sha256
from http.client import responses
import json
from pathlib import Path
from typing import Mapping
from uuid import uuid4

from omega_web_hg_t.models import FetchResponse, utc_now

CRLF = b"\r\n"


def _warc_digest(payload: bytes) -> str:
    encoded = base64.b32encode(sha256(payload).digest()).decode("ascii").rstrip("=")
    return f"sha256:{encoded}"


class WARCWriter:
    """Small append-only WARC/1.1 response + metadata writer.

    It emits standards-shaped records using only the Python standard library.
    Full replay interoperability remains an audited integration target rather than
    an implicit claim.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _append_record(
        self,
        *,
        warc_type: str,
        target_uri: str,
        content_type: str,
        payload: bytes,
        warc_date: str | None = None,
        record_id: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> str:
        identifier = record_id or f"<urn:uuid:{uuid4()}>"
        headers = {
            "WARC-Type": warc_type,
            "WARC-Target-URI": target_uri,
            "WARC-Date": warc_date or utc_now(),
            "WARC-Record-ID": identifier,
            "WARC-Block-Digest": _warc_digest(payload),
            "Content-Type": content_type,
            "Content-Length": str(len(payload)),
        }
        if extra_headers:
            headers.update(extra_headers)
        block = bytearray(b"WARC/1.1\r\n")
        for key, value in headers.items():
            block.extend(f"{key}: {value}\r\n".encode("utf-8"))
        block.extend(CRLF)
        block.extend(payload)
        block.extend(CRLF + CRLF)
        with self.path.open("ab") as handle:
            handle.write(block)
        return identifier

    def write_response(self, response: FetchResponse) -> str:
        reason = responses.get(response.status, "")
        http_payload = bytearray(f"HTTP/1.1 {response.status} {reason}\r\n".encode("ascii", errors="replace"))
        for key, value in sorted(response.headers.items()):
            http_payload.extend(f"{key}: {value}\r\n".encode("utf-8"))
        http_payload.extend(CRLF)
        http_payload.extend(response.body)
        return self._append_record(
            warc_type="response",
            target_uri=response.final_url,
            content_type="application/http; msgtype=response",
            payload=bytes(http_payload),
            warc_date=response.fetched_at,
            extra_headers={"WARC-Payload-Digest": _warc_digest(response.body)},
        )

    def write_metadata(self, target_uri: str, metadata: Mapping[str, object]) -> str:
        payload = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return self._append_record(
            warc_type="metadata",
            target_uri=target_uri,
            content_type="application/json",
            payload=payload,
        )
