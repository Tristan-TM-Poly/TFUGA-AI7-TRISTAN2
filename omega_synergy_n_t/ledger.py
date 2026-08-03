"""Append-only proof ledger with hash-chain integrity (integrity is not truth)."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, json
from .models import Serializable


def _digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class LedgerEntry(Serializable):
    sequence: int
    record_type: str
    payload: dict
    previous_hash: str
    entry_hash: str

class ProofLedger:
    def __init__(self,path: str|Path): self.path=Path(path)
    def entries(self) -> list[LedgerEntry]:
        if not self.path.exists(): return []
        return [LedgerEntry(**json.loads(line)) for line in self.path.read_text().splitlines() if line.strip()]
    def append(self,record_type: str,payload: dict) -> LedgerEntry:
        entries=self.entries(); previous=entries[-1].entry_hash if entries else "GENESIS"
        base={"sequence":len(entries),"record_type":record_type,"payload":payload,"previous_hash":previous}
        entry=LedgerEntry(**base,entry_hash=_digest(base))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open("a",encoding="utf-8") as handle: handle.write(json.dumps(entry.to_dict(),sort_keys=True,ensure_ascii=False)+"\n")
        return entry
    def verify(self) -> tuple[bool,list[str]]:
        previous="GENESIS"; errors=[]
        for index,entry in enumerate(self.entries()):
            base={"sequence":entry.sequence,"record_type":entry.record_type,"payload":entry.payload,"previous_hash":entry.previous_hash}
            if entry.sequence!=index: errors.append(f"sequence mismatch at {index}")
            if entry.previous_hash!=previous: errors.append(f"chain mismatch at {index}")
            if entry.entry_hash!=_digest(base): errors.append(f"hash mismatch at {index}")
            previous=entry.entry_hash
        return not errors,errors
