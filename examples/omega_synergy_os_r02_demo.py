"""Generate and verify the Ω-SYNERGY-OS R0.2 deterministic demo bundle."""
from __future__ import annotations
import json
from pathlib import Path
from omega_synergy_t.r02 import SynergyOSKernel,demo_inputs,verify_bundle,write_bundle

def main()->int:
    output=Path("generated/omega_synergy_os_r02/example")
    result=SynergyOSKernel().compile(demo_inputs(),available_evidence=["PR-234","PR-243","PR-259","PR-292","PR-318","PR-332","PR-338","PR-346","PR-347"])
    written=write_bundle(result,output);verification=verify_bundle(output)
    print(json.dumps({"bundle_id":written.manifest.bundle_id,"ir_digest":written.manifest.ir_digest,"selected":result.bundle.portfolio.selected_ids,"verification":verification,"human_review_required":True,"automatic_merge_allowed":False},indent=2,ensure_ascii=False,sort_keys=True))
    return 0 if verification["valid"] else 1
if __name__=="__main__":raise SystemExit(main())
