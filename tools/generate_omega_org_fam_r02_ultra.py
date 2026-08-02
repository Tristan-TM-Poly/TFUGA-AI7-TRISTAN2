#!/usr/bin/env python3
"""Materialize and audit Ω-ORG-FAM-T R0.2 Ultra packed atlas."""
from __future__ import annotations
import argparse, json, shutil, sys, traceback
from pathlib import Path

# Direct script execution puts tools/ rather than the repository root on
# sys.path. Bootstrap the root explicitly so CI and local module execution are
# equivalent without requiring an editable install.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from omega_org_fam_t.packed_atlas import audit_packed_atlas, generate_packed_atlas


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",default=".")
    parser.add_argument("--family-records",type=int,default=16_777_216)
    parser.add_argument("--shard-families",type=int,default=1_048_576)
    parser.add_argument("--start-index",type=int,default=0)
    parser.add_argument("--clean",action="store_true")
    args=parser.parse_args()
    output=Path(args.root).resolve()/"generated"/"omega_org_fam_t_r02_ultra"
    if args.clean and output.exists(): shutil.rmtree(output)
    try:
        manifest=generate_packed_atlas(output,family_records=args.family_records,shard_families=args.shard_families,start_index=args.start_index)
        audit=audit_packed_atlas(output)
        (output/"oak-report.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
        if not audit["valid"]: raise RuntimeError(audit)
        print(json.dumps({"manifest":manifest,"audit":audit},indent=2,ensure_ascii=False))
        return 0
    except Exception as exc:
        output.mkdir(parents=True,exist_ok=True)
        with (output/"m_minus.jsonl").open("a",encoding="utf-8") as handle:
            handle.write(json.dumps({"event":"materialization_failure","error_type":type(exc).__name__,"error":str(exc),"family_records":args.family_records,"shard_families":args.shard_families,"next_action":"reduce shard size or resume from checkpoint; do not install a permanent total ceiling"})+"\n")
        traceback.print_exc()
        return 1
if __name__=="__main__": raise SystemExit(main())
