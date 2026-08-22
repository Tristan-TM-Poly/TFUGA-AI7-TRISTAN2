from __future__ import annotations

import argparse
import json
from pathlib import Path

from .arena import mutate_axiom, rank_candidates
from .core import AxiomGenome, ClaimPassport, EpistemicKind, EpistemicStatus, EvidenceItem, EvidenceType, Prediction, genome_to_dict, oak_audit, oak_to_dict
from .regen import DEFAULT_BOOK0, regeneration_receipt


def _load_genome(path: str) -> AxiomGenome:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    p = data["passport"]
    evidence = tuple(EvidenceItem(e["evidence_id"], EvidenceType(e["evidence_type"]), e["source"], tuple(e.get("supports_scope", [])), bool(e.get("independent", False)), float(e.get("strength", 0.5)), e.get("notes", "")) for e in p.get("evidence", []))
    counter = tuple(EvidenceItem(e["evidence_id"], EvidenceType(e["evidence_type"]), e["source"], tuple(e.get("supports_scope", [])), bool(e.get("independent", False)), float(e.get("strength", 0.5)), e.get("notes", "")) for e in p.get("counterevidence", []))
    passport = ClaimPassport(
        claim_id=p["claim_id"], statement=p["statement"], kind=EpistemicKind(p["kind"]), domain=p["domain"],
        definitions=tuple(p.get("definitions", [])), scope=tuple(p.get("scope", [])), assumptions=tuple(p.get("assumptions", [])),
        dependencies=tuple(p.get("dependencies", [])), evidence=evidence, counterevidence=counter,
        uncertainty=dict(p.get("uncertainty", {})), falsifiers=tuple(p.get("falsifiers", [])), proof_obligations=tuple(p.get("proof_obligations", [])),
        provenance=tuple(p.get("provenance", [])), version=p.get("version", "0.1.0"), status=EpistemicStatus(p.get("status", "IDEA")),
        generator_id=p.get("generator_id", ""), judge_id=p.get("judge_id", ""), revenue_score=p.get("revenue_score"),
    )
    predictions = tuple(Prediction(x["prediction_id"], x["variable"], x["expected"], x.get("condition", "default"), x.get("falsifier", "")) for x in data.get("predictions", []))
    return AxiomGenome(passport=passport, consequences=tuple(data.get("consequences", [])), predictions=predictions, tests=tuple(data.get("tests", [])), boundary_conditions=tuple(data.get("boundary_conditions", [])), parent_ids=tuple(data.get("parent_ids", [])), mutation_label=data.get("mutation_label", "SEED"), generated_candidate=bool(data.get("generated_candidate", False)))


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m omega_axiome_tristan_t")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_audit = sub.add_parser("audit"); p_audit.add_argument("genome")
    p_mut = sub.add_parser("mutate"); p_mut.add_argument("genome")
    p_regen = sub.add_parser("regen"); p_regen.add_argument("genome")
    sub.add_parser("book0")
    args = parser.parse_args()

    if args.cmd == "book0":
        print(json.dumps({"manifest": DEFAULT_BOOK0.__dict__, "digest": DEFAULT_BOOK0.digest()}, ensure_ascii=False, indent=2))
        return
    genome = _load_genome(args.genome)
    if args.cmd == "audit":
        print(json.dumps(oak_to_dict(oak_audit(genome.passport)), ensure_ascii=False, indent=2))
    elif args.cmd == "mutate":
        muts = mutate_axiom(genome)
        print(json.dumps({"mutations": [genome_to_dict(m) for m in muts], "ranking": rank_candidates(muts), "authoritative": False}, ensure_ascii=False, indent=2))
    elif args.cmd == "regen":
        print(json.dumps(regeneration_receipt(genome).__dict__, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
