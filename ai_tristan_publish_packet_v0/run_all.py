from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from datetime import datetime, timezone
from itertools import combinations
from math import prod
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
REG = ROOT / "registries"

@dataclass(frozen=True)
class Score:
    fertility: float
    verifiability: float
    reusability: float
    impact: float
    compression: float
    stability: float
    complexity: float
    noise: float
    untested_speculation: float
    risk: float

    def clamp(self):
        def c(x): return max(0.01, min(1.0, float(x)))
        return Score(**{k: c(v) for k, v in asdict(self).items()})

@dataclass(frozen=True)
class Candidate:
    id: str
    name: str
    lane: str
    status: str
    score: Score
    tags: tuple[str, ...]
    dct_ready: bool = True
    stable_canon_allowed: bool = False

    def jsonable(self):
        d = asdict(self)
        d["power"] = power_score(self.score)
        return d

def power_score(score: Score) -> float:
    s = score.clamp()
    num = prod([s.fertility, s.verifiability, s.reusability, s.impact, s.compression, s.stability])
    den = prod([s.complexity, s.noise, s.untested_speculation, s.risk])
    raw = num / max(1e-9, den)
    return round(raw / (1.0 + raw), 6)

def classify(score: Score, dct_ready: bool, physical_validation: bool = False) -> str:
    p = power_score(score)
    s = score.clamp()
    if physical_validation and dct_ready and p >= 0.88 and s.untested_speculation <= 0.18 and s.risk <= 0.35:
        return "stable-canon-candidate"
    if dct_ready and p >= 0.72 and s.verifiability >= 0.55:
        return "crystallizable"
    if p >= 0.45:
        return "exploratory-structured"
    return "sandbox"

def shift(score: Score, **delta):
    data = asdict(score)
    for k, v in delta.items():
        data[k] += v
    return Score(**data).clamp()

def seed():
    return [Candidate(
        id="AI-TRISTAN-V0-SEED",
        name="AI-TRISTAN^n governed publish seed",
        lane="Lane-RUNTIME",
        status="crystallizable",
        score=Score(0.92, 0.70, 0.88, 0.86, 0.82, 0.66, 0.62, 0.28, 0.45, 0.40),
        tags=("ai-tristan", "yggdrasil", "hgfm", "top64", "dct"),
    )]

def generators64():
    families = [
        ("geo", {"compression": 0.03, "reusability": 0.02, "complexity": 0.01}),
        ("hgfm", {"fertility": 0.04, "noise": -0.01, "complexity": 0.02}),
        ("dct", {"verifiability": 0.06, "stability": 0.03, "untested_speculation": -0.06}),
        ("verify", {"verifiability": 0.05, "risk": -0.03, "stability": 0.03}),
        ("score", {"compression": 0.02, "noise": -0.04, "reusability": 0.02}),
        ("proto", {"impact": 0.03, "verifiability": 0.04, "risk": -0.02}),
        ("publish", {"impact": 0.04, "compression": 0.03, "noise": -0.03}),
        ("safety", {"risk": -0.05, "stability": 0.05, "untested_speculation": -0.04}),
    ]
    out = []
    for fi, (fam, delta) in enumerate(families):
        for j in range(8):
            gid = f"G{fi*8+j+1:02d}-{fam}-{j+1}"
            def make(gid=gid, fam=fam, delta=delta):
                def gen(c: Candidate):
                    ns = shift(c.score, **delta)
                    return Candidate(
                        id=f"{c.id}__{gid}",
                        name=f"{c.name} + {fam}",
                        lane=c.lane,
                        status=classify(ns, c.dct_ready, False),
                        score=ns,
                        tags=tuple(dict.fromkeys(c.tags + (gid,))),
                        dct_ready=c.dct_ready,
                        stable_canon_allowed=False,
                    )
                return gen
            out.append(make())
    assert len(out) == 64
    return out

def beam(depth=2, width=16):
    items = seed()
    gens = generators64()
    for _ in range(depth):
        expanded = [g(c) for c in items for g in gens]
        expanded.sort(key=lambda c: power_score(c.score), reverse=True)
        items = expanded[:width]
    return items

def hypergraph(cands):
    nodes = [{"id": c.id, "label": c.name, "status": c.status, "power": power_score(c.score), "tags": list(c.tags)} for c in cands]
    edges = []
    for a, b in combinations(cands[:8], 2):
        edges.append({"source": a.id, "target": b.id, "type": "meta-hypersynergy-proxy"})
    return {"kind": "HGFMRuntimeGraph", "generated_at": datetime.now(timezone.utc).isoformat(), "nodes": nodes, "hyperedges": edges[:16]}

def write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def main():
    OUT.mkdir(exist_ok=True)
    REG.mkdir(exist_ok=True)
    best = beam(depth=2, width=16)
    ranked = [c.jsonable() for c in best]
    run = {
        "id": "AI-TRISTAN-PUBLISH-RUN-001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "succeeded",
        "decision": "PUBLISH_AS_CRYSTALLIZABLE_PACKET",
        "stable_canon_allowed": False,
        "anti_inflation_guard": "Do not label as stable canon. Publish as bounded DCT packet and PR.",
        "top_candidate_power": ranked[0]["power"],
        "ranked_candidates": ranked,
    }
    run["receipt_sha256"] = hashlib.sha256(json.dumps(run, sort_keys=True).encode()).hexdigest()
    write(OUT / "run_receipt.json", run)
    write(OUT / "top_candidates.json", ranked)
    write(OUT / "hgfm_runtime_graph.json", hypergraph(best))
    (REG / "publish_registry.jsonl").write_text("\n".join([
        json.dumps({"kind": "CommandRow", "status": "accepted", "action": "push_publish_run_all_best_revolutionnaire"}),
        json.dumps({"kind": "ScoreRow", "status": "scored", "top_candidate_power": ranked[0]["power"], "stable_canon_allowed": False}),
        json.dumps({"kind": "ReviewDecision", "status": "reviewed", "decision": "PUBLISH_AS_CRYSTALLIZABLE_PACKET"}),
        json.dumps({"kind": "RollbackPointer", "status": "ready", "recovery_steps": ["delete outputs/*", "delete registries/*", "rerun python run_all.py"]}),
    ]) + "\n", encoding="utf-8")
    print(json.dumps({"status": run["status"], "decision": run["decision"], "top_candidate_power": run["top_candidate_power"], "receipt_sha256": run["receipt_sha256"]}, indent=2))

if __name__ == "__main__":
    main()
