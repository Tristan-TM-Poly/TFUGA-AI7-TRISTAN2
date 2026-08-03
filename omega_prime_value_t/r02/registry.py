from __future__ import annotations

import hashlib
from typing import Any

from .storage import CampaignStore


def prime_fingerprint(value: int) -> str:
    return hashlib.sha256(f"public-prime:{value}".encode("ascii")).hexdigest()


class LocalPrimeRegistry:
    """Local anti-duplication registry; never substitutes for external novelty research."""

    def __init__(self, store: CampaignStore):
        self.store = store

    def register(self, campaign_id: str, certificate: dict[str, Any]) -> bool:
        value = int(certificate["candidate"]["value"])
        fingerprint = prime_fingerprint(value)
        with self.store.connection:
            cursor = self.store.connection.execute(
                """
                INSERT OR IGNORE INTO registry(
                    fingerprint,value,certificate_id,certificate_sha256,first_campaign_id
                ) VALUES(?,?,?,?,?)
                """,
                (
                    fingerprint,
                    str(value),
                    certificate["certificate_id"],
                    certificate["sha256"],
                    campaign_id,
                ),
            )
        return cursor.rowcount == 1

    def contains(self, value: int) -> bool:
        row = self.store.connection.execute(
            "SELECT 1 FROM registry WHERE fingerprint=?", (prime_fingerprint(value),)
        ).fetchone()
        return row is not None

    def count(self) -> int:
        return int(self.store.connection.execute("SELECT COUNT(*) FROM registry").fetchone()[0])

    def export(self) -> list[dict[str, str]]:
        rows = self.store.connection.execute(
            "SELECT * FROM registry ORDER BY value"
        ).fetchall()
        return [dict(row) for row in rows]
