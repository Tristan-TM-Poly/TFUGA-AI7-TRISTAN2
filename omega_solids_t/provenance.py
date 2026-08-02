from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Iterable
import hashlib,json,os,tempfile
from .models import EvidenceRef
class EvidenceLedger:
    def __init__(self): self._records={}
    def add(self,record:EvidenceRef):
        existing=self._records.get(record.evidence_id)
        if existing is not None and existing!=record: raise ValueError(f'conflicting evidence id: {record.evidence_id}')
        self._records[record.evidence_id]=record
    def get(self,evidence_id): return self._records[evidence_id]
    def coverage(self,evidence_ids:Iterable[str]):
        ids=tuple(evidence_ids); return 1.0 if not ids else sum(i in self._records for i in ids)/len(ids)
    def digest(self):
        payload=[asdict(self._records[k]) for k in sorted(self._records)]; return hashlib.sha256(json.dumps(payload,default=str,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def write_jsonl(self,path):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as handle:
            tmp=Path(handle.name)
            for key in sorted(self._records): handle.write(json.dumps(asdict(self._records[key]),default=str,ensure_ascii=False,sort_keys=True)+'\n')
            handle.flush(); os.fsync(handle.fileno())
        tmp.replace(path)
