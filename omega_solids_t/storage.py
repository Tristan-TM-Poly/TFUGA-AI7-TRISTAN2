from __future__ import annotations
from dataclasses import asdict,is_dataclass
from pathlib import Path
from typing import Iterable,Iterator,Any
import hashlib,json,os,tempfile
class AtomicJSONLShardWriter:
    def __init__(self,output_dir,*,records_per_shard=4096,prefix='records'):
        if records_per_shard<=0: raise ValueError('records_per_shard must be positive')
        self.output_dir=Path(output_dir); self.output_dir.mkdir(parents=True,exist_ok=True); self.records_per_shard=records_per_shard; self.prefix=prefix
    def write(self,records:Iterable[Any],*,start_shard=0):
        shard_index=start_shard; count=0; manifests=[]; buffer=[]
        def flush(items,index):
            path=self.output_dir/f'{self.prefix}_{index:05d}.jsonl'; hasher=hashlib.sha256()
            with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=self.output_dir,delete=False) as handle:
                tmp=Path(handle.name)
                for record in items:
                    obj=asdict(record) if is_dataclass(record) else record; line=json.dumps(obj,ensure_ascii=False,sort_keys=True,default=str,separators=(',',':'))+'\n'; handle.write(line); hasher.update(line.encode())
                handle.flush(); os.fsync(handle.fileno())
            tmp.replace(path); return {'path':path.name,'records':len(items),'sha256':hasher.hexdigest(),'bytes':path.stat().st_size}
        for record in records:
            buffer.append(record); count+=1
            if len(buffer)>=self.records_per_shard: manifests.append(flush(buffer,shard_index)); buffer=[]; shard_index+=1
        if buffer: manifests.append(flush(buffer,shard_index))
        manifest={'records':count,'records_per_shard':self.records_per_shard,'shards':manifests}; atomic_write_json(self.output_dir/f'{self.prefix}_manifest.json',manifest); return manifest
def atomic_write_json(path,payload):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as handle:
        tmp=Path(handle.name); json.dump(payload,handle,ensure_ascii=False,sort_keys=True,indent=2,default=str); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    tmp.replace(path)
def iter_jsonl(paths:Iterable[str|Path])->Iterator[dict]:
    for path in paths:
        with Path(path).open(encoding='utf-8') as handle:
            for line_no,line in enumerate(handle,1):
                if line.strip():
                    try: yield json.loads(line)
                    except json.JSONDecodeError as exc: raise ValueError(f'{path}:{line_no}: {exc}') from exc
def verify_manifest(directory,manifest_name):
    directory=Path(directory); manifest=json.loads((directory/manifest_name).read_text(encoding='utf-8')); errors=[]; total=0
    for shard in manifest['shards']:
        path=directory/shard['path']
        if not path.exists(): errors.append(f'missing:{path.name}'); continue
        if hashlib.sha256(path.read_bytes()).hexdigest()!=shard['sha256']: errors.append(f'digest:{path.name}')
        lines=sum(1 for _ in path.open(encoding='utf-8')); total+=lines
        if lines!=shard['records']: errors.append(f'count:{path.name}')
    return {'valid':not errors,'errors':errors,'records':total,'expected':manifest['records']}
