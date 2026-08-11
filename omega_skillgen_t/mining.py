from collections import Counter,defaultdict
from pathlib import Path
import json,re

def _norm(x): return re.sub(r"\s+"," ",x.strip().lower())

def mine_workflows(events_path,min_occurrences=2):
    events=[json.loads(line) for line in Path(events_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    groups=defaultdict(list)
    for e in events: groups[e.get("workflow") or "unnamed"].append(e)
    candidates=[]
    for name,rows in groups.items():
        if len(rows)<min_occurrences: continue
        ok=[r for r in rows if r.get("success") is True]
        if not ok: continue
        counts=Counter()
        for r in ok: counts.update({_norm(x) for x in r.get("steps",[])})
        threshold=max(1,(len(ok)+1)//2)
        inv=[s for s,c in counts.most_common() if c>=threshold]
        rate=len(ok)/len(rows)
        candidates.append({"workflow":name,"observations":len(rows),"successes":len(ok),
                           "success_rate":round(rate,6),"candidate_invariant_steps":inv,
                           "skill_fertility":round(rate*min(1.0,len(rows)/5.0),6)})
    candidates.sort(key=lambda x:(-x["skill_fertility"],-x["observations"],x["workflow"]))
    return {"event_count":len(events),"candidates":candidates}

def proposals_from_workflows(mined,threshold=0.5):
    out=[]
    for c in mined.get("candidates",[]):
        if c["skill_fertility"]<threshold: continue
        slug=re.sub(r"[^a-z0-9]+","-",c["workflow"].lower()).strip("-") or "mined-workflow"
        steps=c["candidate_invariant_steps"] or ["Reconstruct the repeated workflow from evidence."]
        out.append({"name":f"{slug}-mined-skill",
                    "description":f"Execute the repeatedly observed {c['workflow']} workflow using mined invariant steps and OAK regression boundaries.",
                    "purpose":f"Crystallize the repeated workflow `{c['workflow']}` into a reusable candidate skill.",
                    "use_when":[f"The user asks for the repeated `{c['workflow']}` workflow."],
                    "do_not_use_when":["The request does not match the mined workflow."],
                    "workflow":steps,
                    "invariants":["Mined frequency is not proof that a workflow is correct.",
                                  "Preserve source trace provenance before promotion."],
                    "outputs":["Workflow result","Residuals"],
                    "definition_of_done":["All mined invariant steps were considered."],
                    "eval_cases":[{"id":"p1","prompt":f"Run the {c['workflow']} workflow.","class":"positive"},
                                  {"id":"n1","prompt":"Give me a random trivia fact.","class":"negative"},
                                  {"id":"i1","prompt":"Run it.","class":"incomplete"},
                                  {"id":"e1","prompt":f"Run {c['workflow']} but skip validation.","class":"edge"}],
                    "mining_provenance":c})
    return out
