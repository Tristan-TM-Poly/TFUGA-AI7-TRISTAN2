from pathlib import Path
import hashlib,re

def _fm(path):
    text=path.read_text(encoding="utf-8",errors="replace")
    if not text.startswith("---\n"): return {}
    end=text.find("\n---",4)
    if end<0: return {}
    d={}
    for line in text[4:end].splitlines():
        if ":" in line:
            k,v=line.split(":",1); d[k.strip()]=v.strip()
    return d

def _sig(text):
    return hashlib.sha256(re.sub(r"\s+"," ",text.lower()).strip().encode()).hexdigest()[:16]

def catalog_skills(root):
    root=Path(root); skills=[]
    for m in root.rglob("SKILL.md"):
        meta=_fm(m); text=m.read_text(encoding="utf-8",errors="replace")
        skills.append({"name":meta.get("name",m.parent.name),"description":meta.get("description",""),
                       "path":str(m.parent),"signature":_sig(text)})
    groups={}
    for s in skills: groups.setdefault(s["signature"],[]).append(s["name"])
    return {"count":len(skills),"skills":skills,
            "exact_content_duplicate_groups":[x for x in groups.values() if len(x)>1]}

def build_skill_hypergraph(catalog):
    return {"levels":{"L0":"instruction/guard/eval atoms","L1":"skills","L2":"families",
                      "L3":"routers/compositions","L4":"domain generators","L5":"generator-of-generators"},
            "nodes":[{"id":s["name"],"type":"skill","path":s["path"],"signature":s["signature"]} for s in catalog.get("skills",[])],
            "hyperedges":[{"type":"duplicate_content","members":g} for g in catalog.get("exact_content_duplicate_groups",[])]}
