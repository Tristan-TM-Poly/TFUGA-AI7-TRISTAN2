from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from .hashutil import sha256

@dataclass(frozen=True)
class NegativeMemory:
    memory_id: str
    context: str
    expected: str
    observed: str
    causes: tuple[str,...]
    anti_rules: tuple[str,...]
    severity: str
    created_at: str
    evidence_hash: str
    def to_dict(self): return asdict(self)

@dataclass
class NegativeMemoryRegistry:
    records: dict[str,NegativeMemory]=field(default_factory=dict)
    def record(self, *, context: str, expected: str, observed: str, causes: tuple[str,...], anti_rules: tuple[str,...], severity: str='medium') -> NegativeMemory:
        core={'context':context,'expected':expected,'observed':observed,'causes':causes,'anti_rules':anti_rules,'severity':severity,'created_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
        item=NegativeMemory('mminus:'+sha256(core)[:16],**core,evidence_hash=sha256(core))
        self.records[item.memory_id]=item; return item
    def applicable(self, text: str) -> tuple[NegativeMemory,...]:
        terms=set(text.casefold().split()); scored=[]
        for item in self.records.values():
            hay=set((item.context+' '+' '.join(item.causes)).casefold().split())
            scored.append((len(terms&hay),item.memory_id,item))
        return tuple(x[2] for x in sorted(scored,reverse=True) if x[0]>0)
    def to_dict(self): return {'count':len(self.records),'records':[self.records[k].to_dict() for k in sorted(self.records)]}
