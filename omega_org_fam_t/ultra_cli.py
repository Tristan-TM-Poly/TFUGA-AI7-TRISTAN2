from __future__ import annotations
import argparse, json
from pathlib import Path
from .codec import MixedRadixCodec
from .packed_atlas import audit_packed_atlas, generate_packed_atlas
from .registry import default_ultra_registry
from .spectral_grammar import evaluate_family


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(prog="omega-organic-family-ultra")
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("stats")
    dec=sub.add_parser("decode"); dec.add_argument("index",type=int)
    enc=sub.add_parser("encode"); enc.add_argument("coordinate_json")
    gen=sub.add_parser("generate"); gen.add_argument("output",type=Path); gen.add_argument("--family-records",type=int,default=16_777_216); gen.add_argument("--start-index",type=int,default=0); gen.add_argument("--shard-families",type=int,default=1_048_576)
    aud=sub.add_parser("audit"); aud.add_argument("output",type=Path)
    spec=sub.add_parser("spectral-evaluate"); spec.add_argument("family"); spec.add_argument("modality"); spec.add_argument("observed",nargs="+")
    args=parser.parse_args(argv); registry=default_ultra_registry(); codec=MixedRadixCodec(registry)
    if args.command=="stats": payload={"version":registry.version,"axes":len(registry.axes),"radices":registry.radices,"family_space":registry.family_space_size,"linked_object_space":registry.linked_object_space_size,"fingerprint":registry.fingerprint}
    elif args.command=="decode": payload={"index":args.index,"coordinate":codec.decode(args.index).coordinate}
    elif args.command=="encode": payload={"index":codec.encode(json.loads(args.coordinate_json))}
    elif args.command=="generate": payload=generate_packed_atlas(args.output,family_records=args.family_records,start_index=args.start_index,shard_families=args.shard_families)
    elif args.command=="audit": payload=audit_packed_atlas(args.output)
    else: payload=evaluate_family(args.family,args.modality,args.observed)
    print(json.dumps(payload,indent=2,ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())
