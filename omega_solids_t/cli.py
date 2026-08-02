from __future__ import annotations
import argparse,json,sys
from dataclasses import asdict
from pathlib import Path
from .atlas import manifest as atlas_manifest,search as atlas_search
from .campaign import default_campaign_spec
from .hypergraph import from_candidate
from .materialize import materialize
from .oak import evaluate_candidate
from .storage import AtomicJSONLShardWriter,atomic_write_json
from .vocabularies import validate_vocabularies
def parser():
    p=argparse.ArgumentParser(prog='omega-solids',description='Ω-SOLID-T∞ R0.2 Solid Universe Compiler'); sub=p.add_subparsers(dest='command',required=True); sub.add_parser('vocab'); sub.add_parser('manifest'); dec=sub.add_parser('decode'); dec.add_argument('index',type=int); dec.add_argument('--environment',type=int,default=0); plan=sub.add_parser('plan'); plan.add_argument('--target-records-per-partition',type=int,default=8192); plan.add_argument('--output'); emit=sub.add_parser('emit'); emit.add_argument('--start',type=int,default=0); emit.add_argument('--stop',type=int,required=True); emit.add_argument('--environment',type=int,default=0); emit.add_argument('--records-per-shard',type=int,default=4096); emit.add_argument('--output-dir',required=True); oak=sub.add_parser('oak'); oak.add_argument('index',type=int); oak.add_argument('--environment',type=int,default=0); graph=sub.add_parser('graph'); graph.add_argument('index',type=int); graph.add_argument('--environment',type=int,default=0); graph.add_argument('--output-dir',required=True); mat=sub.add_parser('materialize'); mat.add_argument('--output-dir',default='generated/omega_solids_t_r02'); mat.add_argument('--records-per-shard',type=int,default=1024); stats=sub.add_parser('materialized-stats'); stats.add_argument('--root',default='generated/omega_solids_t_r02'); search=sub.add_parser('search'); search.add_argument('query'); search.add_argument('--root',default='generated/omega_solids_t_r02'); search.add_argument('--limit',type=int,default=20); return p
def main(argv=None):
    args=parser().parse_args(argv); spec=default_campaign_spec()
    try:
        if args.command=='vocab': payload=validate_vocabularies()
        elif args.command=='manifest': payload={'campaign_id':spec.campaign_id,'fingerprint':spec.fingerprint,'base_cardinality':spec.base_cardinality,'contextual_cardinality':spec.contextual_cardinality,'no_permanent_cap':True}
        elif args.command=='decode':
            candidate=spec.candidate_at(args.index,args.environment); payload={**asdict(candidate),'fingerprint':candidate.fingerprint}
        elif args.command=='plan':
            payload=spec.plan(args.target_records_per_partition)
            if args.output: atomic_write_json(args.output,payload)
        elif args.command=='emit':
            if args.stop<=args.start: raise ValueError('--stop must exceed --start')
            payload=AtomicJSONLShardWriter(args.output_dir,records_per_shard=args.records_per_shard,prefix='candidates').write(spec.iter_candidates(args.start,args.stop,args.environment))
        elif args.command=='oak': payload=asdict(evaluate_candidate(spec.candidate_at(args.index,args.environment)))
        elif args.command=='graph':
            graph=from_candidate(spec.candidate_at(args.index,args.environment)); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True); atomic_write_json(out/'hypergraph.json',graph.to_dict()); (out/'hypergraph.graphml').write_text(graph.to_graphml(),encoding='utf-8'); payload=graph.validate()
        elif args.command=='materialize': payload=materialize(args.output_dir,args.records_per_shard)
        elif args.command=='materialized-stats': payload=atlas_manifest(args.root)
        elif args.command=='search': payload=atlas_search(args.query,args.root,args.limit)
        else: raise AssertionError(args.command)
        print(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True,default=str)); return 0
    except (ValueError,IndexError,KeyError,OSError) as exc:
        print(f'omega-solids: {exc}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
