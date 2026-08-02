#!/usr/bin/env python3
"""Audit the checked-in Ω-PCT∞ R0.3 campaign atlas."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def audit(root: Path) -> dict:
    base=root/'data/omega_pct_r03_campaign'
    manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    seen=set(); total=0; failures=[]
    for shard in manifest['shards']:
        path=root/shard['path']; raw=path.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest != shard['sha256']: failures.append(f"hash:{shard['path']}")
        lines=raw.decode('utf-8').splitlines()
        if len(lines) != shard['records']: failures.append(f"count:{shard['path']}")
        for line in lines:
            row=json.loads(line); identifier=row['i']
            if identifier in seen: failures.append(f"duplicate:{identifier}")
            seen.add(identifier)
            if row['ap'] is not False or row['fr'] is not True: failures.append(f"authority:{identifier}")
        total += len(lines)
    if total != manifest['records']: failures.append('total')
    return {'passed':not failures,'records':total,'unique':len(seen),'failures':failures,'permanent_total_ceiling':manifest['permanent_total_ceiling'],'automatic_scientific_promotion':manifest['automatic_scientific_promotion']}

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument('--root',default='.')
    report=audit(Path(parser.parse_args().root)); print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
