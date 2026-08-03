from __future__ import annotations
from dataclasses import asdict, dataclass, field
from .hashutil import sha256

@dataclass(frozen=True)
class PublicSource:
    source_id: str
    publisher: str
    title: str
    canonical_ref: str
    licence: str
    update_cadence: str
    data_class: str
    access_method: str
    permitted_uses: tuple[str,...]
    prohibited_uses: tuple[str,...]
    status: str='registered_not_ingested'
    def to_dict(self): return asdict(self)

@dataclass
class SourceRegistry:
    records: dict[str,PublicSource]=field(default_factory=dict)
    def register(self, source: PublicSource) -> None:
        if source.source_id in self.records and self.records[source.source_id]!=source: raise ValueError('conflicting source id')
        if not source.canonical_ref.startswith(('https://','file:','fixture:')): raise ValueError('canonical_ref must be explicit')
        self.records[source.source_id]=source
    def manifest(self) -> dict:
        payload={'sources':[self.records[k].to_dict() for k in sorted(self.records)]}
        payload['source_count']=len(self.records); payload['manifest_hash']=sha256(payload); return payload

def fixture_registry() -> SourceRegistry:
    r=SourceRegistry()
    r.register(PublicSource('synthetic-quebec-r01','Tristan research fixture','Synthetic Québec regional energy model','fixture:omega_hqt_t.synthetic_quebec','repository-defined synthetic contract','versioned with code','synthetic','local generator',('testing','education','benchmarking'),('claiming real topology','operational control')))
    r.register(PublicSource('public-org-capabilities-r01','Tristan research fixture','Public utility capability ontology','fixture:omega_hqt_t.organization','repository-defined synthetic contract','versioned with code','synthetic','local generator',('organizational modelling','research planning'),('claiming internal org chart',)))
    return r
