"""Deterministic artifact bundles and tamper detection for Ω-SYNERGY-OS R0.2."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from pathlib import Path
from typing import Any,Sequence
from .contracts import ArtifactReceipt,BundleManifest,canonical_json,stable_id
from .kernel import CompileResult

def _json_text(payload):return json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+"\n"
def _sha(data):return hashlib.sha256(data).hexdigest()
def _merkle_root(digests:Sequence[str]):
    level=[bytes.fromhex(item) for item in sorted(digests)]
    if not level:return hashlib.sha256(b"").hexdigest()
    while len(level)>1:
        if len(level)%2:level.append(level[-1])
        level=[hashlib.sha256(level[i]+level[i+1]).digest() for i in range(0,len(level),2)]
    return level[0].hex()
def _report_markdown(result):
    bundle=result.bundle;decisions={i.constellation_id:i for i in bundle.gate_decisions};selected=set(bundle.portfolio.selected_ids)
    lines=["# Ω-SYNERGY-OS-T∞ R0.2 MAX","","**Authority:** A3 review candidate only. No merge, publication, release, spending, outreach, IP filing or scientific certification.","","```text","intent -> Transformation IR -> typed bridges -> hard OAK gates -> diversified portfolio -> bounded experiment -> evidence -> human review","```","",f"- IR digest: `{bundle.ir.content_digest}`",f"- Nodes: **{len(bundle.ir.nodes)}**",f"- Edges: **{len(bundle.ir.edges)}**",f"- Bridge candidates: **{len(result.bridge_candidates)}**",f"- Constellations: **{len(bundle.constellations)}**",f"- Selected: **{len(bundle.portfolio.selected_ids)}**",f"- M− residuals: **{len(bundle.m_minus)}**","","| Selected | Utility | Gate | Constellation | Systems |","|---|---:|---|---|---|"]
    for item in sorted(bundle.constellations,key=lambda x:(-x.heuristic_utility,x.id)):lines.append(f"| {'yes' if item.id in selected else 'no'} | {item.heuristic_utility:.3f} | {decisions[item.id].status.value} | {item.name} | {' × '.join(item.systems)} |")
    lines.extend(["","## Hard boundaries","","- A score is not a truth probability.","- Passing gates is not irreversible authority.","- Bridges remain hypotheses until tested against the simplest baseline.","- Evidence hashes prove identity, not scientific truth.","- Recursive generation remains bounded by portfolio, proof, stop, budget and rollback governors.","","## M−",""])
    for residual in sorted(bundle.m_minus,key=lambda x:(x.severity,x.code,x.id)):lines.append(f"- `{residual.severity}` **{residual.code}** — {residual.message}")
    return "\n".join(lines)+"\n"
ARTIFACT_BUILDERS={"transformation_ir.json":lambda r:r.bundle.ir.to_dict(),"adaptation_receipts.json":lambda r:[i.to_dict() for i in r.adaptation_receipts],"bridge_candidates.json":lambda r:[i.to_dict() for i in r.bridge_candidates],"top_constellations.json":lambda r:[i.to_dict() for i in r.bundle.constellations],"gate_decisions.json":lambda r:[i.to_dict() for i in r.bundle.gate_decisions],"portfolio.json":lambda r:r.bundle.portfolio.to_dict(),"graph_metrics.json":lambda r:r.graph_metrics,"synergy_os_bundle.json":lambda r:r.bundle.to_dict()}
@dataclass(slots=True)
class BundleWriteResult:
    output_dir:Path;manifest:BundleManifest
    def to_dict(self):return {"output_dir":str(self.output_dir),"manifest":self.manifest.to_dict()}
def write_bundle(result,output_dir):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);receipts=[]
    for filename,builder in sorted(ARTIFACT_BUILDERS.items()):
        data=_json_text(builder(result)).encode();(out/filename).write_bytes(data);receipts.append(ArtifactReceipt(filename,_sha(data),len(data),"json"))
    mminus="".join(canonical_json(i.to_dict())+"\n" for i in result.bundle.m_minus).encode();(out/"m_minus.jsonl").write_bytes(mminus);receipts.append(ArtifactReceipt("m_minus.jsonl",_sha(mminus),len(mminus),"jsonl"))
    report=_report_markdown(result).encode();(out/"REPORT.md").write_bytes(report);receipts.append(ArtifactReceipt("REPORT.md",_sha(report),len(report),"markdown"))
    merkle=_merkle_root([i.sha256 for i in receipts]);manifest=BundleManifest("2.0",stable_id("SYNERGY-BUNDLE",result.bundle.ir.content_digest,merkle,length=32),result.bundle.ir.generated_at,result.bundle.ir.content_digest,merkle,sorted(receipts,key=lambda i:i.path),limitations=["heuristic priorities are not truth probabilities","local software validation is not independent scientific validation","no merge, publication, release or external action authority","dynamic runtime dependencies may be incomplete"])
    (out/"manifest.json").write_text(_json_text(manifest.to_dict()),encoding="utf-8");return BundleWriteResult(out,manifest)
def verify_bundle(output_dir):
    out=Path(output_dir);manifest_path=out/"manifest.json"
    if not manifest_path.exists():return {"valid":False,"errors":["missing_manifest"],"checked":0}
    raw=json.loads(manifest_path.read_text());errors=[];observed=[];receipts=raw.get("receipts",[])
    for receipt in receipts:
        path=out/receipt["path"]
        if not path.exists():errors.append(f"missing_artifact:{receipt['path']}");continue
        data=path.read_bytes();value=_sha(data);observed.append(value)
        if value!=receipt["sha256"]:errors.append(f"digest_mismatch:{receipt['path']}")
        if len(data)!=receipt["size"]:errors.append(f"size_mismatch:{receipt['path']}")
    observed_merkle=_merkle_root(observed) if len(observed)==len(receipts) else ""
    if observed_merkle!=raw.get("merkle_root"):errors.append("merkle_root_mismatch")
    bundle_path=out/"synergy_os_bundle.json"
    if bundle_path.exists():
        bundle=json.loads(bundle_path.read_text())
        if bundle.get("automatic_merge_allowed") is not False:errors.append("automatic_merge_boundary_broken")
        if bundle.get("automatic_publication_allowed") is not False:errors.append("automatic_publication_boundary_broken")
        if bundle.get("human_review_required") is not True:errors.append("human_review_boundary_broken")
    return {"valid":not errors,"errors":sorted(set(errors)),"checked":len(receipts),"observed_merkle_root":observed_merkle,"expected_merkle_root":raw.get("merkle_root",""),"bundle_id":raw.get("bundle_id","")}
def compare_bundles(left_dir,right_dir):
    left=json.loads((Path(left_dir)/"manifest.json").read_text());right=json.loads((Path(right_dir)/"manifest.json").read_text());lr={i["path"]:i["sha256"] for i in left.get("receipts",[])};rr={i["path"]:i["sha256"] for i in right.get("receipts",[])};paths=sorted(set(lr)|set(rr))
    return {"same_ir":left.get("ir_digest")==right.get("ir_digest"),"same_merkle_root":left.get("merkle_root")==right.get("merkle_root"),"added":[p for p in paths if p not in lr],"removed":[p for p in paths if p not in rr],"changed":[p for p in paths if p in lr and p in rr and lr[p]!=rr[p]]}
