from __future__ import annotations

import base64
import copy
import hashlib
import json
import sqlite3
import subprocess
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..r03.canonical import canonical_json, sha256_hex
from ..r03.merkle import MerkleTree


@dataclass(frozen=True, slots=True)
class TransparencyEntry:
    sequence: int
    kind: str
    payload_hash: str
    previous_hash: str
    entry_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TransparencyCheckpoint:
    version: str
    tree_size: int
    merkle_root: str
    head_hash: str
    created_at_utc: str
    signature_algorithm: str | None
    signature_base64: str | None
    public_key_sha256: str | None
    oak: dict[str, Any]
    sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def signing_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "tree_size": self.tree_size,
            "merkle_root": self.merkle_root,
            "head_hash": self.head_hash,
            "created_at_utc": self.created_at_utc,
            "signature_algorithm": self.signature_algorithm,
            "public_key_sha256": self.public_key_sha256,
            "oak": self.oak,
        }


class TransparencyLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                sequence INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                entry_hash TEXT NOT NULL UNIQUE
            )
            """
        )
        self.connection.commit()

    def __enter__(self) -> "TransparencyLog":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def append(self, kind: str, payload: Any) -> TransparencyEntry:
        if not kind.strip():
            raise ValueError("kind is required")
        payload_json = canonical_json(payload)
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        row = self.connection.execute(
            "SELECT sequence, entry_hash FROM entries ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        sequence = 0 if row is None else int(row[0]) + 1
        previous_hash = "0" * 64 if row is None else str(row[1])
        entry_hash = sha256_hex(
            {
                "sequence": sequence,
                "kind": kind,
                "payload_hash": payload_hash,
                "previous_hash": previous_hash,
            }
        )
        self.connection.execute(
            "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?)",
            (sequence, kind, payload_json, payload_hash, previous_hash, entry_hash),
        )
        self.connection.commit()
        return TransparencyEntry(sequence, kind, payload_hash, previous_hash, entry_hash)

    def entries(self, *, limit: int | None = None) -> tuple[TransparencyEntry, ...]:
        sql = "SELECT sequence, kind, payload_hash, previous_hash, entry_hash FROM entries ORDER BY sequence"
        parameters: tuple[int, ...] = ()
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be nonnegative")
            sql += " LIMIT ?"
            parameters = (limit,)
        rows = self.connection.execute(sql, parameters).fetchall()
        return tuple(TransparencyEntry(int(a), str(b), str(c), str(d), str(e)) for a, b, c, d, e in rows)

    def verify_chain(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        rows = self.connection.execute(
            "SELECT sequence, kind, payload_json, payload_hash, previous_hash, entry_hash FROM entries ORDER BY sequence"
        ).fetchall()
        previous = "0" * 64
        for expected_sequence, row in enumerate(rows):
            sequence, kind, payload_json, payload_hash, previous_hash, entry_hash = row
            if int(sequence) != expected_sequence:
                errors.append(f"sequence discontinuity at {expected_sequence}")
            actual_payload_hash = hashlib.sha256(str(payload_json).encode("utf-8")).hexdigest()
            if actual_payload_hash != payload_hash:
                errors.append(f"payload hash mismatch at {sequence}")
            if previous_hash != previous:
                errors.append(f"previous hash mismatch at {sequence}")
            actual_entry_hash = sha256_hex(
                {
                    "sequence": int(sequence),
                    "kind": str(kind),
                    "payload_hash": str(payload_hash),
                    "previous_hash": str(previous_hash),
                }
            )
            if actual_entry_hash != entry_hash:
                errors.append(f"entry hash mismatch at {sequence}")
            previous = str(entry_hash)
        return not errors, errors

    def checkpoint(self, *, tree_size: int | None = None, created_at_utc: str) -> TransparencyCheckpoint:
        try:
            datetime.fromisoformat(created_at_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("created_at_utc must be an ISO-8601 timestamp") from exc
        all_entries = self.entries()
        size = len(all_entries) if tree_size is None else tree_size
        if size <= 0 or size > len(all_entries):
            raise ValueError("tree_size must select a non-empty prefix")
        prefix = all_entries[:size]
        leaves = [{"sequence": item.sequence, "entry_hash": item.entry_hash} for item in prefix]
        checkpoint = TransparencyCheckpoint(
            version="4.0",
            tree_size=size,
            merkle_root=MerkleTree(leaves).root,
            head_hash=prefix[-1].entry_hash,
            created_at_utc=created_at_utc,
            signature_algorithm=None,
            signature_base64=None,
            public_key_sha256=None,
            oak={
                "append_only_prefix_committed": True,
                "unsigned_checkpoint_is_not_authenticity_proof": True,
                "novelty_claimed": False,
            },
        )
        payload = checkpoint.to_dict()
        payload["sha256"] = ""
        return replace(checkpoint, sha256=sha256_hex(payload))


def _seal_checkpoint(checkpoint: TransparencyCheckpoint) -> TransparencyCheckpoint:
    payload = checkpoint.to_dict()
    payload["sha256"] = ""
    return replace(checkpoint, sha256=sha256_hex(payload))


def sign_checkpoint_openssl(
    checkpoint: TransparencyCheckpoint,
    *,
    private_key: str | Path,
    public_key: str | Path,
) -> TransparencyCheckpoint:
    private_path = Path(private_key).resolve()
    public_path = Path(public_key).resolve()
    if not private_path.is_file() or not public_path.is_file():
        raise ValueError("private_key and public_key must exist")
    signed_oak = {
        **checkpoint.oak,
        "unsigned_checkpoint_is_not_authenticity_proof": False,
        "private_key_custody_external_to_repository": True,
    }
    provisional = replace(
        checkpoint,
        signature_algorithm="Ed25519/OpenSSL",
        signature_base64=None,
        public_key_sha256=hashlib.sha256(public_path.read_bytes()).hexdigest(),
        oak=signed_oak,
        sha256="",
    )
    message = canonical_json(provisional.signing_payload()).encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="omega-prime-sign-") as directory:
        message_path = Path(directory) / "checkpoint.json"
        signature_path = Path(directory) / "checkpoint.sig"
        message_path.write_bytes(message)
        completed = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-sign",
                "-inkey",
                str(private_path),
                "-rawin",
                "-in",
                str(message_path),
                "-out",
                str(signature_path),
            ],
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
        signature = signature_path.read_bytes()
    signed = replace(
        provisional,
        signature_base64=base64.b64encode(signature).decode("ascii"),
    )
    return _seal_checkpoint(signed)


def verify_checkpoint(
    checkpoint: TransparencyCheckpoint | Mapping[str, Any],
    entries: Iterable[TransparencyEntry | Mapping[str, Any]],
    *,
    public_key: str | Path | None = None,
) -> tuple[bool, list[str]]:
    payload = checkpoint.to_dict() if isinstance(checkpoint, TransparencyCheckpoint) else copy.deepcopy(dict(checkpoint))
    errors: list[str] = []
    unsigned = copy.deepcopy(payload)
    expected_hash = str(unsigned.get("sha256", ""))
    unsigned["sha256"] = ""
    if sha256_hex(unsigned) != expected_hash:
        errors.append("checkpoint sha256 mismatch")
    items = [item.to_dict() if isinstance(item, TransparencyEntry) else dict(item) for item in entries]
    try:
        size = int(payload["tree_size"])
        prefix = items[:size]
        if size <= 0 or len(prefix) != size:
            errors.append("checkpoint prefix unavailable")
        else:
            leaves = [{"sequence": int(item["sequence"]), "entry_hash": str(item["entry_hash"])} for item in prefix]
            if MerkleTree(leaves).root != payload.get("merkle_root"):
                errors.append("checkpoint Merkle root mismatch")
            if str(prefix[-1]["entry_hash"]) != payload.get("head_hash"):
                errors.append("checkpoint head hash mismatch")
    except (KeyError, TypeError, ValueError):
        errors.append("malformed checkpoint")
    signature = payload.get("signature_base64")
    algorithm = payload.get("signature_algorithm")
    fingerprint = payload.get("public_key_sha256")
    if signature is None and (algorithm is not None or fingerprint is not None):
        errors.append("unsigned checkpoint contains signature metadata")
    if signature is not None:
        if algorithm != "Ed25519/OpenSSL":
            errors.append("unsupported checkpoint signature algorithm")
        elif public_key is None:
            errors.append("public key required for signed checkpoint")
        else:
            public_path = Path(public_key).resolve()
            if hashlib.sha256(public_path.read_bytes()).hexdigest() != payload.get("public_key_sha256"):
                errors.append("public key fingerprint mismatch")
            message_payload = {
                key: payload[key]
                for key in (
                    "version",
                    "tree_size",
                    "merkle_root",
                    "head_hash",
                    "created_at_utc",
                    "signature_algorithm",
                    "public_key_sha256",
                    "oak",
                )
            }
            with tempfile.TemporaryDirectory(prefix="omega-prime-verify-") as directory:
                message_path = Path(directory) / "checkpoint.json"
                signature_path = Path(directory) / "checkpoint.sig"
                message_path.write_text(canonical_json(message_payload), encoding="utf-8")
                try:
                    signature_path.write_bytes(base64.b64decode(str(signature), validate=True))
                except ValueError:
                    errors.append("invalid base64 signature")
                else:
                    completed = subprocess.run(
                        [
                            "openssl",
                            "pkeyutl",
                            "-verify",
                            "-pubin",
                            "-inkey",
                            str(public_path),
                            "-rawin",
                            "-in",
                            str(message_path),
                            "-sigfile",
                            str(signature_path),
                        ],
                        capture_output=True,
                        check=False,
                    )
                    if completed.returncode != 0:
                        errors.append("checkpoint signature verification failed")
    return not errors, errors
