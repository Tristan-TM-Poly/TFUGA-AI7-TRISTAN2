from pathlib import Path
import re

PATTERNS={
 "approval_bypass":[r"\bwithout (?:asking|approval|confirmation)\b",r"\bskip (?:approval|confirmation)\b",r"\bsilently (?:merge|delete|publish|send|pay)\b"],
 "credential_request":[r"\b(password|private key|api key|token|session cookie)\b"],
 "destructive_action":[r"\b(delete|destroy|wipe|drop database|force push|merge everything)\b"],
 "exfiltration_language":[r"\b(send|upload|forward|exfiltrate)\b.{0,80}\b(secret|credential|private|sensitive)\b"],
 "epistemic_overclaim":[r"\bprove\b.{0,50}\bfrom (?:this )?(?:plot|graph|simulation)\b",r"\bguarantee(?:d)? true\b"]
}

def scan_skill_trust(skill_dir):
    skill_dir=Path(skill_dir); findings=[]
    for p in skill_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".md",".txt",".py",".json",".jsonl",".yaml",".yml",".toml"}: continue
        text=p.read_text(encoding="utf-8",errors="ignore")
        for cat,patterns in PATTERNS.items():
            for pattern in patterns:
                for m in re.finditer(pattern,text,re.I|re.S):
                    s=max(0,m.start()-80); e=min(len(text),m.end()+120)
                    findings.append({"category":cat,"file":str(p.relative_to(skill_dir)),
                                     "evidence":re.sub(r"\s+"," ",text[s:e]).strip()})
    high={"approval_bypass","exfiltration_language"}
    status="REVIEW" if any(x["category"] in high for x in findings) else ("PASS_WITH_FINDINGS" if findings else "PASS")
    return {"status":status,"finding_count":len(findings),"findings":findings,
            "note":"Heuristic static scan; not malware sandboxing or behavioral proof."}
