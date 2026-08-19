from __future__ import annotations
import argparse, json
from pathlib import Path
from .master_doc_atlas import write_bundle

def main() -> int:
    p=argparse.ArgumentParser(description="Ω-MASTER-DOC-ATLAS-T∞ multi-repository documentation atlas")
    p.add_argument("--registry", type=Path, default=Path("docs/generated/omega_master_doc_atlas/source-registry.json"))
    p.add_argument("--output-dir", type=Path, default=Path("generated/omega_master_doc_atlas"))
    a=p.parse_args()
    atlas=write_bundle(a.registry,a.output_dir)
    print(json.dumps({"atlas_version":atlas["atlas_version"],"repository_count":atlas["repository_count"],"atlas_fingerprint":atlas["atlas_fingerprint"],"output_dir":str(a.output_dir)},sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
