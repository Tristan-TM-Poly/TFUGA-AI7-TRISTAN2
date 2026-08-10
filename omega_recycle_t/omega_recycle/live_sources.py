from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen

_ALLOWED_HOSTS=frozenset({"ec.europa.eu","www.epa.gov"})

@dataclass(frozen=True, slots=True)
class LiveSourceSpec:
    source_id:str
    url:str
    max_bytes:int=2_000_000
    def __post_init__(self):
        parsed=urlparse(self.url)
        if parsed.scheme!="https" or parsed.hostname not in _ALLOWED_HOSTS:
            raise ValueError("live source must be an allowlisted official HTTPS host")
        if self.max_bytes<=0: raise ValueError("max_bytes must be positive")

@dataclass(frozen=True, slots=True)
class LiveSnapshot:
    source_id:str
    url:str
    retrieved_at:str
    sha256:str
    byte_count:int
    content_type:str|None
    etag:str|None
    last_modified:str|None
    http_status:int
    claim_boundary:str="http_content_identity_only_not_source_truth_or_semantic_equivalence"

@dataclass(frozen=True, slots=True)
class LiveManifestDiff:
    added:tuple[str,...]
    removed:tuple[str,...]
    changed:tuple[str,...]
    unchanged:tuple[str,...]
    claim_boundary:str="content_hash_revision_signal_only_not_semantic_change_classification"

def fetch_live_snapshot(spec:LiveSourceSpec, *, retrieved_at:str, timeout:float=20.0, opener=urlopen)->tuple[bytes,LiveSnapshot]:
    req=Request(spec.url,headers={"User-Agent":"omega-recycle-t/0.6 evidence acquisition"})
    with opener(req,timeout=timeout) as response:
        status=int(getattr(response,"status",response.getcode()))
        if status!=200: raise RuntimeError(f"source returned HTTP {status}")
        data=response.read(spec.max_bytes+1)
        if len(data)>spec.max_bytes: raise ValueError("source response exceeds max_bytes")
        headers=response.headers
        snap=LiveSnapshot(
            spec.source_id,spec.url,retrieved_at,sha256(data).hexdigest(),len(data),
            headers.get("Content-Type"),headers.get("ETag"),headers.get("Last-Modified"),status,
        )
        return data,snap

def compare_live_snapshots(previous:tuple[LiveSnapshot,...], current:tuple[LiveSnapshot,...])->LiveManifestDiff:
    old={x.source_id:x for x in previous}; new={x.source_id:x for x in current}
    added=sorted(set(new)-set(old)); removed=sorted(set(old)-set(new))
    common=sorted(set(old)&set(new))
    changed=[k for k in common if old[k].sha256!=new[k].sha256]
    unchanged=[k for k in common if old[k].sha256==new[k].sha256]
    return LiveManifestDiff(tuple(added),tuple(removed),tuple(changed),tuple(unchanged))

def render_manifest(snapshots:tuple[LiveSnapshot,...])->str:
    return json.dumps({"schema":"omega-recycle-live-manifest-v1","snapshots":[asdict(s) for s in snapshots]},sort_keys=True,indent=2)

EUROSTAT_ENV_WASMUN_LIVE=LiveSourceSpec(
    "eurostat-env-wasmun-eu27-latest2",
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/env_wasmun?lang=EN&geo=EU27_2020&lastTimePeriod=2",
)
EPA_SMM_LANDING_LIVE=LiveSourceSpec(
    "epa-smm-facts-figures",
    "https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/advancing-sustainable-materials-management",
)
