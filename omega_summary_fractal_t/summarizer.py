from __future__ import annotations

import hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path
from .audit import duplicate_candidates, gap_analysis, health_dashboard
from .graph import SummaryHypergraph
from .models import SummaryBundle
from .scanner import RepositoryScanner

DEPTH_KIND = {0:{"repository"},1:{"repository","system"},2:{"repository","system","document"},3:{"repository","system","document","workflow","schema"},4:{"repository","system","document","workflow","schema","code","test"},5:{"repository","system","document","workflow","schema","code","test","data","binary","other"},6:{"repository","system","document","workflow","schema","code","test","data","binary","other","class","function"},7:None,8:None,9:None}
AUDIENCES = {"tristan","developer","scientist","investor","client","ip","contributor","oak"}


def deterministic_timestamp() -> str:
    epoch = os.getenv("SOURCE_DATE_EPOCH"); dt = datetime.fromtimestamp(int(epoch), tz=timezone.utc) if epoch else datetime.now(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def bundle_fingerprint(file_hashes: dict[str,str], depth:int, audience:str, focus:str|None) -> str:
    payload = json.dumps({"files":file_hashes,"depth":depth,"audience":audience,"focus":focus}, sort_keys=True, separators=(",", ":")).encode(); return hashlib.sha256(payload).hexdigest()


class SummaryEngine:
    def __init__(self, root: str|Path, *, max_files:int=20000) -> None: self.root=Path(root).resolve(); self.max_files=max_files
    def generate(self, *, depth:int=3, audience:str="tristan", focus:str|None=None) -> SummaryBundle:
        if not 0 <= depth <= 9: raise ValueError("depth must be between 0 and 9")
        if audience not in AUDIENCES: raise ValueError(f"audience must be one of {sorted(AUDIENCES)}")
        scan = RepositoryScanner(self.root, max_files=self.max_files).scan(include_symbols=depth>=6); graph=SummaryHypergraph(scan.nodes,scan.edges)
        selected=graph.focus(focus)
        if focus and not selected: selected=[n for n in scan.nodes if n.kind=="repository"]
        allowed=DEPTH_KIND[depth]
        if allowed is not None: selected=[n for n in selected if n.kind in allowed]
        ids={n.id for n in selected}; edges=[e for e in scan.edges if e.source in ids and e.target in ids]
        selected=sorted(selected,key=lambda n:(self._rank(n.kind),n.path,n.id)); edges=sorted(edges,key=lambda e:(e.source,e.relation,e.target))
        return SummaryBundle("1.0.0", deterministic_timestamp(), self.root.name, depth, audience, focus, selected, edges, health_dashboard(scan.nodes), gap_analysis(scan.nodes) if depth>=3 else [], duplicate_candidates(scan.nodes) if depth>=4 else [], bundle_fingerprint(scan.file_hashes,depth,audience,focus))
    @staticmethod
    def _rank(kind:str)->int: return {"repository":0,"system":1,"document":2,"workflow":3,"schema":4,"code":5,"test":6,"class":7,"function":8}.get(kind,9)


def build_summary(root: str|Path, *, depth:int=3, audience:str="tristan", focus:str|None=None) -> SummaryBundle: return SummaryEngine(root).generate(depth=depth,audience=audience,focus=focus)
