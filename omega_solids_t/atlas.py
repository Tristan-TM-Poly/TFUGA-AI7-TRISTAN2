from __future__ import annotations
from pathlib import Path
from typing import Iterator
import json
DEFAULT_ROOT=Path(__file__).resolve().parents[1]/'generated'/'omega_solids_t_r02'
def _iter_shards(folder:Path)->Iterator[dict]:
    for path in sorted(folder.glob('*.jsonl')):
        with path.open(encoding='utf-8') as handle:
            for line in handle:
                if line.strip(): yield json.loads(line)
def iter_hot_candidates(root:Path|str=DEFAULT_ROOT)->Iterator[dict]: return _iter_shards(Path(root)/'hot_atlas')
def iter_evidence_templates(root:Path|str=DEFAULT_ROOT)->Iterator[dict]: return _iter_shards(Path(root)/'evidence')
def iter_world_mechanisms(root:Path|str=DEFAULT_ROOT)->Iterator[dict]: return _iter_shards(Path(root)/'world_mechanisms')
def manifest(root:Path|str=DEFAULT_ROOT)->dict: return json.loads((Path(root)/'manifest.json').read_text(encoding='utf-8'))
def search(query:str,root:Path|str=DEFAULT_ROOT,limit:int=50)->list[dict]:
    q=query.casefold(); out=[]
    for source,iterator in (('candidate',iter_hot_candidates(root)),('evidence',iter_evidence_templates(root)),('mapping',iter_world_mechanisms(root))):
        for item in iterator:
            if q in json.dumps(item,ensure_ascii=False).casefold():
                out.append({'source':source,**item})
                if len(out)>=limit:return out
    return out
