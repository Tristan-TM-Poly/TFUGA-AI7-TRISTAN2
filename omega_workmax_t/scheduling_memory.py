"""R0.7 append-only scheduling M⁺/M⁻ memory primitives."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json
from pathlib import Path
from typing import Iterable

@dataclass(frozen=True)
class SchedulingMemoryEvent:
    kind: str
    event_id: str
    policy_fingerprint: str
    context_fingerprint: str
    observation: str
    evidence_refs: tuple[str,...]=()
    metric_deltas: tuple[tuple[str,float],...]=()
    mitigation: str|None=None
    reproducible: bool=False

    def __post_init__(self):
        if self.kind not in {"M_PLUS","M_MINUS"}: raise ValueError("kind must be M_PLUS or M_MINUS")
        if not self.event_id: raise ValueError("event_id required")
        object.__setattr__(self,"evidence_refs",tuple(dict.fromkeys(self.evidence_refs)))
        object.__setattr__(self,"metric_deltas",tuple(sorted((str(k),float(v)) for k,v in self.metric_deltas)))

    @property
    def digest(self):
        return hashlib.sha256(json.dumps(asdict(self),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    def to_dict(self):
        d=asdict(self);d["metric_deltas"]=[list(x) for x in self.metric_deltas];d["digest"]=self.digest;return d

class SchedulingMemoryLedger:
    def __init__(self, events: Iterable[SchedulingMemoryEvent]=()):
        self._events=[]
        self._digests=set()
        for e in events:self.append(e)
    def append(self,event:SchedulingMemoryEvent)->bool:
        if event.digest in self._digests:return False
        self._digests.add(event.digest);self._events.append(event);return True
    @property
    def events(self):return tuple(self._events)
    def evidence_score(self, policy_fingerprint:str, context_fingerprint:str)->float:
        score=0.0
        for e in self._events:
            if e.policy_fingerprint!=policy_fingerprint or e.context_fingerprint!=context_fingerprint or not e.reproducible: continue
            score += 1.0 if e.kind=="M_PLUS" else -1.0
        return score
    def blocks_repeat(self, policy_fingerprint:str, context_fingerprint:str)->bool:
        negatives=sum(1 for e in self._events if e.kind=="M_MINUS" and e.policy_fingerprint==policy_fingerprint and e.context_fingerprint==context_fingerprint and e.reproducible)
        positives=sum(1 for e in self._events if e.kind=="M_PLUS" and e.policy_fingerprint==policy_fingerprint and e.context_fingerprint==context_fingerprint and e.reproducible)
        return negatives>positives
    def to_dict(self):
        payload={"schema":"omega-workmax-scheduling-memory/v1","events":[e.to_dict() for e in self._events]}
        canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False)
        payload["ledger_digest"]=hashlib.sha256(canonical.encode()).hexdigest()
        return payload
    def write_jsonl(self,path:str|Path)->None:
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text("".join(json.dumps(e.to_dict(),sort_keys=True,ensure_ascii=False)+"\n" for e in self._events),encoding="utf-8")
