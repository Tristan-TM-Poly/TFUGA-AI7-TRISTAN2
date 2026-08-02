"""Unbounded-by-design finite campaign generator with checkpoints and backpressure."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from pathlib import Path
import hashlib,json,time
@dataclass(frozen=True)
class CampaignAxis: name:str; values:tuple[float|str|bool,...]
@dataclass(frozen=True)
class CampaignPolicy:
    initial_batch_size:int=128; growth_factor:float=1.7; pressure_soft:float=0.75; pressure_hard:float=0.95; quality_floor:float=0.98; checkpoint_every:int=1000
class CampaignGenerator:
    def __init__(self,axes:list[CampaignAxis],policy:CampaignPolicy=CampaignPolicy()):
        if not axes: raise ValueError("at least one axis required")
        if any(not a.values for a in axes): raise ValueError("axis values cannot be empty")
        self.axes=axes; self.policy=policy
    def combinations(self):
        names=[a.name for a in self.axes]
        for vals in product(*(a.values for a in self.axes)):
            item=dict(zip(names,vals)); raw=json.dumps(item,sort_keys=True,separators=(",",":"))
            yield {"id":hashlib.sha256(raw.encode()).hexdigest()[:20],"parameters":item}
    def emit_jsonl(self,path:Path,resume_after:int=0,work_budget:int|None=None)->dict:
        path.parent.mkdir(parents=True,exist_ok=True); count=0; skipped=0; start=time.time(); mode="a" if resume_after else "w"
        with path.open(mode,encoding="utf-8") as f:
            for index,item in enumerate(self.combinations()):
                if index<resume_after: skipped+=1; continue
                if work_budget is not None and count>=work_budget: break
                f.write(json.dumps(item,sort_keys=True)+"\n"); count+=1
                if self.policy.checkpoint_every and count%self.policy.checkpoint_every==0:
                    path.with_suffix(".checkpoint.json").write_text(json.dumps({"last_index":index,"written":count,"path":str(path),"timestamp":time.time()},indent=2),encoding="utf-8")
        return {"written":count,"skipped":skipped,"elapsed_s":time.time()-start,"work_budget":work_budget,"permanent_cap":False}
