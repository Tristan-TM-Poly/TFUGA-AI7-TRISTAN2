"""JKD-YY3-Tristan² prototype engine.

A dependency-free engine that composes:
- JKD: minimum verified movement for maximum fertile impact.
- YY3: knowledge -> meta-knowledge -> generators.
- Tristan²: the Tristan loop applied to itself under OAK.

It generates candidates, scores them with Score_JYT2, keeps top16, stores
bottom16 as negative memory, and decompresses the best into a one-page codex.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Sequence


GENERATORS: Sequence[str] = (
    "Canon Compiler Generator",
    "OAK Attack Generator",
    "HGFM Mapper Generator",
    "FTPCI Optimizer Generator",
    "Codex Decompressor Generator",
    "Prototype Forge Generator",
    "Residual Physics Generator",
    "Plasma Benchmark Generator",
    "AIT Pantheon Generator",
    "Negative Memory Generator",
    "Theory Gap Generator",
    "GitHub Artifact Generator",
    "Metric Calibrator Generator",
    "AntiHype Generator",
    "Strategy Optimizer Generator",
    "Next Generator Generator",
)


@dataclass(frozen=True)
class JYT2Candidate:
    id: str
    generator: str
    cycle: int
    fertility: float
    oak: float
    generator_value: float
    reuse: float
    prototype_value: float
    movement: float
    compute: float
    risk: float
    hype: float
    debt: float
    score: float
    status: str
    jkd_reason: str
    next_action: str


def _hash_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _unit(seed: str, field: str) -> float:
    return (_hash_int(f"{seed}|{field}") % 1000) / 999


def build_candidate(generator: str, cycle: int, salt: str = "") -> JYT2Candidate:
    seed = f"{salt}|{cycle}|{generator}"
    fertility = 10 * (0.45 * _unit(seed, "fertility") + 0.30 * _unit(seed, "descendants") + 0.25 * _unit(seed, "bridges"))
    oak = min(1.0, 0.40 * _unit(seed, "trace") + 0.35 * _unit(seed, "attack") + 0.25 * _unit(seed, "limits"))
    generator_value = 10 * (0.50 * _unit(seed, "generator_value") + 0.30 * _unit(seed, "self_improve") + 0.20 * _unit(seed, "meta"))
    reuse = 10 * (0.45 * _unit(seed, "reuse") + 0.30 * _unit(seed, "compression") + 0.25 * _unit(seed, "transmission"))
    prototype_value = 10 * (0.45 * _unit(seed, "prototype") + 0.30 * _unit(seed, "test") + 0.25 * _unit(seed, "measurement"))

    movement = 1 + 8 * _unit(seed, "movement")
    compute = 1 + 8 * _unit(seed, "compute")
    risk = 1 + 8 * _unit(seed, "risk")
    hype = 1 + 8 * _unit(seed, "hype")
    debt = 1 + 8 * _unit(seed, "debt")

    if "OAK" in generator or "AntiHype" in generator:
        oak = min(1.0, oak + 0.12)
        hype = max(1.0, hype - 1.0)
    if "Prototype" in generator or "Benchmark" in generator:
        prototype_value = min(10.0, prototype_value + 1.0)
    if "Next Generator" in generator:
        generator_value = min(10.0, generator_value + 1.2)
        hype = min(9.0, hype + 0.5)
    if "Negative Memory" in generator:
        risk = max(1.0, risk - 0.8)
        debt = max(1.0, debt - 0.6)

    score = (fertility * oak * generator_value * reuse * prototype_value) / (movement + compute + risk + hype + debt + 1)
    status = "selected" if score >= 75 and oak >= 0.65 else "quarantine"
    if movement <= 3.5 and compute <= 4.0:
        jkd_reason = "low movement and compute; strong JKD fit"
    elif score >= 75:
        jkd_reason = "high score; acceptable movement under OAK"
    else:
        jkd_reason = "not JKD-minimal enough; keep compressed"
    next_action = "decompress to codex and test plan" if status == "selected" else "attack, simplify, or bury in negative memory"
    candidate_id = f"jyt2-{cycle:02d}-{_hash_int(seed) % 10000:04d}"
    return JYT2Candidate(
        id=candidate_id,
        generator=generator,
        cycle=cycle,
        fertility=round(fertility, 3),
        oak=round(oak, 3),
        generator_value=round(generator_value, 3),
        reuse=round(reuse, 3),
        prototype_value=round(prototype_value, 3),
        movement=round(movement, 3),
        compute=round(compute, 3),
        risk=round(risk, 3),
        hype=round(hype, 3),
        debt=round(debt, 3),
        score=round(score, 3),
        status=status,
        jkd_reason=jkd_reason,
        next_action=next_action,
    )


def run_jyt2(cycles: int = 1, salt: str = "") -> Dict[str, object]:
    all_bottom: List[JYT2Candidate] = []
    top16: List[JYT2Candidate] = []
    history = []
    for cycle in range(cycles):
        candidates = [build_candidate(generator, cycle, salt=salt) for generator in GENERATORS]
        ranked = sorted(candidates, key=lambda item: item.score, reverse=True)
        top16 = ranked[:16]
        bottom16 = ranked[-16:]
        all_bottom.extend(bottom16)
        history.append(
            {
                "cycle": cycle,
                "top1": asdict(top16[0]),
                "bottom1": asdict(bottom16[0]),
            }
        )
    top1 = top16[0]
    return {
        "engine": "JKD-YY3-Tristan2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cycles": cycles,
        "salt": salt,
        "top16": [asdict(candidate) for candidate in top16],
        "bottom16": [asdict(candidate) for candidate in sorted(all_bottom, key=lambda item: item.score)[:16]],
        "top1_jkd": asdict(top1),
        "codex_1p": one_page_codex(top1),
        "history": history,
        "oak_note": "Prototype generator ranking only; not a proof or external action.",
    }


def one_page_codex(candidate: JYT2Candidate) -> str:
    return "\n".join(
        [
            f"# JKD-YY3-Tristan² Codex — {candidate.id}",
            "",
            f"**Generator:** {candidate.generator}",
            f"**Score JYT2:** {candidate.score}",
            f"**OAK:** {candidate.oak}",
            f"**Status:** {candidate.status}",
            "",
            "## Racine",
            "Minimiser mouvement/calcul tout en maximisant génération vérifiable.",
            "",
            "## Tronc",
            "JKD sélectionne le Top1 minimal; YY3 élève connaissance -> méta-connaissance -> générateur; Tristan² réinjecte la boucle dans elle-même.",
            "",
            "## Branches",
            f"- Fertility: {candidate.fertility}",
            f"- Generator value: {candidate.generator_value}",
            f"- Prototype value: {candidate.prototype_value}",
            f"- JKD reason: {candidate.jkd_reason}",
            "",
            "## OAK",
            "Rester prototype tant qu'il n'existe pas de test, mesure, usage ou validation locale.",
            "",
            "## Prochaine action",
            candidate.next_action,
            "",
        ]
    )


def write_outputs(result: Dict[str, object], reports_dir: Path, examples_dir: Path) -> None:
    reports_dir.mkdir(exist_ok=True)
    examples_dir.mkdir(exist_ok=True)
    (reports_dir / "jkd_yy3_tristan2_latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (reports_dir / "jkd_yy3_tristan2_top1_codex.md").write_text(str(result["codex_1p"]), encoding="utf-8")
    summary = {
        "engine": result["engine"],
        "generated_at_utc": result["generated_at_utc"],
        "top1_jkd": result["top1_jkd"],
        "oak_note": result["oak_note"],
    }
    (examples_dir / "jkd_yy3_tristan2_latest.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JKD-YY3-Tristan2 prototype cycle.")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--salt", default="manual")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = run_jyt2(cycles=args.cycles, salt=args.salt)
    if args.write:
        write_outputs(result, Path("reports"), Path("examples"))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
