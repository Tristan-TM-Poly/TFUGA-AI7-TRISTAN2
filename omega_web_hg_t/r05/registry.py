"""SQLite/WAL registry for policy profiles, compilations and gate decisions."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Iterable

from .models import CompiledPolicy, GateDecision, PolicyProfile, StorageDecisionRecord, canonical_json


class PolicyRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                digest TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS profiles_source_idx ON profiles(source_id, observed_at);

            CREATE TABLE IF NOT EXISTS compiled_policies (
                digest TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                evaluated_as_of TEXT NOT NULL,
                review_status TEXT NOT NULL,
                source_profile_digest TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS compiled_source_idx
                ON compiled_policies(source_id, evaluated_as_of);

            CREATE TABLE IF NOT EXISTS gate_decisions (
                digest TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                action TEXT NOT NULL,
                allowed INTEGER NOT NULL,
                policy_digest TEXT NOT NULL,
                decided_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS decisions_source_idx
                ON gate_decisions(source_id, decided_at);

            CREATE TABLE IF NOT EXISTS storage_decisions (
                digest TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                object_id TEXT NOT NULL,
                storage_level INTEGER NOT NULL,
                allowed INTEGER NOT NULL,
                policy_digest TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS storage_source_idx
                ON storage_decisions(source_id, object_id);
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "PolicyRegistry":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def record_profile(self, profile: PolicyProfile) -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO profiles(digest, source_id, observed_at, payload) VALUES (?, ?, ?, ?)",
            (profile.digest, profile.source_id, profile.policy_observed_at, canonical_json(profile.to_dict())),
        )
        self.connection.commit()
        return bool(cursor.rowcount)

    def record_compiled(self, policy: CompiledPolicy) -> bool:
        cursor = self.connection.execute(
            """INSERT OR IGNORE INTO compiled_policies(
                   digest, source_id, evaluated_as_of, review_status,
                   source_profile_digest, payload
               ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                policy.policy_digest,
                policy.source_id,
                policy.evaluated_as_of,
                policy.review_status,
                policy.source_profile_digest,
                canonical_json(policy.to_dict()),
            ),
        )
        self.connection.commit()
        return bool(cursor.rowcount)

    def record_decision(self, decision: GateDecision) -> bool:
        cursor = self.connection.execute(
            """INSERT OR IGNORE INTO gate_decisions(
                   digest, source_id, action, allowed, policy_digest, decided_at, payload
               ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                decision.decision_digest,
                decision.source_id,
                decision.action,
                int(decision.allowed),
                decision.policy_digest,
                decision.decided_at,
                canonical_json(decision.to_dict()),
            ),
        )
        self.connection.commit()
        return bool(cursor.rowcount)

    def record_storage_decision(self, decision: StorageDecisionRecord) -> bool:
        cursor = self.connection.execute(
            """INSERT OR IGNORE INTO storage_decisions(
                   digest, source_id, object_id, storage_level, allowed, policy_digest, payload
               ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                decision.digest,
                decision.source_id,
                decision.object_id,
                decision.storage_level,
                int(decision.allowed),
                decision.policy_digest,
                canonical_json(decision.to_dict()),
            ),
        )
        self.connection.commit()
        return bool(cursor.rowcount)

    def latest_compiled(self, source_id: str) -> dict[str, object] | None:
        row = self.connection.execute(
            """SELECT payload FROM compiled_policies
               WHERE source_id = ?
               ORDER BY evaluated_as_of DESC, digest DESC LIMIT 1""",
            (source_id,),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def counts(self) -> dict[str, int]:
        return {
            table: int(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("profiles", "compiled_policies", "gate_decisions", "storage_decisions")
        }

    def denied_decisions(self, source_id: str | None = None) -> list[dict[str, object]]:
        if source_id is None:
            rows = self.connection.execute(
                "SELECT payload FROM gate_decisions WHERE allowed = 0 ORDER BY decided_at, digest"
            )
        else:
            rows = self.connection.execute(
                """SELECT payload FROM gate_decisions
                   WHERE allowed = 0 AND source_id = ? ORDER BY decided_at, digest""",
                (source_id,),
            )
        return [json.loads(row[0]) for row in rows]

    def export_jsonl(self, output_dir: str | Path) -> tuple[Path, ...]:
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        outputs: list[Path] = []
        for table in ("profiles", "compiled_policies", "gate_decisions", "storage_decisions"):
            path = root / f"{table}.jsonl"
            rows = self.connection.execute(f"SELECT payload FROM {table} ORDER BY digest")
            path.write_text(
                "".join(json.dumps(json.loads(payload), ensure_ascii=False, sort_keys=True) + "\n" for (payload,) in rows),
                encoding="utf-8",
            )
            outputs.append(path)
        manifest = root / "registry-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema": "omega-web-hg-policy-registry-manifest/1.0",
                    "counts": self.counts(),
                    "raw_policy_documents_persisted": False,
                    "compiled_rules_are_legal_advice": False,
                    "denied_actions_preserved": True,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        outputs.append(manifest)
        return tuple(outputs)
