from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import canonical_json, stable_digest


class ProofLedger:
    """Append-only JSONL ledger with a deterministic hash chain.

    This is an integrity chain, not a cryptographic identity signature.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _last(self) -> tuple[int, str]:
        if not self.path.exists():
            return (-1, "GENESIS")
        last: Mapping[str, Any] | None = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                last = json.loads(line)
        if last is None:
            return (-1, "GENESIS")
        return (int(last["sequence"]), str(last["entry_hash"]))

    def append(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        sequence, previous_hash = self._last()
        entry_core = {
            "sequence": sequence + 1,
            "previous_hash": previous_hash,
            "payload": dict(payload),
        }
        entry = {**entry_core, "entry_hash": stable_digest(entry_core)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(entry) + "\n")
        return entry

    def entries(self) -> tuple[Mapping[str, Any], ...]:
        if not self.path.exists():
            return ()
        return tuple(json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip())

    def verify(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []
        previous_hash = "GENESIS"
        for expected_sequence, entry in enumerate(self.entries()):
            if int(entry.get("sequence", -1)) != expected_sequence:
                errors.append(f"sequence mismatch at {expected_sequence}")
            if entry.get("previous_hash") != previous_hash:
                errors.append(f"previous hash mismatch at {expected_sequence}")
            core = {
                "sequence": entry.get("sequence"),
                "previous_hash": entry.get("previous_hash"),
                "payload": entry.get("payload"),
            }
            computed = stable_digest(core)
            if entry.get("entry_hash") != computed:
                errors.append(f"entry hash mismatch at {expected_sequence}")
            previous_hash = str(entry.get("entry_hash"))
        return (not errors, tuple(errors))
